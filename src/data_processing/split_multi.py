# 設定log檔案
import logging
import multiprocessing as mp
import os
from time import sleep, time

import lib.corcoordinate_caculate as cc
import pandas as pd

# 建立檔案存放的資料夾
folderPath = "./ok_near_facility/"
if not os.path.exists(folderPath):
    os.makedirs(folderPath)
folderPath = "./problem_near_facility/"
if not os.path.exists(folderPath):
    os.makedirs(folderPath)


# 設定log檔，會放在problem_near_facility資料夾底下
def set_logger():
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)

    # 設定輸出格式
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    # 儲存在 log 當中的事件處理器(存在.log檔中)
    # 設定log檔的檔名也是在此
    fileHandler = logging.FileHandler(
        "./problem_near_facility/record_of_near_facility.log",
        mode="a",
        encoding="utf-8",
    )  # a: append, w: write  #建構方法
    fileHandler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = logging.StreamHandler()  # 建構方法
    console_handler.setFormatter(formatter)  # 將物件設定格式(這邊的formatter)

    # 加入事件
    logger.addHandler(
        console_handler
    )  # addHandler也就是說，這個logger物件要要如何處理log訊息
    logger.addHandler(fileHandler)

    return logger


# 給multiprocessing使用的function，執行特定"檔案"，意思是原先for當中的一次迴圈(一個檔案) (原先的作法是使用for迭代多個檔案)
def process_key(key, test_dict, type_list, near_fac):
    logger = set_logger()
    try:
        start_time_each = time()
        house_df = test_dict[key]
        cc.convert_lat_lon_to_tuple(house_df, "latitude", "longitude")

        for fac_type in type_list:
            start_time = time()
            near_fac_df = near_fac[near_fac["類型"] == fac_type]
            logger.info(f"{key}_{fac_type} started")
            cc.distance_caculate_and_cat_counts(
                house_df, near_fac_df, fac_type, [250, 500, 750]
            )
            logger.info(f"{key}_{fac_type} finish")
            logger.info(f"{key}_{fac_type}:{time() - start_time}")

        house_df.to_csv(f"./ok_near_facility/near_facility_combine_{key}.csv")
        logger.info(
            f"{key} file is saved, each_file_time:{(time() - start_time_each)/60} mins"
        )
    except Exception as e:
        logger.warning(f"{key} have some problem: {e}")
        # 確保在發生錯誤時保存部分結果
        house_df.to_csv(
            f"./problem_near_facility/stash_{key}_but_have_some_problem.csv"
        )


# 再寫一個function設定process_key當中的其他參數，因為使用multiprocessing時，只能有一個參數的變動的(就像是for para in range(): para是可變動參數的意思)
def initialize_pool(test_dict, type_list, near_fac):
    pool = mp.Pool(4)  # mp.Pool(mp.cpu_count()) 使用全部的cpu核心(電腦可能會爆炸喔)
    keys = list(test_dict.keys())

    # 使用 partial 函數來固定參數
    from functools import partial

    # process_key是function name好像算在全域的定義喔?!
    worker = partial(
        process_key, test_dict=test_dict, type_list=type_list, near_fac=near_fac
    )
    pool.map(worker, keys)
    pool.close()
    pool.join()


def main(near_fac_file: str):
    # 比鄰表格，製造cor欄位並創建比鄰類別list
    near_fac = pd.read_csv(near_fac_file)
    cc.convert_lat_lon_to_tuple(near_fac, "Latitude", "Longitude")
    type_list = list(near_fac["類型"].unique())

    # 讀取資料夾下的所有檔案名稱
    dirPath = r"./main_data_piece"
    file_list = os.listdir(dirPath)
    # 讀取檔案，並以dict製造每個dataframe(一個檔案)對應的名稱
    test_dict = {}
    for index, i in enumerate(file_list):
        key = i.split(".")[0]
        test_dict[key] = pd.read_csv(f"{dirPath}/{i}")

    # multiprocessing使用多個cpu同時處理多個檔案
    try:
        start_time = time()
        initialize_pool(test_dict, type_list, near_fac)
    except Exception as e:
        logger.error(f"!!!!critical problem or {e}")
    finally:
        logger.info(f"total_time:{(time() - start_time)/60} mins")


if __name__ == "__main__":

    # 第一次使用時"記得"更改，主資料集位置，分配到的筆數，及給個檔案的大小(可以自己決定，建議絕對不要超過1000)
    # 將主資料集切分成較少筆數(ex: 100 row per file)的多個子資料集，並放在main_data_piece資料夾底下
    folderPath = f"./main_data_piece/"  # 這裡不要改
    if not os.path.exists(folderPath):
        import create_split_main_data as csmd

        ##### 改成自己房屋主資料集的位置 ################
        file_path = "../../all_data/main_data_testing_set_11304_11306.csv"
        # 主資料位置, 筆數開始位置, 筆數結束位置, 每個子檔案多少筆
        csmd.partition_data(file_path, 0, 6300, 100)

    # 這得這個logger設定只有main()接的到，應該是因為他只有一層，其他像process_key()可能是因為他又被包在其他函數當中所以吃不到logger，反正就在裡面宣告多紀錄幾次也無訪
    # return值要記得用變數接.....
    logger = set_logger()
    logger.info("starting")

    ##########################################
    # 主程式
    # 比鄰表格檔案位置記得要改
    main(near_fac_file="../../all_data/near_fac_corrected.csv")
    ##########################################

    logger.info("end")
