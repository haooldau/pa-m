from sqlalchemy import create_engine
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
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:password@localhost:3306/damai')

# 创建数据库引擎，添加连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 超过pool_size后最多可以创建的连接数
    pool_timeout=30,  # 连接池中没有可用连接的等待时间
    pool_recycle=1800,  # 连接在连接池中重复使用的时间间隔（秒）
    pool_pre_ping=True,  # 每次连接前ping一下数据库，确保连接有效
    poolclass=QueuePool,  # 使用队列池
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基本映射类
Base = declarative_base()

def get_db_with_retry(max_retries=3, retry_delay=1):
    """获取数据库会话，添加重试机制"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            db = SessionLocal()
            # 测试连接是否有效
            db.execute("SELECT 1")
            return db
        except Exception as e:
            retry_count += 1
            logger.error(f"数据库连接失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                time.sleep(retry_delay)
                continue
            raise
        
# 获取数据库会话
def get_db():
    try:
        db = get_db_with_retry()
        yield db
    except Exception as e:
        logger.error(f"获取数据库连接失败: {str(e)}")
        raise
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {str(e)}") 