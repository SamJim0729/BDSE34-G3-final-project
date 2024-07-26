""" 基本套件 """
import requests as req
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
import warnings
warnings.filterwarnings("ignore") 

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

# 加入行為鏈 ActionChain (在 WebDriver 中模擬滑鼠移動、點擊、拖曳、按右鍵出現選單，以及鍵盤輸入文字、按下鍵盤上的按鈕等)
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
    log_file_path = './XY_house_Taipei/XY_house_Taipei_informationtest.log'
    # log_file_path = './XY_house_NewTaipei/XY_house_NewTaipei_informationtest.log'
    
    # 基本設定
    logger = log.getLogger('XY_house.log')

    # 設定等級
    logger.setLevel(log.INFO)

    # 設定輸出格式
    formatter = log.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

    # 儲存在 log 當中的事件處理器 (# a: append, w: write)
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
def set_driver():
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
    # XY_options.add_argument("--disable-dev-shm-usage")  # 提高性能
    XY_options.add_argument('--disable-gpu')            # 禁用GPU加速

    # 使用 Chrome 的 Webdriver (若沒有特別設定，只要電腦有安裝Chrome，就可以直接使用)
    driver = wd.Chrome(options = XY_options)
    
    return driver

""" 滾動頁面 """
def scroll():
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
        
        # 透過執行 js語法 來取得捲動後的當前總高度
        innerHeight = driver.execute_script(
            'return document.documentElement.scrollHeight;'
        )
        
        # 經過計算，如果滾動距離(offset)大於、等於視窗內部總高度(innerHeight)，代表已經到底了
        if offset == innerHeight:
            count += 1
            
        # 為了實驗功能，捲動超過一定的距離，就結束程式
        # if offset >= 600:
        #     break

        # print (innerHeight)

""" 從先前爬取的檔案中，讀取裡面的網址 """
def get_house_list(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    house_list = json.loads(data)
    return house_list

""" 從網址內讀取資料 """
def XY_url_information(partial_url, all_house_data, index):
    url = f"https://www.sinyi.com.tw{partial_url}"

    # 記錄目前要爬取第X筆資料
    logger.info(f'開始處理第 {index+1} 筆資料，URL: {url}')

    try:
        driver.get(url)
        sleep(4)  # 等待頁面完全加載

        # 獲取頁面的 HTML 源碼
        html_source = driver.page_source
        soup = bs(html_source, 'html.parser')

        data = {}

        # 區塊一
        try:
            # 房名
            title_spans = soup.select('div.buy-content-title-left-area span')
            if title_spans:
                data['名稱'] = title_spans[0].text.strip()
                logger.info(f"名稱: {data['名稱']}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到房名")

            # 地址
            address_spans = soup.select('div.buy-content-title-left-area span')
            if address_spans:
                full_address_text = address_spans[2].text.strip()
                # 分割爬下來的資料，移除前面的「地址」(只分割一次)
                address_parts = full_address_text.split('地址', 1)
                # 分割後會有兩個list，取 address_partsp[1] 作為主要資料
                if len(address_parts) > 1:
                    data['地址'] = address_parts[1].strip()
                # 若爬下來的 原始資料full_address_text 沒有「地址」，則使用原始資料
                else:
                    data['地址'] = full_address_text
                logger.info(f"地址: {data['地址']}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到地址")

            # 總價
            price_div = soup.select('div.buy-content-title-total-price')
            if price_div:
                # 將抓取價格的數字部分內的逗號刪除
                raw_price = price_div[0].text.strip().replace(',', '')
                # 用正則表達式分別抓取 數字 和 單位
                price = re.search(r'(\d+)(\D+)', raw_price)
                if price:
                    # 提取 數字 和 單位
                    data['總價'] = price.group(1) + price.group(2)  # 若是 group(0)，則會抓到整個 3198萬
                else:
                    data['總價'] = '總價格式不符'  # 顯示異常情況
                logger.info(f"總價: {data['總價']}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到總價")

        except Exception as e:
            logger.error(f"url:{url} 第{index+1}筆資料的區塊一出現錯誤: {e}")
            return None
        
        sleep(2)

        # 區塊二
        try:
            # 坪數
            area_spans = soup.select('div.buy-content-detail-area span')
            if area_spans:
                for i in range(0, len(area_spans), 2):
                    # 刪除key中的 「/ 」，並無須用其餘字元取代 
                    key = area_spans[i].text.strip().replace('/ ', '')  
                    value = area_spans[i+1].text.strip()
                    data[key] = value
                    logger.info(f"{key}: {value}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到坪數資料")

            # 格局
            layout_div = soup.select('div.buy-content-detail-layout')
            if layout_div:
                for i in range(len(layout_div)):
                    value = layout_div[0].text.strip()
                    data['格局'] = value
                    logger.info(f"格局: {value}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到格局資料")

            # 年份、販售類型
            type_spans = soup.select('div.buy-content-detail-type span')
            if type_spans:
                keys = ['年份', '販售類型']
                for i in range(len(type_spans)):
                    key = keys[i]
                    value = type_spans[i].text.strip()
                    data[key] = value
                    logger.info(f"{key}: {value}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到年份、販售類型資料")

            # 樓層
            floor_div = soup.select('div.buy-content-detail-floor')
            if floor_div:
                for i in range(len(layout_div)):
                    value = floor_div[0].text.strip()
                    data['樓層'] = value
                    logger.info(f"樓層: {value}")
            else:
                logger.error(f"url:{url} 第{index+1}筆 無法找到樓層資料")

        except Exception as e:
            logger.error(f"url:{url} 第{index+1}筆資料的區塊二出現錯誤: {e}")
            return None
        
        sleep(2)

        # 區塊三
        try:
            # 爬取所有 buy-content-basic-cell 下的 div
            block3 = soup.select('div.buy-content-body-grid div.buy-content-basic-cell')

            for div in block3:
                key = div.select_one('div.basic-title').text.strip()
                value_elements = div.select('div.basic-value span')

                # 若 value_elements 存在，則抓取第一個 <span>
                if value_elements:
                    value_text = value_elements[0].text.strip()
                    # 若抓取的 <span> 是 「＋」 或 「＝」，則改抓 <div>
                    if '＋' in value_text or '＝' in value_text:
                        value = div.select_one('div.basic-value').text.strip()
                    else:
                        value = value_text

                # 若 value_elements 不存在，則改抓第一個 <div>
                else:
                    value = div.select_one('div.basic-value').text.strip()
                
                # 因 div.basic-value 會抓取 div下方的所有元素 → 爬取的資料還是會有符號
                if value.endswith('＋') or value.endswith('＝'):
                    # 若尾端有符號，則將之刪除
                    value = value[:-1].strip()

                data[key] = value
                logger.info(f"{key}: {value}")

        except Exception as e:
            logger.error(f"url:{url} 第{index+1}筆的區塊三出現錯誤: {e}")
            return None 
        
        sleep(2)

        # 滑動頁面
        scroll()

        # 區塊四
        try:
            # 爬取經緯度
            try:
                # 等待區塊載入
                block4 = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".view-lifeInfo-btn.d-none.d-lg-inline-block"))
                )
                
                # 使用 JavaScript 執行點擊
                driver.execute_script("arguments[0].click();", block4)

                # 等待資訊載入後，獲取<a>內的資料
                a_information = WebDriverWait(driver, 2).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.d-md-none.d-lg-block a"))
                )

                a_href = a_information.get_attribute('href')

                # 使用正則表達式抓取經緯度
                LL_information = re.search(r'([0-9.]+),([0-9.]+)', a_href)
                if LL_information:
                    keys = ['經度', '緯度']
                    
                    for i in range(len(keys)):
                        # 經緯度
                        key = keys[i]
                        value = LL_information.group(i+1)
                        data[key] = value
                        logger.info(f'{key}: {value}')
                else:
                    logger.error('點擊失敗，無法抓取經緯度')

                sleep(2)

            except Exception as e:
                logger.error(f"url:{url} 第{index+1}筆的區塊四出現錯誤: {e}")
                return None

        except Exception as e:
            logger.error(f"url:{url} 區塊四出現錯誤: {e}")
            return None
        
        # 區域五
        try:
            #圖片
            block5 = soup.select('div.carousel-item.carousel-content-size div.carousel-content-size.carousel-current-img')

            for i, div in enumerate(block5, start=1):
                # 用正則表達式抓取 div 下的 style 內的 圖片網址
                style = div['style']
                url_match = re.search(r'url\((.*?)\)', style)

                if url_match:
                    # 抓取的 url_match 前後可能會有雙引號，用 strip 去掉
                    image_url = url_match.group(1).strip('"').strip("'")
                    data[f'圖片{i}'] = image_url
                    logger.info(f"圖片{i}: {image_url}")
                else:
                    logger.error('無法抓取圖片')
            
            logger.info(f"找到 {len(block5)} 張圖片")
                    
        except Exception as e:
            logger.error(f"url:{url} 區塊五出現錯誤: {e}")
            return None
        
        sleep(1)
        
        # 註記: 記錄爬取網址
        data['網址'] = url

        # 把房屋資料加入列表
        all_house_data.append(data)  # 添加成功抓取的房屋資訊

        # 將所有房屋資料寫入 JSON 檔案
        json_file_path = './XY_house_Taipei/XY_house_Taipei_informationtest.json'
        # json_file_path = './XY_house_NewTaipei/XY_house_NewTaipei_informationtest.json'

        # 儲存當前進度
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(all_house_data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"url:{url} 爬取第{index+1}筆資料時發生錯誤: {e}")
        return None
    
    return data

""" 函式庫 """
if __name__ == "__main__":
    # 檢查路徑、資料夾，若不存在就建立
    log_json_path = './XY_house_Taipei'
    # log_json_path = './XY_house_NewTaipei'
    ensure_directory_exists(log_json_path)

    # 開啟瀏覽器
    driver = set_driver()

    # 設定log
    logger = set_log()
    logger.info('開始信義房屋的爬蟲')

    # 初始化儲存抓取成功 URL 的列表
    all_house_data = []  
    # 初始化儲存抓取失敗 URL 的列表
    error_house_list = []

    # 讀取房屋網址的 List文件
    house_list_path = './XY_house_Taipei/XY_house_Taipei_urls.json'
    # house_list_path = './XY_house_NewTaipei/XY_house_NewTaipei_urls.json'
    readurl = get_house_list(house_list_path)

    # 從第 X 筆資料開始處理，結束於第 Y 筆資料
    (start_index, end_index) = (1, 4903)
    # 依序將文件內的網址組合、開啟，並爬取所需資料
    for index, url in enumerate(readurl[ (start_index-1) : end_index ], start = (start_index-1)):
        house_data = XY_url_information(url, all_house_data, index)
        if house_data:
            logger.info(f"已成功抓取第{index+1}筆房屋資料：{house_data}")
        else:
            logger.error(f"第 {index+1} 筆房屋資料爬取失敗，url:{url}")
            error_house_list.append(url)

    # 關閉
    driver.quit()

    logger.info('所有房屋資料已保存到 JSON 檔案')
    