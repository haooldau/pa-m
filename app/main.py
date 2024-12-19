from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from .crawler.spider import DamaiCrawler
from .data_processor import ShowDataProcessor
from .services.upload_service import UploadService
from .config.database import SessionLocal
import logging

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=False,  # 关闭 credentials 模式
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 headers
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 请求模型
class CrawlerRequest(BaseModel):
    artists: List[str]

async def update_artist_shows(artist: str):
    try:
        logger.info(f"开始更新艺人 {artist} 的演出信息")
        
        # 创建爬虫和数据处理器实例
        crawler = DamaiCrawler()
        processor = ShowDataProcessor()
        
        # 获取演出数据
        shows = crawler.analyze_search_page(artist)
        if not shows:
            logger.warning(f"未找到艺人 {artist} 的演出信息")
            return False
            
        logger.info(f"找到 {len(shows)} 条原始演出信息")
        
        # 处理演出数据
        processed_shows = processor.process_date_range(shows)
        logger.info(f"处理后得到 {len(processed_shows)} 条演出信息")
        
        # 上传到数据库
        db = SessionLocal()
        try:
            success = UploadService.upload_shows(
                db=db,
                shows=processed_shows,
                artist=artist
            )
            
            if success:
                logger.info(f"艺人 {artist} 的数据更新成功")
                return True
            else:
                logger.error(f"艺人 {artist} 的数据更新失败")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"艺人 {artist} 数据更新失败: {str(e)}")
        raise

@app.post("/crawler/update")
async def update_shows(request: Request):
    try:
        data = await request.json()
        artists = data.get('artists', [])
        results = []
        
        for artist in artists:
            try:
                success = await update_artist_shows(artist)
                results.append({
                    "artist": artist,
                    "success": success,
                    "message": "更新成功" if success else "更新失败"
                })
            except Exception as e:
                results.append({
                    "artist": artist,
                    "success": False,
                    "message": str(e)
                })
        
        return {
            "success": True,
            "data": results
        }
        
    except Exception as e:
        logger.error(f"新请求处理失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"} 