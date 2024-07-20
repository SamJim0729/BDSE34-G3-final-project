import json
import logging
import os
import re
import warnings
from datetime import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup

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
        "log/591_page_crawler.log", mode="a", encoding="utf-8"
    )  # a: append, w: write
    file_handler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 加入事件
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def get_single_page_info(partial_url):
    url = f"https://sale.591.com.tw{partial_url}"

    #############開始找出重要變數#############
    single_entry = {}  # 一筆row data，全部存在字典中
    # 因變數欄位在不同案件中可能會沒有，用for找出區塊有的欄位，再填入字典
    #########################################

    single_entry["url"] = partial_url

    # reqrest案件html，透過soup解析(591一定要加hearder)
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, "html.parser")

        try:
            # 總價
            info_price_num = soup.select_one("span.info-price-num").text
            # single_entry['總價'] = re.search(r'(\s+)?(\S+)(\s+)?萬元', info_price_num)
            info_price_num_list = re.split(
                r"\s+", info_price_num
            )  # 可能要切萬元前面字串
            single_entry["總價"] = info_price_num_list[0]
            single_entry["total_price_list"] = info_price_num_list
        except:
            logger.error(f"url:{url} ;  問題:總價部分有問題")
            return None

        try:
            # 格局、屋齡、權狀坪數
            top_right_block_titles_tags_1 = soup.select("div.info-floor-value")
            for num, item in enumerate(top_right_block_titles_tags_1):
                single_entry[item.text] = soup.select("div.info-floor-key")[num].text

            # 樓層、朝向、社區、地址
            top_right_block_titles_tags_2 = soup.select(
                "span.info-addr-key"
            )  # 找出這個區塊有哪些項目
            for num, item in enumerate(top_right_block_titles_tags_2):
                single_entry[item.text] = soup.select(".info-addr-value")[
                    num
                ].text  # 對應tilte與對應值放入dict
        except:
            logger.error(f"url:{url} ;  問題:網頁右上房屋資訊有問題")
            return None

        try:
            # (房屋介紹)透過迴圈取出內容放入single_entry，屋況特色不在範圍內
            for item in soup.select("div.detail-house-box"):
                if item.select("div.detail-house-value"):
                    if item.select("div.detail-house-key"):
                        bottom_block_titles = item.select("div.detail-house-key")
                        for num, item_title in enumerate(bottom_block_titles):
                            single_entry[item_title.text] = item.select(
                                "div.detail-house-value"
                            )[num].text
                    else:
                        temp = []
                        for value in item.select("div.detail-house-value"):
                            temp.append(value.text)
                        single_entry[item.select("div.detail-house-name")[0].text] = (
                            temp
                        )

                else:
                    temp = []
                    for value in item.select("div.detail-house-life"):
                        temp.append(value.text)
                    single_entry[item.select("div.detail-house-name")[0].text] = temp

            # 屋況特色(格式很亂，不撈)

        except:
            logger.error(f"url:{url} ;  問題:網頁下方房屋介紹有問題")
            return None

        try:
            if soup.select_one("div.house-pic-title"):
                temp_house_image_url = []
                for image in soup.select("div.pic-box-item"):
                    try:
                        temp_house_image_url.append(
                            image.select_one("img.pic-box-img")["data-original"]
                        )
                    except:
                        continue
                single_entry[soup.select_one("div.house-pic-title").text] = (
                    temp_house_image_url
                )
            else:
                single_entry[soup.select_one("div.house-pic-title").text] = None
        except:
            logger.error(f"url:{url} ;  問題:網頁下方應該沒有圖片，不會進入重撈list")

        return single_entry
    else:
        logger.error(f"url:{url}, res連線失敗，可能是標的已移除")
        return None


def get_house_list(path: str):
    with open(f"{path}", "r") as f:
        data = f.read()
    house_list = json.loads(data)
    return house_list


def get_total_house_info(house_partial_url_list: list, target: str, start, end):
    now = datetime.now()
    formatted_now = now.strftime("%Y%m%d_%H%M%S")
    total_house_info = []
    error_house_list = []
    count_to_save = 0
    count_times = 0
    save_at_threshold = 5

    directory = "result-data"
    if not os.path.exists(directory):
        os.makedirs(directory)

    for house_partial_url in house_partial_url_list[start:end]:
        sleep(6)
        single_entry_dict = get_single_page_info(house_partial_url)
        if single_entry_dict:
            total_house_info.append(single_entry_dict)
        else:
            logger.error(f"url:{house_partial_url}, 已加入重撈清單")
            error_house_list.append(house_partial_url)

        if count_to_save == save_at_threshold:  # 每達到設定值，就存一次，避免失敗
            with open(
                f"result-data/{formatted_now}_{target}_page_error_list_{start}_to_{end}.json",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(
                    json.dumps(error_house_list, ensure_ascii=False, indent=4)
                )  # 最後結束時再存一次

            with open(
                f"result-data/{formatted_now}_{target}_page_result_{start}_to_{end}.json",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(json.dumps(total_house_info, ensure_ascii=False, indent=4))
            logger.info(
                f"已經存了{len(total_house_info)}筆成功資料，{len(error_house_list)}筆失敗資料，目前執行到{target}list中第{start+count_times}筆，若斷掉了就從這繼續"
            )
            count_to_save = 0
        count_times += 1
        count_to_save += 1

    with open(
        f"result-data/{formatted_now}_{target}_page_error_list_{start}_to_{end}.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(
            json.dumps(error_house_list, ensure_ascii=False, indent=4)
        )  # 最後結束時再存一次

    with open(
        f"result-data/{formatted_now}_{target}_page_result_{start}_to_{end}.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(total_house_info, ensure_ascii=False, indent=4))
    logger.info(
        f"結束了，總共存了{len(total_house_info)}筆成功資料，{len(error_house_list)}筆失敗資料"
    )
    return total_house_info


if __name__ == "__main__":
    # (執行前要切到py檔目錄位置)########################################################
    # (改這邊決定要撈哪一個檔案)########################################################
    # target = "taipei"
    target = "newtaipei"  #
    logger = set_logger()
    logger.info(f"接下來要跑{target}，591_中古屋_info清單")
    house_partial_url_list = get_house_list(f"references/{target}_591_all_list.json")
    # 下面決定負責的範圍[start:end]#####################################################
    total_house_info = get_total_house_info(
        house_partial_url_list, target, start=0, end=1127
    )
