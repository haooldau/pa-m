from datetime import datetime, timedelta

class ShowDataProcessor:
    @staticmethod
    def process_date_range(shows):
        """处理演出数据，将跨天演出拆分成多条记录"""
        processed_shows = []
        
        for show in shows:
            date_str = show['date']
            
            # 检查是否包含日期范围（例如：2024.12.21-12.22）
            if '-' in date_str:
                try:
                    # 分割日期范围
                    date_parts = date_str.split('-')
                    start_date_str = date_parts[0].strip()  # 例如: 2024.12.21
                    end_date_str = date_parts[1].strip()    # 例如: 12.22
                    
                    # 从开始日期提取年份
                    year = start_date_str.split('.')[0]  # 2024
                    
                    # 处理开始日期
                    start_month = start_date_str.split('.')[1]  # 12
                    start_day = start_date_str.split('.')[2]    # 21
                    
                    # 处理结束日期
                    end_parts = end_date_str.split('.')  # [12, 22]
                    end_month = end_parts[0]
                    end_day = end_parts[1]
                    
                    # 构建完整的日期字符串
                    start_full = f"{year}.{start_month}.{start_day}"
                    end_full = f"{year}.{end_month}.{end_day}"
                    
                    # 转换为datetime对象
                    start_date = datetime.strptime(start_full, '%Y.%m.%d')
                    end_date = datetime.strptime(end_full, '%Y.%m.%d')
                    
                    # 生成日期范围内的每一天
                    current_date = start_date
                    while current_date <= end_date:
                        show_copy = show.copy()
                        show_copy['date'] = current_date.strftime('%Y.%m.%d')
                        processed_shows.append(show_copy)
                        current_date += timedelta(days=1)
                        
                except Exception as e:
                    print(f"处理日期范围时出错: {str(e)}")
                    processed_shows.append(show)
            else:
                # 如果不是日期范围，直接添加原始数据
                processed_shows.append(show)
        
        return processed_shows 