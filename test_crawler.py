from app.crawler.spider import DamaiCrawler
from app.data_processor import ShowDataProcessor
from app.services.upload_service import UploadService
from app.config.database import SessionLocal
import json

def main():
    # 1. 爬取数据
    crawler = DamaiCrawler()
    print("开始爬取陈楚生的演出信息...")
    shows = crawler.analyze_search_page("陈楚生")
    
    if shows:
        # 2. 处理数据
        processor = ShowDataProcessor()
        processed_shows = processor.process_date_range(shows)
        
        print(f"\n处理后共有 {len(processed_shows)} 场演出")
        
        # 3. 上传到数据库
        print("\n开始上传数据到数据库...")
        upload_service = UploadService()
        upload_service.init_db()  # 初始化数据库表
        
        db = SessionLocal()
        try:
            if upload_service.upload_shows(db, processed_shows):
                print("数据上传成功！")
            else:
                print("数据上传失败！")
        finally:
            db.close()
            
        # 4. 打印处理后的数据
        print("\n完整的演出信息JSON:")
        print(json.dumps(processed_shows, ensure_ascii=False, indent=2))
    else:
        print("\n爬取失败或未找到演出信息")

if __name__ == "__main__":
    main() 