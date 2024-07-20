from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup 
import warnings
import json
import logging
warnings.filterwarnings("ignore")


def set_logger():
    # 基本設定
    logger = logging.getLogger("crawler_591_log")

    # 設定等級
    logger.setLevel(logging.INFO)

    # 設定輸出格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

    # 儲存在 log 當中的事件處理器
    file_handler = logging.FileHandler('house_price_log/591_crawler.log', mode='a', encoding='utf-8') # a: append, w: write
    file_handler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 加入事件
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

def run_driver(url):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')#不開啟瀏覽器視窗
    options.add_argument('--start-maximized')#最大化視窗
    options.add_argument('--disable-popup-blocking')#禁用彈出連結
    options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"')#修改瀏覽器產生header
    options.add_experimental_option('detach', True)#設定不自動關閉瀏覽器
    options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})#關閉通知彈跳
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    return driver

# def get_crawler_list(url):

def save_all_page_house_list(driver, save_file_name=str()):
    all_house_list = set()
    all_house_error_list = set()
    house_list_page = 1
    current_url = driver.current_url
    while True:
        try: #若token到期報錯，重新連線chrome
            #等待"為您推薦"出現在開始撈
            WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "houseList-head-title"))
            )

            sleep(6)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            house_samples = soup.select("div.houseList-item-main.oh")
            count_page_house_num = 0
            for item in house_samples:
                a_tag = item.select_one("div.houseList-item-title").select_one('a')
                if a_tag.has_attr('href'):
                    if a_tag['href'][0:5] == '/home':
                        # all_house_list.append(a_tag['href'])
                        all_house_list.add(a_tag['href'])
                        count_page_house_num += 1
                    else:
                        logger.error(f"奇怪的網址:{a_tag['href']}")
                        # all_house_error_list.append(a_tag['href'])
                        all_house_error_list.add(a_tag['href'])

            
            
            try:
                with open(f'searched_json_url/{save_file_name}_house_url_list_2.json', 'w', encoding='utf-8') as f:
                    f.write(json.dumps(list(all_house_list)))
                with open(f'searched_json_url/{save_file_name}_house_url_error_list_3.json', 'w', encoding='utf-8') as f:
                    f.write(json.dumps(list(all_house_error_list)))
            except:
                logger.error(f'第{house_list_page}頁儲存異常')
                

            try:
                driver.find_element(By.CSS_SELECTOR, 'a.pageNext.last')
                logger.info(f"爬完第{house_list_page}頁，本頁{count_page_house_num}筆資訊:終於爬完")
                logger.info(f"總共{len(all_house_list)}筆")
                break

            except:
                logger.info(f"爬完第{house_list_page}頁，本頁{count_page_house_num}筆資訊:繼續努力")
                sleep(4)
                current_url = driver.current_url
                driver.find_element(By.CSS_SELECTOR, 'a.pageNext').click()
                house_list_page += 1
        except:
            logger.error(f'網頁異常重開連線，從失敗的上一個網址重爬{current_url}')
            sleep(5)
            driver = run_driver(current_url)
            sleep(5)

    





if __name__ == '__main__':
    logger = set_logger()
    #隨時間total_rows會增加，網址會變，但舊網址可以用
    # url_second_handHouse_taipeicity = 'https://sale.591.com.tw/?category=1&shType=list&regionid=1'
    url_second_handHouse_newtaipeicity = 'https://sale.591.com.tw/?category=1&shType=list&regionid=3'
    
    driver = run_driver(url_second_handHouse_newtaipeicity)
    sleep(5)
    save_all_page_house_list(driver, 'newtaipeicity_restart')
    driver.quit()
















