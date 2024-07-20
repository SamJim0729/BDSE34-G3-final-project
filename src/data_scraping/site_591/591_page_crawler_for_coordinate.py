import json
import logging
import os
import re
import warnings
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

warnings.filterwarnings("ignore")


def set_logger():
    # 基本設定
    logger = logging.getLogger("crawler_591_log")

    # 設定等級
    logger.setLevel(logging.INFO)

    # 設定輸出格式
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    # 儲存在 log 當中的事件處理器
    file_handler = logging.FileHandler(
        "log/591_page_crawler_for_coordinate.log", mode="a", encoding="utf-8"
    )  # a: append, w: write
    file_handler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 加入事件
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def set_driver():
    global driver
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')#不開啟瀏覽器視窗
    options.add_argument("--start-maximized")  # 最大化視窗
    options.add_argument("--disable-popup-blocking")  # 禁用彈出連結
    options.add_argument(
        '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"'
    )  # 修改瀏覽器產生header
    options.add_experimental_option("detach", True)  # 設定不自動關閉瀏覽器
    options.add_experimental_option(
        "prefs", {"profile.default_content_setting_values.notifications": 2}
    )  # 關閉通知彈跳
    driver = webdriver.Chrome(options=options)
    return driver

def driver_quit(driver):
    driver.quit()


# 滑到網頁最底部
def scroll():
    # '''
    # innerHeight => 瀏覽器內部的高度
    # offset => 當前捲動的量(高度)
    # count => 累計無效滾動次數
    # limit => 最大無效滾動次數
    # '''
    innerHeight = 0
    offset = 0
    count = 0
    limit = 3

    # 在捲動到沒有元素動態產生前，持續捲動
    while count <= limit:
        # 每次移動高度
        offset = driver.execute_script(
            "return document.documentElement.scrollHeight;"
        )  # 文件的完整高度

        """
        或是每次只滾動一點距離，
        以免有些網站會在移動長距離後，
        將先前移動當中的元素隱藏

        例如將上方的 script 改成:
        offset += 600
        """

        # 捲軸往下滑動
        driver.execute_script(
            f"""
            window.scrollTo({{
                top: {offset}, 
                behavior: 'smooth' 
            }});
        """
        )

        """
        [補充]
        如果要滾動的是 div 裡面的捲軸，可以使用以下的方法
        document.querySelector('div').scrollTo({...})
        """

        # (重要)強制等待，此時若有新元素生成，瀏覽器內部高度會自動增加
        sleep(3)

        # 透過執行 js 語法來取得捲動後的當前總高度
        innerHeight = driver.execute_script(
            "return document.documentElement.scrollHeight;"
        )

        # 經過計算，如果滾動距離(offset)大於等於視窗內部總高度(innerHeight)，代表已經到底了
        if offset == innerHeight:
            count += 1

        # 為了實驗功能，捲動超過一定的距離，就結束程式
        if offset >= 600:
            sleep(3)
            break


def get_house_list(path: str):
    with open(f"{path}", "r") as f:
        data = f.read()
    house_list = json.loads(data)
    return house_list


def get_single_page_coordinate(partial_url, driver):
    try:
        single_entry = {}
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.detail-house-title"))
        )
        sleep(1)
    except:
        logger.error(f"url:{partial_url}, 有可能斷線，或是網頁標的移除了")
        return

    try:
        scroll()
    except:
        logger.error(f"url:{partial_url}, 滾動網頁失敗")
        return

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#detail-map-free"))
        )
    except:
        logger.error(f"url:{partial_url}, 沒定位到iframe")
        return
    sleep(6)

    try:
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe#detail-map-free")
        coordinate_text = str(iframe.get_attribute("src"))
        coordinate = re.search(r"(?<=&q=).*(?=&language)", coordinate_text)
        coordinate = coordinate[0].split(",")

        single_entry["url"] = partial_url
        single_entry["latitude"] = coordinate[0]  # 緯度
        single_entry["longtitude"] = coordinate[1]  # 經度
    except:
        logger.error(f"url:{partial_url}, 經緯度取得失敗")
        return
    return single_entry


def get_total_coordinate(house_partial_url_list: list, driver, target, start, end):
    now = datetime.now()
    formatted_now = now.strftime("%Y%m%d_%H%M%S")
    total_house_coordinate = []
    total_error_house_coordinate = []
    count_times = 0
    count_to_save = 0
    save_at_threshold = 5

    directory = "result-data"
    if not os.path.exists(directory):
        os.makedirs(directory)

    #美幾次重開broswer降低iframe異常
    threshold_restart_driver = 100
    count_for_restart = 0
    
    for house_partial_url in house_partial_url_list[start:end]:
        url = f"https://sale.591.com.tw{house_partial_url}"
        if count_for_restart < threshold_restart_driver:
            driver.get(url)
            single_house_coordinate = get_single_page_coordinate(house_partial_url, driver)
            count_for_restart += 1
        else:
            driver_quit(driver)
            driver = set_driver()
            driver.get(url)
            sleep(10)
            single_house_coordinate = get_single_page_coordinate(house_partial_url, driver)
            count_for_restart = 1
            logger.info(f'重開瀏覽器避免瀏覽器異常')
        
        
        if single_house_coordinate:
            total_house_coordinate.append(single_house_coordinate)
        else:
            total_error_house_coordinate.append(house_partial_url)
        if count_to_save == save_at_threshold:
            with open(
                f"result-data/{formatted_now}_{target}_coordinate_{start}_to_{end}.json",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(
                    json.dumps(total_house_coordinate, ensure_ascii=False, indent=4)
                )

            with open(
                f"result-data/{formatted_now}_{target}_coordinate_error_list_{start}_to_{end}.json",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(
                    json.dumps(
                        total_error_house_coordinate, ensure_ascii=False, indent=4
                    )
                )
            logger.info(
                f"已經存了{len(total_house_coordinate)}筆成功資料，{len(total_error_house_coordinate)}筆失敗資料，目前執行到{target}list中第{start+count_times}筆，若斷掉了就從這繼續"
            )
            count_to_save = 0
        count_times += 1
        count_to_save += 1

    with open(
        f"result-data/{formatted_now}_{target}_coordinate_{start}_to_{end}.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(total_house_coordinate, ensure_ascii=False, indent=4))

    with open(
        f"result-data/{formatted_now}_{target}_coordinate_error_list_{start}_to_{end}.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(total_error_house_coordinate, ensure_ascii=False, indent=4))
    logger.info(
        f"結束了，總共存了{len(total_house_coordinate)}筆成功資料，{len(total_error_house_coordinate)}筆失敗資料"
    )


if __name__ == "__main__":
    logger = set_logger()
    driver = set_driver()
    target = "newtaipei"  # (決定要爬的檔案)#################################
    # target = 'taipei'#
    logger.info(f"接下來要跑{target}，591_中古屋_coordinate清單")
    house_partial_url_list = get_house_list(f"references/{target}_591_all_list.json")
    total_house_coordinate = get_total_coordinate(
        house_partial_url_list, driver, f"{target}", start=0, end=1719
    )  # (改需要爬的筆數)#######################################################
    driver.quit()
