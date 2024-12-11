from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import time
import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# 数据库连接配置
DATABASE_URL = os.getenv('DATABASE_URL')
logger.info(f"使用数据库连接URL: {DATABASE_URL}")

# 创建数据库引擎，添加连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    poolclass=QueuePool,
    echo=True  # 启用SQL语句日志
)

# 添加数据库事件监听器
@event.listens_for(engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
    logger.info("数据库连接已建立")

@event.listens_for(engine, 'checkout')
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.info("数据库连接已从连接池中取出")

@event.listens_for(engine, 'checkin')
def receive_checkin(dbapi_connection, connection_record):
    logger.info("数据库连接已归还到连接池")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基本映射类
Base = declarative_base()

def get_db_with_retry(max_retries=3, retry_delay=1):
    """获取数据库会话，添加重试机制"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info("尝试获取数据库会话...")
            db = SessionLocal()
            # 测试连接是否有效
            logger.info("测试数据库连接...")
            db.execute("SELECT 1")
            logger.info("数据库连接测试成功")
            return db
        except Exception as e:
            retry_count += 1
            logger.error(f"数据库连接失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                continue
            raise
        
def get_db():
    """获取数据库会话"""
    try:
        logger.info("开始获取数据库会话...")
        db = get_db_with_retry()
        logger.info("成功获取数据库会话")
        yield db
    except Exception as e:
        logger.error(f"获取数据库连接失败: {str(e)}")
        raise
    finally:
        try:
            logger.info("关闭数据库会话...")
            db.close()
            logger.info("数据库会话已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}") 