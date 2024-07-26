""" 基本套件 """
import requests as res
from bs4 import BeautifulSoup as bs
from time import sleep
from pprint import pprint
import pandas as pd
import logging as log
import json

# 處理正則表達式
import re 

# 執行 系統命令(commend)
import os

# 讓執行中可能會跑出的warnings閉嘴
# import warnings
# warnings.filterwarnings("ignore") 

from logging import getLogger
logger = getLogger('XY_house.log')

""" selenium套件 """
# 瀏覽器自動化
from selenium import webdriver as wd
from selenium.webdriver.chrome.service import Service

# (三人行) 在動態網頁中，等待指定元素出現的工具(要等多久?)
from selenium.webdriver.support.ui import WebDriverWait
# (三人行) 當指定元素出現，便符合等待條件 → 停止等待階段，並往下一段程式碼執行
from selenium.webdriver.support import expected_conditions as EC
# (三人行) 以...搜尋指定物件 (如: ID、Name、連結內容等...)
from selenium.webdriver.common.by import By 

# 處理逾時例外的工具 (網頁反應遲緩 or 網路不穩定)
from selenium.common.exceptions import TimeoutException

# 加入行為鍊 ActionChain (在 WebDriver 中模擬滑鼠移動、點擊、拖曳、按右鍵出現選單，以及鍵盤輸入文字、按下鍵盤上的按鈕等)
from selenium.webdriver.common.action_chains import ActionChains

# 加入鍵盤功能 (例如 Ctrl、Alt 等)
from selenium.webdriver.common.keys import Keys


""" 檢查目錄是否存在，如果不存在就建立目錄 """
def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
    
    logger.info(f'已建立資料夾路徑 {path}')

""" 設定log檔 """
def set_log():
    # 儲存路徑
    log_file_path = './XY_house_Taipei/XY_house_Taipei_urls.log'
    # log_file_path = './XY_house_NewTaipei/XY_house_NewTaipei_urls.log'

    # 基本設定
    logger = log.getLogger('XY_house.log')

    # 設定等級
    logger.setLevel(log.INFO)

    # 設定輸出格式
    formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

    # 儲存在 log 當中的事件處理器 (a: append, w: write)
    fileHandler = log.FileHandler(log_file_path, mode='a', encoding='utf-8')
    fileHandler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = log.StreamHandler()
    console_handler.setFormatter(formatter)

    # 加入事件
    logger.addHandler(console_handler)
    logger.addHandler(fileHandler)

    return logger

""" 設定driver """
def set_driver(url):
    # 啟動瀏覽器的工具選項
    XY_options = wd.ChromeOptions()
    # XY_options.add_argument("--headless")             # 不開啟實體瀏覽器視窗 (瑞德說這樣會出錯)
    XY_options.add_argument("--start-maximized")        # 最大化視窗
    XY_options.add_argument("--incognito")              # 開啟無痕分頁(如果要開實體瀏覽器，就不用無痕分頁)
    XY_options.add_argument("--disable-popup-blocking") # 禁止彈出連結，避免彈窗干擾自動化操作
    XY_options.add_argument("--disable-notifications")  # 取消 chrome 推波通知
    XY_options.add_argument("--lang=zh-TW")             # 設定為繁體中文
    XY_options.add_experimental_option('detach', True)  # 設定不自動關閉瀏覽器
    XY_options.add_argument("--no-sandbox")             # 添加此行可以在某些環境中提高穩定性
    XY_options.add_argument("--disable-dev-shm-usage")  # 提高性能
    
    # 修改 header，營造安全登入者的狀況
    # XY_options.add_argument('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    # 使用 Chrome 的 Webdriver (若沒有特別設定，只要電腦有安裝Chrome，就可以直接使用)
    driver = wd.Chrome(options = XY_options)
    
    # 開啟網頁
    driver.get(url)
    return driver


    # JS元素
    innerHeight = 0 # 瀏覽器內部的高度
    offset = 0      # 當前捲動的量(高度)
    count = 0       # 累計無效滾動次數
    limit = 3       # 最大無效滾動次數
    
    # 持續捲動，直到沒有元素動態產生
    while count <= limit:
        # 每次移動高度
        offset = driver.execute_script(
            'return document.documentElement.scrollHeight;'
        )

        '''
        或是每次只滾動一點距離，
        以免有些網站會在移動長距離後，
        將先前移動當中的元素隱藏

        EX: 將上方的 script 改成: offset += 600
        '''

        # 捲軸往下滑動
        driver.execute_script(f'''window.scrollTo({{top: {offset}, behavior: 'smooth' }});''')
        
        '''
        [補充]
        如果要滾動的是 div 裡面的捲軸，可以使用以下的方法
        document.querySelector('div').scrollTo({...})
        '''
        
        # (重要)強制等待，此時若有新元素生成，瀏覽器內部高度會自動增加
        sleep(3)
        
        # 透過執行 js 語法來取得捲動後的當前總高度
        innerHeight = driver.execute_script(
            'return document.documentElement.scrollHeight;'
        )
        
        # 經過計算，如果滾動距離(offset)大於、等於視窗內部總高度(innerHeight)，代表已經到底了
        if offset == innerHeight:
            count += 1
            
        # 為了實驗功能，捲動超過一定的距離，就結束程式
        if offset >= 600:
            break

        # print (innerHeight)

""" 抓取信義房屋每筆選項的URL """
def house_list(driver, all_house_urls, total_pages=305):
    try:
        # 瀏覽每一頁
        for page in range(1, total_pages+1):
            # 動態生成每一頁的URL
            # current_url = f'https://www.sinyi.com.tw/buy/list/Taipei-city/default-desc/{page}'
            current_url = f'https://www.sinyi.com.tw/buy/list/NewTaipei-city/default-desc/{page}'
            # 導航到當前頁面
            driver.get(current_url)
            # 等待頁面開始加載
            sleep(5)  
            
            try:
                # 等待直到頁面上所有的房屋列表項目被加載
                WebDriverWait(driver,10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "buy-list-item"))
                )
            except TimeoutException:
                print(f"第{page}頁無房屋列表，可能已超過實際頁數，爬蟲結束")
                break

            # 強制等待，確保頁面元素完全加載
            sleep(5)

            # 解析當前頁面的HTML
            soup = bs(driver.page_source, 'html.parser')

            # 查找所有的房屋元素
            house_list = soup.find_all('div', class_='buy-list-item')

            # 如果沒有房屋列表，提前結束
            if not house_list:
                print(f"第{page}頁沒有房屋資訊，可能已到最後一頁")
                break

            for hlist in house_list:
                # 提取每個房子的ID
                house_id = hlist.get('id')
                # 在房屋選項中找到<a>標籤
                a_tag = hlist.find('a', href=True)
                # 提取<a>標籤的href屬性，若無<a>標籤則返回'No link available'
                href = a_tag['href'] if a_tag else 'No link available'
                # 紀錄房屋ID，鏈接，和頁碼
                all_house_urls.append(href)

                # 將所有房屋網址資料轉存成 JSON
                json_file_path = './XY_house_Taipei/XY_house_Taipei_urls.json'
                # json_file_path = './XY_house_NewTaipei/XY_house_NewTaipei_urls.json'

                # 儲存當前進度
                with open(json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(all_house_urls, file, ensure_ascii=False, indent=4)

            logger.info(f'已爬完第{page}頁')

            # 休息後再進行下一頁的加載，減緩請求速率
            sleep(5)

    except Exception as e:
        logger.error(f"爬取過程中發生錯誤: {e}")

    # 確保無論如何(成功、錯誤、被中斷)都能關閉程式碼
    finally:
        print('爬蟲結束')
        driver.quit()

    return all_house_urls

""" 函式 """
if __name__ == '__main__':
    # 檢查路徑、資料夾，若不存在就建立
    log_json_path = './XY_house_Taipei'
    # log_json_path = './XY_house_NewTaipei'
    ensure_directory_exists(log_json_path)

    # 開啟瀏覽器
    # url = 'https://www.sinyi.com.tw/buy/list/Taipei-city/default-desc'
    url = 'https://www.sinyi.com.tw/buy/list/NewTaipei-city/default-desc'
    driver = set_driver(url)

    # 設定log
    logger = set_log()
    logger.info('開始爬取信義房屋的網址')

    # 初始化一個集合來儲存所有房屋的資訊
    all_house_urls = []

    urls_list = house_list(driver, all_house_urls)

    driver.quit()