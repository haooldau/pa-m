from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from services.upload_service import UploadService
from database.db import db
from utils.get_artist_shows import get_artist_shows
from utils.logger import logger

router = APIRouter()

@router.post("/update")
async def update_shows(request: Request):
    try:
        data = await request.json()
        artists = data.get('artists', [])
        results = []
        
        for artist in artists:
            try:
                # 获取演出数据
                shows = await get_artist_shows(artist)
                
                # 修改这里：正确传递 artist 参数
                success = UploadService.upload_shows(
                    db=db, 
                    shows=shows, 
                    artist=artist,  # 确保这个参数名与方法定义匹配
                    max_retries=3
                )
                
                results.append({
                    "artist": artist,
                    "success": True,
                    "message": "更新成功"
                })
            except Exception as e:
                logger.error(f"艺人 {artist} 数据更新失败: {str(e)}")
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
        logger.error(f"更新请求处理失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 