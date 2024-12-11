import os
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import urllib.parse
import platform

class DamaiCrawler:
    def __init__(self):
        self.status = "idle"
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        # 添加反爬虫检测
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置 user-agent
        self.chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.109 Safari/537.36')
        
        self.results = []
        self.base_url = "https://www.damai.cn/"
        self.search_base_url = "https://search.damai.cn/search.html"
        
    def get_driver(self):
        """获取配置好的 WebDriver，使用 Selenium Manager 自动管理"""
        try:
            # 直接使用 Chrome()，Selenium Manager 会自动处理驱动
            driver = webdriver.Chrome(options=self.chrome_options)
            return driver
        except Exception as e:
            print(f"创建 WebDriver 时出错: {str(e)}")
            raise
            
    def analyze_page_structure(self):
        """分析页面结构"""
        try:
            # 检测系统架构并选择合适的 ChromeDriver
            if platform.system() == 'Darwin' and platform.machine() == 'arm64':
                # Mac M1/M2
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            else:
                # 其他系统
                service = Service(ChromeDriverManager().install())
                
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            # 访问大麦网
            driver.get(self.base_url)
            time.sleep(3)
            
            # 打印页面标题
            print(f"页面标题: {driver.title}")
            
            # 分析主要区域
            print("\n分析页面主要区域:")
            main_sections = driver.find_elements(By.CSS_SELECTOR, "div[class*='section']")
            for section in main_sections:
                print(f"区域class: {section.get_attribute('class')}")
            
            # 分析导航菜单
            print("\n分析导航菜单:")
            nav_items = driver.find_elements(By.CSS_SELECTOR, "ul.dm-nav li")
            for item in nav_items:
                print(f"导航项: {item.text}")
            
            # 分析演出列表结构
            print("\n分析演出列表结构:")
            show_items = driver.find_elements(By.CSS_SELECTOR, "div[class*='show-item']")
            if show_items:
                sample_item = show_items[0]
                print("演出项目结构:")
                print(f"HTML结构: {sample_item.get_attribute('outerHTML')}")
            
            # 保存页面源码以供分析
            with open("damai_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            driver.quit()
            return True
            
        except Exception as e:
            print(f"分析页面结构时出错: {str(e)}")
            return False
    
    def start_crawling(self):
        """开始爬取数据"""
        # 这里先不实现爬取逻辑，等分析完页面结构后再实现
        pass

    def get_status(self):
        return {
            "status": self.status,
            "results_count": len(self.results)
        } 

    def get_artist_search_url(self, artist_name: str) -> str:
        """
        构建艺人搜索URL
        :param artist_name: 艺人名字
        :return: 搜索URL
        """
        encoded_name = urllib.parse.quote(artist_name)
        return f"{self.search_base_url}?keyword={encoded_name}&spm=a2oeg.search_category.searchtxt.dsearchbtn"
  
    def analyze_search_page(self, artist_name: str):
        try:
            search_url = self.get_artist_search_url(artist_name)
            print(f"\n开始分析搜索页面: {search_url}")
            
            driver = self.get_driver()
            driver.implicitly_wait(10)
            driver.get(search_url)
            time.sleep(10)
            
            # 查找所有演出项目的容器
            items = driver.find_elements(By.CSS_SELECTOR, "div.item__main div.items")
            print(f"\n找到 {len(items)} 个演出项目")
            
            shows_info = []
            for item in items:
                try:
                    show_info = {}
                    
                    # 1. 获取详情链接
                    title_link = item.find_element(By.CSS_SELECTOR, "a[href*='detail.damai.cn']")
                    show_info['detail_url'] = title_link.get_attribute('href')
                    
                    # 2. 获取海报图片
                    img = title_link.find_element(By.CSS_SELECTOR, "img")
                    show_info['poster'] = img.get_attribute('src') or img.get_attribute('data-src')
                    
                    # 3. 获取标签
                    tag = title_link.find_element(By.CSS_SELECTOR, "span.items__img__tag")
                    show_info['tag'] = tag.text.strip()
                    
                    # 4. 获取演出信息容器
                    info_container = item.find_element(By.CSS_SELECTOR, "div.items__txt")
                    
                    # 5. 获取标题和城市
                    title_container = info_container.find_element(By.CSS_SELECTOR, "div.items__txt__title")
                    city_span = title_container.find_element(By.CSS_SELECTOR, "span")
                    show_info['city'] = city_span.text.strip().replace("【","").replace("】","")
                    title_text = title_container.find_element(By.CSS_SELECTOR, "a")
                    show_info['name'] = title_text.text.strip()
                    
                    # 6. 获取演出阵容
                    try:
                        lineup = info_container.find_element(By.CSS_SELECTOR, "div.items__txt__time")
                        if "艺人：" in lineup.text:
                            show_info['lineup'] = lineup.text.replace("艺人：","").strip()
                        else:
                            show_info['lineup'] = ""
                    except:
                        show_info['lineup'] = ""
                    
                    # 7. 获取场馆
                    try:
                        venue_container = info_container.find_elements(By.CSS_SELECTOR, "div.items__txt__time")[1]
                        venue_text = venue_container.text.strip()
                        if "|" in venue_text:
                            city, venue = venue_text.split("|")
                            show_info['venue'] = venue.strip()
                        else:
                            show_info['venue'] = venue_text
                    except:
                        show_info['venue'] = ""
                    
                    # 8. 获取演出时间
                    try:
                        date_container = info_container.find_elements(By.CSS_SELECTOR, "div.items__txt__time")[2]
                        show_info['date'] = date_container.text.strip()
                    except:
                        show_info['date'] = ""
                    
                    # 9. 获取价格和售票状态
                    try:
                        price_container = info_container.find_element(By.CSS_SELECTOR, "div.items__txt__price")
                        price_text = price_container.find_element(By.CSS_SELECTOR, "span").text.strip()
                        show_info['price'] = price_text.replace("元","").strip()
                        
                        status_text = price_container.text.replace(price_text,"").replace("元","").strip()
                        show_info['status'] = status_text
                    except:
                        show_info['price'] = ""
                        show_info['status'] = ""
                    
                    shows_info.append(show_info)
                    
                    print("\n演出信息:")
                    print(f"名称: {show_info['name']}")
                    print(f"标签: {show_info['tag']}")
                    print(f"城市: {show_info['city']}")
                    print(f"场所: {show_info['venue']}")
                    print(f"阵容: {show_info['lineup']}")
                    print(f"日期: {show_info['date']}")
                    print(f"价格: {show_info['price']}")
                    print(f"状态: {show_info['status']}")
                    print(f"详情链接: {show_info['detail_url']}")
                    print(f"海报链接: {show_info['poster']}")
                    print("----------------------------------------")
                    
                except Exception as e:
                    print(f"提取演出信息时出错: {str(e)}")
                    continue
            
            # 保存结果到JSON文件
            if shows_info:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"damai_shows_{artist_name}_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(shows_info, f, ensure_ascii=False, indent=2)
                    print(f"\n结果已保存到: {filename}")
            
            driver.quit()
            return shows_info
            
        except Exception as e:
            print(f"分析搜索页面时出错: {str(e)}")
            return None
  