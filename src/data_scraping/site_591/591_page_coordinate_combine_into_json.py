import os
import json
import pandas as pd
import re
import numpy as np

#對照page/coordinate非error的檔名，自動合併檔案
def merged_json_output_page_coordinate_list(path:str):
    result_list = os.listdir(path)
    all_page_data = []
    all_coordinate_data = []
    count_page = 0
    count_coordinate = 0
    for file in result_list: #合併大家的檔案
        if ('error' not in file) and ('coordinate' not in file): #抓成功的page檔合併
            count_page += 1
            with open(f'{path}/{file}', 'r', encoding='utf-8') as f:
                success_page_file = json.loads(f.read())
            all_page_data += success_page_file

        if ('error' not in file) and ('coordinate' in file): #抓成功的coordinate檔合併
            count_coordinate += 1
            with open(f'{path}/{file}', 'r', encoding='utf-8') as f:
                success_coordinate_file = json.loads(f.read())
            all_coordinate_data += success_coordinate_file

    print(f'count_page_files:{count_page}')
    print(f'count_coordinate_files:{count_coordinate}')


    return all_page_data, all_coordinate_data

#把page檔資訊合併coordinate檔座標，return df
def combine_page_coordinate_data_into_df(all_page_data:list, all_coordinate_data:list):
    combine_page_coordinate = []
    for page_data in all_page_data: #把page資料透過url做合併
        for coordinate_data in all_coordinate_data:
            if page_data['url'] == coordinate_data['url']:
                page_data['latitude'] = coordinate_data['latitude']
                page_data['longtitude'] = coordinate_data['longtitude']
                combine_page_coordinate.append(page_data)
                continue

    check_unique_urls = set()
    combine_page_coordinate_unique = []
    for data in combine_page_coordinate: #最終清單只取url唯一值
        if data['url'] not in check_unique_urls:
            check_unique_urls.add(data['url'])
            combine_page_coordinate_unique.append(data)
    print(f'總共page資料:{len(all_page_data)}筆資料,合併座標成功且url不重複{len(combine_page_coordinate_unique)}筆')
    df = pd.DataFrame(combine_page_coordinate_unique)
    df.to_csv('591_final_data.csv')
    return df

def df_col_str_to_num(df, columns:list):
    df[columns] = df[columns].apply(pd.to_numeric)
    return df

#XX坪轉成數字
def df_unit_ping_to_num(df, columns:list):
    for col in columns:
        df[col] = df[col].str.replace('坪', '').astype('float')
    return df

#X年或X月轉成以年為單位
def df_unit_year_to_num(df, columns:list):
    for col in columns:
        temp_list = []
        for item in df[col]:
            if item == None:
                temp_list.append(None)
            elif '年' in item:
                temp_list.append(int(item.replace('年', '')))
            elif '個月' in item:
                temp_list.append(int(item.replace('個月', ''))/12)
            else:
                temp_list.append(None)
        df[col] = temp_list
    return df

#處理權狀坪數
def df_total_area_to_num(df, column:str):
    temp_ping_list = []
    temp_include_parking_space_list = []
    for item in df[column]:
        if item == '':
            temp_ping_list.append(None)
        else:
            temp_ping_list.append(item.split('坪')[0])

        if '含車位' in item:
            temp_include_parking_space_list.append(1)
        else:
            temp_include_parking_space_list.append(0)        
    df[column] = temp_ping_list
    df['含車位'] = temp_include_parking_space_list
    print("新增車位column")
    return df
            
#處理管理費
def df_management_fee_to_num(df, column:str):
    temp_management_fee_list = []
    for item in df[column]:
        if item == '無' or item == '':
            temp_management_fee_list.append(None)
        elif '年' in item:
            temp_management_fee_list.append(float(item.split('元')[0]))
        elif '月' in item:
            temp_management_fee_list.append(float(item.split('元')[0])*12)
        elif '季' in item:
            temp_management_fee_list.append(float(item.split('元')[0])*4)
        else:
            temp_management_fee_list.append(None)
    df[column] =  temp_management_fee_list
    return df

#樓層轉換成3個欄位
def df_floor_level(df, column:str):
    df[column] = df[column].str.replace('F', '')
    df_floors_split = df[column].str.split('/', expand=True)
    print(df_floors_split)
    df_floors_split.columns = ['temp_floors', 'total_floors']


    temp_target_floors_list = []
    temp_transaction_floors_list = []
    for index ,item in enumerate(df_floors_split['temp_floors']):
        if item == 'None' or item == 'nan':
            temp_target_floors_list.append(np.nan)
            temp_transaction_floors_list.append(np.nan)
        else:
            if '頂樓加蓋' in item:
                temp_target_floors_list.append(int(df_floors_split['total_floors'][index])+1)
                temp_transaction_floors_list.append(1)
                continue
                
            if '整棟' in item:
                temp_target_floors_list.append(1)
                temp_transaction_floors_list.append(int(df_floors_split['total_floors'][index]))
                continue

            if '~' in item:
                temp_floors = item.split('~')
                if 'B' in item:
                    temp_target_floors_list.append(int(temp_floors[0][1:])*-1)
                    temp_transaction_floors_list.append(int(temp_floors[0][1:]) + int(temp_floors[1]))
                else:
                    temp_target_floors_list.append(temp_floors[0])
                    temp_transaction_floors_list.append(int(temp_floors[1])-int(temp_floors[0])+1)
            
            else:
                temp_transaction_floors_list.append(1)
                if 'B' in item:
                    temp_target_floors_list.append(int(item[1:])*-1)
                else:
                    temp_target_floors_list.append(int(item))
    df['total_floors'] = df_floors_split['total_floors']
    df['transaction_floors'] = temp_transaction_floors_list
    df['target_floors'] = temp_target_floors_list
    # df[['樓層','transaction_floors', 'target_floors', 'total_floors']].to_csv('test_floors.csv', encoding = 'utf-8')
    return df
                    

def df_building_layout_to_number(df, column:str):
    df[['bedrooms', 'living_rooms', 'bathrooms', 'balcony']] = df[column].str.extract(r'(?:(\d*)房)?(?:(\d*)廳)?(?:(\d*)衛)?(?:(\d*)陽台)?')
    return df
            


if __name__ == '__main__':
    # all_page_data, all_coordinate_data = merged_json_output_page_coordinate_list(path = 'C:\\Users\\user\\Desktop\\591\\success_data')
    # df = combine_page_coordinate_data_into_df(all_page_data, all_coordinate_data)
    df = pd.read_csv('591_final_data_cleaned.csv')
    # df.info()
    
    # #欄位轉數字處理
    df['公設比'] = df['公設比'].str.replace("%", "").astype(float)/100
    df = df_col_str_to_num(df, ['總價', 'latitude', 'longtitude'])
    df = df_unit_ping_to_num(df, ['主建物','共用部分','附屬建物','土地坪數', '現況坪數', '土地（持分）坪數'])
    df['屋齡'] = df['屋齡'].astype('str')
    df = df_unit_year_to_num(df, ['屋齡'])
    df['權狀坪數'] = df['權狀坪數'].astype('str')
    df = df_total_area_to_num(df, '權狀坪數')
    df['管理費'] = df['管理費'].astype('str')
    df = df_management_fee_to_num(df, '管理費')
    df['樓層'] = df['樓層'].astype('str')
    df = df_floor_level(df, '樓層')
    df = df_building_layout_to_number(df, '格局')
    df = df.drop(columns=[df.columns[0], 'url', 'total_price_list', '格局', '樓層', '車位類型'])
    df = df[df['現況']!='車位']




    # #欄位onehot
    df['帶租約'] = pd.get_dummies(df['帶租約'], prefix='帶租約')['帶租約_是'].astype(int)
    
    # df.to_csv('591_final_data_cleaned.csv', encoding='utf-8', index=False)
    # df.to_json('591_final_data_cleaned.json', orient='records', force_ascii=False, indent=4)




    






    
