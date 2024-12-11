from datetime import datetime
import time
import logging
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
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            raise
    
    @staticmethod
    def parse_show_date(date_str: str) -> datetime:
        """解析日期字符串，只保留日期部分"""
        try:
            # 分割字符串，只取日期部分
            date_part = date_str.split(' ')[0]
            return datetime.strptime(date_part, '%Y.%m.%d')
        except Exception as e:
            logger.error(f"解析日期失败: {str(e)}, 日期字符串: {date_str}")
            raise
    
    @staticmethod
    def is_duplicate(db: Session, show_data: dict, max_retries=3) -> bool:
        """检查是否存在重复数据，带重试机制"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 使用新的解析方法
                show_date = UploadService.parse_show_date(show_data['date'])
                return db.query(Show).filter(
                    and_(
                        Show.name == show_data['name'],
                        Show.date == show_date.date(),
                        Show.city == show_data['city']
                    )
                ).first() is not None
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
        """
        上传演出数据到数据库，跳过重复数据，带重试机制
        
        Args:
            db (Session): 数据库会话
            shows (list): 演出数据列表
            artist (str): 艺人名称
            max_retries (int, optional): 最大重试次数. Defaults to 3.
        """
        new_count = 0
        skip_count = 0
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 转换并插入新数据
                for show_data in shows:
                    try:
                        # 检查是否重复
                        if UploadService.is_duplicate(db, show_data):
                            skip_count += 1
                            logger.info(f"跳过重复数据: {show_data['name']} - {show_data['date']} - {show_data['city']}")
                            continue
                        
                        # 插入新数据
                        show = Show(
                            name=show_data['name'],
                            artist=artist,  # 使用传入的 artist 参数
                            tag=show_data['tag'],
                            city=show_data['city'],
                            venue=show_data['venue'],
                            lineup=show_data['lineup'],
                            date=UploadService.parse_show_date(show_data['date']).date(),
                            price=show_data['price'],
                            status=show_data['status'],
                            detail_url=show_data['detail_url'],
                            poster=show_data['poster']
                        )
                        db.add(show)
                        new_count += 1
                        
                    except Exception as e:
                        logger.error(f"处理数据时出错: {str(e)}")
                        continue
                
                # 提交事务
                db.commit()
                logger.info(f"\n数据上传完成:")
                logger.info(f"新增数据: {new_count} 条")
                logger.info(f"跳过重复: {skip_count} 条")
                return True
                
            except Exception as e:
                logger.error(f"上传数据时发生错误: {str(e)}")
                db.rollback()
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)
                    continue
                raise 