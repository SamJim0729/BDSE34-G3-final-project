####台北先跑，再跑新北，透過資料夾資料分###

import os
from dotenv import load_dotenv
import json
import requests
import pandas as pd
import re
from sqlalchemy import create_engine
from urllib.parse import quote
import logging

def files_combine(path):
    file_names = os.listdir(path)
    logger.info(f'本次url的檔案包含{file_names}')
    merged_file = []
    for file_name in file_names:
        with open(f'{path}/{file_name}') as f:
            json_str = f.read()
        file_list = json.loads(json_str)
        logger.info(f'{file_name}: {len(file_list)}') #check資料筆數是否撈的正確
        merged_file.extend(file_list)  #把list合併
    logger.info(f'本次抓取總網址數量:{len(merged_file)}')
    return merged_file   #所有網址合併的list
        
def read_json_urls_merged_return_df(merged_file):
    merged_json_file = []
    failed_file = []
    for url in merged_file:
        print('ready to connect')
        response = requests.get(url) #沒連線到網址內容不會報錯，要靠status_code判斷
        if response.status_code == 200:
            print('success')
            data = response.json()
            merged_json_file.extend(data)
        else:
            print('fail')
            failed_file.append(url)
    if failed_file != []:
        logger.error(f'共 "{len(failed_file)}" 筆資料獲取失敗，url記錄至failed_file_urls.json')
        with open('failed_file_urls.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(failed_file))
    try:
        df = pd.DataFrame(merged_json_file)
    except:
        logger.error('資料轉pd異常')
    return df
    
def change_df_head(df):
    rename_dict = {}
    df_for_rename = pd.read_csv('head_rename_final.csv')
    for index, row in df_for_rename.iterrows():
        rename_dict[row['KEY'].strip()] = row['KEY_new']
    df.rename(columns=rename_dict, inplace=True)
    return df
    # df.to_csv('temp_df_changed_head.csv', encoding='utf-8')

def df_column_str_to_num(df , col_name_list, delimite_str=None):
    for name in col_name_list:
        df[name] = pd.to_numeric(df[name].str.replace(pat=delimite_str, repl=''))
    return df
    
def minguo_to_ad(df, col_name_str):
    temp_change_date_list = []
    count_month_day_error = 0
    for item in df[col_name_str]:
        year, month, day = item.split('/')
        year = int(year) + 1911
        #month/day有包含0跟奇怪格式的值，先判斷是否都有數值
        
        if month.isdigit() and day.isdigit():
            if int(month) == 0 or int(day) == 0:
                logger.error(f'民國轉西元{year}/{month}/{day}有誤，轉換為{year}/1/1')
                count_month_day_error += 1
                month = 1
                day = 1
        else:
            logger.error(f'民國轉西元{year}/{month}/{day}有誤，轉換為{year}/1/1')
            count_month_day_error += 1
            month = 1
            day = 1

        date_str = f'{year}/{month}/{day}'
        temp_change_date_list.append(date_str)
    logger.error(f'minguo_to_ad 轉換中 "{count_month_day_error}" 筆資料異常')
    df['transaction_date'] = pd.to_datetime(temp_change_date_list)
    logger.info(f'df新增transaction_date欄位')
    return df

def floor_height_to_three_columns(df, col_name_str):
        final_total_floors_list = []
        final_target_floors_list = []
        final_transaction_floors_list = []
        for row in df[col_name_str]:
            if row == '':
                final_total_floors_list.append(None)
                final_target_floors_list.append(None)
                final_transaction_floors_list.append(None)
            else:
                #1.建物有幾層 (這邊會呼叫chinese_floor_to_number方法)
                temp_total_floor = chinese_floor_to_number(row.split('/')[1])
                final_total_floors_list.append(temp_total_floor)

                #2.目標在第幾層 (這邊會呼叫chinese_floor_to_number方法)
                temp_target_floor = row.split('/')[0].split(',')[0]
                temp_target_floor = chinese_floor_to_number(temp_target_floor)
                final_target_floors_list.append(temp_target_floor)

                #3.總共交易幾層
                temp_transaction_floors_list = row.split('/')[0].split(',')
                num = 0
                for floor in temp_transaction_floors_list:
                    if '全' in floor:
                        num = temp_total_floor
                        break
                    if '夾' in floor:
                        num -= 1 #'夾層'算0 = 夾(-1)+層(1)
                    if '層' in floor:
                        num += 1
                final_transaction_floors_list.append(num)

        df['total_floors'] = final_total_floors_list  
        df['target_floor'] = final_target_floors_list
        df['transaction_floors'] = final_transaction_floors_list 
        logger.info(f'df新增total_floors欄位')
        logger.info(f'df新增target_floor欄位')
        logger.info(f'df新增transaction_floors欄位')


        return df

def building_layout_to_number(df, col_name_str):
    temp_bedrooms_list = []
    temp_living_rooms_list = []
    temp_bathrooms_list = []
    for row in df[col_name_str]:
        match_building_layout = re.search(r'(?P<bed>\d*房)?(?P<liv>\d*廳)?(?P<bath>\d*衛)?',row)
        if match_building_layout.group()=='':
            temp_bedrooms_list.append(None)
            temp_living_rooms_list.append(None)
            temp_bathrooms_list.append(None)
        else:
            if match_building_layout.group('bed'):
                temp_bedrooms_list.append(int(match_building_layout.group('bed')[:-1]))
            else:
                temp_bedrooms_list.append(0)

            if match_building_layout.group('liv'):
                temp_living_rooms_list.append(int(match_building_layout.group('liv')[:-1]))
            else:
                temp_living_rooms_list.append(0)

            if match_building_layout.group('bath'):
                temp_bathrooms_list.append(int(match_building_layout.group('bath')[:-1]))
            else:
                temp_bathrooms_list.append(0)

    df['bedrooms'] = temp_bedrooms_list
    df['living_rooms'] = temp_living_rooms_list
    df['bathrooms'] = temp_bathrooms_list
    logger.info(f'df新增bedrooms欄位')
    logger.info(f'df新增living_rooms欄位')
    logger.info(f'df新增bathrooms欄位')         
    return df

def chinese_floor_to_number(chinese_floor_str):
    
    #傳進來的str不包含層
    num_dict = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                '六': 6, '七': 7, '八': 8, '九': 9}
    mul_dict = {'十': 10, '百': 100}
    basement_dict = {'地下': -1, '地下層': -1, '防空避難室': -1}
    all_dict = {'全': 1}
    mezzanine_dict = {'夾層': None}
    arcade_dict = {'騎樓': 1}
    
    #處理欄位為df['floor_num']空值情況
    if chinese_floor_str == '':
        return None
    
    #處理欄位為df['floor_num']為'--'情況
    if chinese_floor_str == '--':
        return None

    #處理'地下層'
    if chinese_floor_str[:3] in basement_dict:
        return -1
    
    #處理'地下X層'
    if chinese_floor_str[:2] in basement_dict:
        return num_dict[chinese_floor_str[2:3]] * -1

    #處理'防空避難室'
    if chinese_floor_str[:5] in basement_dict:
        return -1
    
    #處理'全'
    if chinese_floor_str[0:1] in all_dict:
        return 1
    
    #處理'夾層'
    if chinese_floor_str[0:2] in mezzanine_dict:
        return None
    
    #處理'騎樓'
    if chinese_floor_str[0:2] in arcade_dict:
        return 1
    
    #處理'XXX層'
    #先處理進來的str最後一字有沒有包含層
    if chinese_floor_str[-1] == '層':

        #處理'X層'
        chinese_floor_str = chinese_floor_str[:-1]
        if chinese_floor_str in num_dict:
            return num_dict[chinese_floor_str]
        
        #處理'X十X層'
        temp_num = 0
        final = 0
        for char in chinese_floor_str:
            if char in num_dict:
                temp_num = num_dict[char]
            elif char in mul_dict:
                if temp_num == 0:
                    temp_num = 1
                final = temp_num * mul_dict[char]
                temp_num = 0
            final += temp_num
        return final

    else: 
        return None

def first_process_for_sql(df):
    #先drop掉確定不要的欄位
    df.drop(columns=['useless_1', 'useless_2', 'useless_3', 'useless_4', 'useless_5', 'useless_6', 'useless_7', 'useless_8', 'useless_9', 'useless_10', 'useless_11', 'useless_12', 'useless_13', 'image_file'], inplace=True)


    #把數值欄位改數值型態，透過上方的方法df_column_str_to_num()
    df = df_column_str_to_num(df, ['main_building_ratio'], '%')
    # df = df_column_str_to_num(df, ['total_price', 'parking_space_price'], ',')
    temp_list = ['building_age', 'number_of_land', 'number_of_building', 'number_of_parking_space', 'total_area_ping','total_price', 'parking_space_price', 'price_per_ping']
    df = df_column_str_to_num(df, temp_list, ',')
    
    #把交易時間欄位民國轉西元，方法是minguo_to_ad()
    df = minguo_to_ad(df, 'transaction_date')

    #把二元變數改為0,1
    df['elevator_available'] = df['elevator_available'].map({'有':1, '無':0})
    df['management_org_available'] = df['management_org_available'].map({'有':1, '無':0})

    
    #把樓別/樓高轉成1.建物幾層 2.目標在哪一層(只判斷第一項，且'夾層'=None)，3.交易幾層('夾層'=0.5)，(Ans:0表示交易的標的不屬於層ex:陽台、屋頂，None表示未知)
    df = floor_height_to_three_columns(df, 'floor_height')
    df.drop(columns=['floor_height'], inplace=True)

    #把building_layout分成1.幾房 2.幾廳 3.幾衛
    df = building_layout_to_number(df, 'building_layout')
    df.drop(columns=['building_layout'], inplace=True)
    return df

def connect_sql_to_insert_df(df):
    load_dotenv()# 從 .env 文件加載環境變量
    
    #建立資料庫串接
    host = os.getenv('HOST')
    username = os.getenv('USERNAME')
    password = quote(os.getenv('PASSWORD'))
    port = int(os.getenv('PORT'))
    database = os.getenv('DATABASE')

    try:
        engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}')
        df.to_sql(name='house_transaction_info', con=engine, if_exists='append', index=False)
        print('資料放入資料庫成功')
        logger.info('資料放入資料庫成功')
    except:
        logger.error('資料放入資料庫失敗')
    
    engine.dispose()
    
def set_logger():
    '''
    Logging 設定
    '''
    # 基本設定
    logger = logging.getLogger("data_price_store_log")

    # 設定等級
    logger.setLevel(logging.INFO)

    # 設定輸出格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")

    # 儲存在 log 當中的事件處理器
    file_handler = logging.FileHandler('house_price_log/data_price_store.log', mode='a', encoding='utf-8') # a: append, w: write
    file_handler.setFormatter(formatter)

    # 輸出在終端機介面上的事件處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 加入事件
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


if __name__ == '__main__':
    logger = set_logger()
    data_url_path = 'searched_json_url'
    merged_url = files_combine(data_url_path)
    df = read_json_urls_merged_return_df(merged_url)
    #df.to_csv('house_price_csv_data/新北市_10101_11303_房價_原始資料.csv')
    df = change_df_head(df)
    try:
        df.to_csv('house_price_csv_data/新北市_11304_11306_房價before.csv')
    except:
        logger.error(f'新北市_11304_11306_房價before_csv存取異常')
    df = first_process_for_sql(df)
    #connect_sql_to_insert_df(df)
    try:
        df.to_csv('house_price_csv_data/新北市_11304_11306_房價after.csv')
    except:
        logger.error(f'新北市_11304_11306_房價after_csv存取異常')



    

    

    

