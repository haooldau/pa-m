from datetime import datetime
import time
import logging
import json
import os
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from ..models.show import Show
from ..config.database import engine, Base

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UploadService:
    @staticmethod
    def init_db():
        """初始化数据库表"""
        try:
            logger.info("开始初始化数据库表...")
            Base.metadata.create_all(bind=engine)
            logger.info("数据库表初始化成功")
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            raise
    
    @staticmethod
    def parse_show_date(date_str: str) -> datetime:
        """解析日期字符串，只保留日期部分"""
        try:
            logger.info(f"开始解析日期: {date_str}")
            # 分割字符串，只取日期部分
            date_part = date_str.split(' ')[0]
            result = datetime.strptime(date_part, '%Y.%m.%d')
            logger.info(f"日期解析结果: {result}")
            return result
        except Exception as e:
            logger.error(f"解析日期失败: {str(e)}, 日期字符串: {date_str}")
            raise
    
    @staticmethod
    def is_duplicate(db: Session, show_data: dict, max_retries=3) -> bool:
        """检查是否存在重复数据，带重试机制"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"检查重复数据: {show_data['name']} - {show_data['date']}")
                # 使用新的解析方法
                show_date = UploadService.parse_show_date(show_data['date'])
                result = db.query(Show).filter(
                    and_(
                        Show.name == show_data['name'],
                        Show.date == show_date.date(),
                        Show.city == show_data['city']
                    )
                ).first() is not None
                logger.info(f"重复检查结果: {'存在' if result else '不存在'}")
                return result
            except OperationalError as e:
                retry_count += 1
                logger.warning(f"检查重复数据失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
                if retry_count < max_retries:
                    time.sleep(1)
                    continue
                raise
            except Exception as e:
                logger.error(f"检查重复数据时发生错误: {str(e)}")
                raise
    
    @staticmethod
    def upload_shows(db: Session, shows: list, artist: str, max_retries: int = 3):
        """上传演出数据到数据库，跳过重复数据，带重试机制"""
        new_count = 0
        skip_count = 0
        retry_count = 0
        
        # 保存原始数据到JSON文件
        try:
            data_path = os.getenv('DATA_SAVE_PATH', './data')
            os.makedirs(data_path, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(data_path, f'damai_shows_{artist}_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(shows, f, ensure_ascii=False, indent=2)
            logger.info(f"原始数据已保存到: {json_file}")
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
        
        while retry_count < max_retries:
            try:
                logger.info(f"开始上传数据，艺人: {artist}, 数据量: {len(shows)}")
                # 转换并插入新数据
                for show_data in shows:
                    try:
                        logger.info(f"处理演出数据: {show_data['name']}")
                        # 检查是否重复
                        if UploadService.is_duplicate(db, show_data):
                            skip_count += 1
                            logger.info(f"跳过重复数据: {show_data['name']} - {show_data['date']} - {show_data['city']}")
                            continue
                        
                        # 解析日期
                        show_date = UploadService.parse_show_date(show_data['date']).date()
                        logger.info(f"创建Show对象: {show_data['name']} - {show_date}")
                        
                        # 插入新数据
                        show = Show(
                            name=show_data['name'],
                            artist=artist,
                            tag=show_data['tag'],
                            city=show_data['city'],
                            venue=show_data['venue'],
                            lineup=show_data['lineup'],
                            date=show_date,
                            price=show_data['price'],
                            status=show_data['status'],
                            detail_url=show_data['detail_url'],
                            poster=show_data['poster']
                        )
                        db.add(show)
                        new_count += 1
                        logger.info(f"数据已添加到会话: {show_data['name']}")
                        
                    except Exception as e:
                        logger.error(f"处理数据时出错: {str(e)}, 数据: {show_data}")
                        continue
                
                # 提交事务
                logger.info("开始提交事务...")
                db.commit()
                logger.info(f"数据上传完成: 新增 {new_count} 条, 跳过 {skip_count} 条")
                return True
                
            except Exception as e:
                logger.error(f"上传数据时发生错误: {str(e)}")
                db.rollback()
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"准备第 {retry_count + 1} 次重试...")
                    time.sleep(1)
                    continue
                raise 