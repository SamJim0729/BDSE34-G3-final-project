from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import re
import json
import logging
from pprint import pprint
import requests

# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


from bs4 import BeautifulSoup as bs
from time import sleep
import pandas as pd
    
def run_driver(url, proxy=None):
    try:
        #啟用瀏覽器工具選項
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')#最大化視窗
        options.add_argument('--disable-popup-blocking')#禁用彈出連結
        options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"')#修改瀏覽器產生header
        options.add_experimental_option('detach', True)#設定不自動關閉瀏覽器
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})#關閉通知彈跳

        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})#為了console
        options.page_load_strategy = 'normal'

        # PROXY = "localhost:8080"
        # options.add_argument('--proxy-server=%s' % PROXY)
        # PROXY.new_har("test")
        
        #使用Chrome的Driver
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
            })
        """
        })#反爬蟲的網頁，會檢測瀏覽器的 window.navigator是否包含 webdriver 屬性，在正常使用瀏覽器的情況下，webdriver 屬性是 undefined，一旦使用了 selenium 函式庫，這個屬性就被初始化為 true，只要藉由 Javascript 判斷這個屬性，進行反爬蟲(將 webdriver 設定為 undefined)

        #訪問網頁
        driver.get(url)
        # print(PROXY.har)
        return driver
    except:
        print("連線失敗、異常")
    # finally:
    #     driver.quit()

def switch_to_flag(driver, flag):
    frame = driver.find_element(By.TAG_NAME, flag)
    driver.switch_to.frame(frame)
    return driver

def select_condition(driver, cities=[], start_year=None, start_month=None, end_year=None, end_month=None):
    #第一步先找出SELECT的縣市，內部有多少區，放進字典中
    cities_districts_info = {}
    for city in cities:
        select_element = driver.find_element(By.ID, "p_city")
        select_object = Select(select_element)
        select_object.select_by_value(city)
        sleep(6)

        html = driver.page_source
        soup = bs(html, 'html.parser')
        district_list = []
        for tag in soup.select('#p_town > option'):
            # district.get_text() #找出點選city後裡面的區
            if tag['value'] != '':
                district_list.append(tag['value'].strip())
        
        cities_districts_info[city] = district_list
        print(cities_districts_info)
        sleep(6)

    check_whether_searched = False
    data_url_list = []
    for key, values in  cities_districts_info.items():
        # #從這邊開始改
        for value in values:
            # try:
            if check_whether_searched == False:
                data_url_dict = {}
                logger.info(f'city{key}, district{value}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 開始查詢')
                #不回傳結果，因為每次request結果都會在driver.requests中
                #data_url = click_condition_first(driver, key, value, start_year, start_month, end_year, end_month)
                click_condition_first(driver, key, value, start_year, start_month, end_year, end_month)
                sleep(5)
                # data_url_dict[value] = data_url
                # data_url_list.append(data_url_dict)
                check_whether_searched = True
            
            else:
                data_url_dict = {}
                logger.info(f'city{key}, district{value}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 開始查詢')
                click_condition_not_first(driver, key, value, start_year, start_month, end_year, end_month)
                # data_url_dict[value] = data_url
                # data_url_list.append(data_url_dict)
                sleep(5)
            # except:
            #     logger.error(f'city{key}, district{value}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 失敗')

        
def click_condition_first(driver, city, district, start_year, start_month, end_year, end_month):

    #第一個格子選縣市
    select_element = driver.find_element(By.ID, "p_city")
    select_object = Select(select_element)
    select_object.select_by_value(city)
    sleep(10)
    
    #第二個格子選地區
    select_element = driver.find_element(By.ID, "p_town")
    select_object = Select(select_element)
    select_object.select_by_value(district)
    sleep(1)

    #第三個格子時間(開始年、月)
    select_element = driver.find_element(By.ID, "p_startY")
    select_object = Select(select_element)
    select_object.select_by_value(start_year)

    select_element = driver.find_element(By.ID, "p_startM")
    select_object = Select(select_element)
    select_object.select_by_value(start_month)
    sleep(1)

    #第四個格子時間(開始年、月)
    select_element = driver.find_element(By.ID, "p_endY")
    select_object = Select(select_element)
    select_object.select_by_value(end_year)
    sleep(1)

    select_element = driver.find_element(By.ID, "p_endM")
    select_object = Select(select_element)
    select_object.select_by_value(end_month)

    sleep(3)

    #條件設完點選查詢
    # driver.find_elements(By.CLASS_NAME, "btn-a")[1].click()

    try:
        btn_a_elements = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "btn-a"))
        )
        sleep(1)
        btn_a_elements[1].click()
        sleep(1)
        logger.info(f'city{city}, district{district}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 點擊查詢成功')
    except:
        logger.info(f'city{city}, district{district}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 點擊查詢失敗')

    
    
    
    #確認左下查詢結果tag出現後才繼續
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "price_table_info"))
    )
    sleep(5)

    select_total_num_text = driver.find_element(By.ID, "price_table_info").text
    logger.info(f"city{city}, district{district}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month} -> {select_total_num_text}")



#要篩選的欄位會在第一次查詢後，html tag的id 會改變
def click_condition_not_first(driver, city, district, start_year, start_month, end_year, end_month):

    #第一個格子選縣市
    select_element = driver.find_element(By.ID, "l_city")
    select_object = Select(select_element)
    select_object.select_by_value(city)
    sleep(5)
    
    #第二個格子選地區
    select_element = driver.find_element(By.ID, "l_town")
    select_object = Select(select_element)
    select_object.select_by_value(district)
    sleep(1)


    #條件設完點選查詢
    # driver.find_elements(By.CLASS_NAME, "btn-a")[1].click()
    
    # 等待頁面上第二個 'btn-a' 類的元素變為可點擊
    #條件完成時查詢按鍵會被遮罩，不能馬上按
    try:
        btn_a_elements = WebDriverWait(driver, 60).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "btn-a"))
        )
        sleep(10)
        btn_a_elements[1].click()
        logger.info(f'city{city}, district{district}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 點擊查詢成功')
    except:
        logger.info(f'city{city}, district{district}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month}, 點擊查詢失敗')

    
    #確認左下查詢結果tag出現後才繼續
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "price_table_info"))
    )
    
    sleep(4)
    select_total_num_text = driver.find_element(By.ID, "price_table_info").text
    logger.info(f"city{city}, district{district}, s_year{start_year}, s_month{start_month}, e_year{end_year}, e_month{end_month} -> {select_total_num_text}")

    

def get_json_url(driver):
    select_url_set = set()
    for request in driver.requests: 
        re_url = re.search('https:\/\/lvr\.land\.moi\.gov\.tw\/SERVICE\/QueryPrice\/[\S]+[==$]', request.url)
        
        if re_url:
            data_url = re_url.group()
            select_url_set.add(data_url)
    return select_url_set, len(select_url_set)
    

def set_logger():
    '''
    Logging 設定
    '''
    # 基本設定
    logger = logging.getLogger("data_price_crawler")

    # 設定等級
    logger.setLevel(logging.INFO)

    # 設定輸出格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

    # 儲存在 log 當中的事件處理器
    file_handler = logging.FileHandler('house_price_log/data_price_crawler.log', mode='a', encoding='utf-8') # a: append, w: write
    file_handler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 加入事件
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def save_data_url_set(select_url_set, cities, start_year, start_month, end_year, end_month):
    name = ''
    for city in cities:
        name += city 
        
    with open(f'searched_json_url/{name}_start_{start_year}-{start_month}_end_{end_year}-{end_month}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(list(select_url_set)))


if __name__ == '__main__':
    #crawler_condition (t表示今天要撈的條件)
    cities_t = ['F']#台北A、新北F
    start_year_t = '113'
    start_month_t =  '4'
    end_year_t = '113'
    end_month_t = '6'

    logger = set_logger()#在需要的地方埋入資訊
    driver = run_driver("https://lvr.land.moi.gov.tw")
    driver = switch_to_flag(driver, 'frame')

    select_condition(driver, cities=cities_t, start_year=start_year_t, start_month=start_month_t, end_year=end_year_t, end_month=end_month_t)

    select_url_set, select_url_len = get_json_url(driver)

    print(f'select_url_len{select_url_len}')


    save_data_url_set(select_url_set, cities=cities_t, start_year=start_year_t, start_month=start_month_t, end_year=end_year_t, end_month=end_month_t)

    driver.quit()




