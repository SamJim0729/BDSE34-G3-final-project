import json
import os



#查看路徑中有多少檔案(list)
result_data_list = os.listdir('result-data')

rerun_newtaipei_page_error_list = []
rerun_newtaipei_coordinate_error_list = []
rerun_taipei_page_error_list = []
rerun_taipei_coordinate_error_list = []

newtaipei_count_page_error = 0
newtaipei_count_coordinate_error = 0
taipei_count_page_error = 0
taipei_count_coordinate_error = 0

#迴圈把錯誤要跑的檔案重新合併，放入references資料夾中
for data in result_data_list:
    if ('page' in data) and ('error' in data) and ('newtaipei' in data):
        with open(f'result-data/{data}', 'r', encoding='utf-8') as f:
            page_error_data = json.loads(f.read())
        rerun_newtaipei_page_error_list += page_error_data
        newtaipei_count_page_error += 1

    if ('coordinate' in data) and ('error' in data) and ('newtaipei' in data):
        with open(f'result-data/{data}', 'r', encoding='utf-8') as f:
            coordinate_error_data = json.loads(f.read())
        rerun_newtaipei_coordinate_error_list += coordinate_error_data
        newtaipei_count_coordinate_error += 1

    if ('page' in data) and ('error' in data) and ('newtaipei' not in data):
        with open(f'result-data/{data}', 'r', encoding='utf-8') as f:
            page_error_data = json.loads(f.read())
        rerun_taipei_page_error_list += page_error_data
        taipei_count_page_error += 1
            

    if ('coordinate' in data) and ('error' in data) and ('newtaipei' not in data):
        with open(f'result-data/{data}', 'r', encoding='utf-8') as f:
            coordinate_error_data = json.loads(f.read())
        rerun_taipei_coordinate_error_list += coordinate_error_data
        taipei_count_coordinate_error += 1



if rerun_newtaipei_page_error_list != []:
    with open(f'references/rerun_newtaipei_page_error_list.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(rerun_newtaipei_page_error_list))
    print(f'新北市_page_重跑清單合併{newtaipei_count_page_error}個檔案，共{len(rerun_newtaipei_page_error_list)}筆資料須重跑，檔案寫在references資料夾中，檔名為 rerun_newtaipei_page_error_list.json')
    

if rerun_newtaipei_coordinate_error_list != []:
    with open(f'references/rerun_newtaipei_coordinate_error_list.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(rerun_newtaipei_coordinate_error_list))
    print(f'新北市_coordinate_重跑清單合併{newtaipei_count_coordinate_error}個檔案，共{len(rerun_newtaipei_coordinate_error_list)}筆資料須重跑，檔案寫在references資料夾中，檔名為 rerun_newtaipei_coordinate_error_list.json')

if rerun_taipei_page_error_list != []:
    with open(f'references/rerun_taipei_page_error_list.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(rerun_taipei_page_error_list))
    print(f'台北市_page_重跑清單合併{taipei_count_page_error}個檔案，共{len(rerun_taipei_page_error_list)}筆資料須重跑，檔案寫在references資料夾中，檔名為 rerun_taipei_page_error_list.json')

if rerun_taipei_coordinate_error_list != []:
    with open(f'references/rerun_taipei_coordinate_error_list.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(rerun_taipei_coordinate_error_list))
    print(f'台北市_coordinate_重跑清單合併{taipei_count_coordinate_error}個檔案，共{len(rerun_taipei_coordinate_error_list)}筆資料須重跑，檔案寫在references資料夾中，檔名為 rerun_taipei_coordinate_error_list.json')

