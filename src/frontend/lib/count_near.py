import json
import pandas as pd 
from geopy.distance import geodesic
import lib.corcoordinate_caculate as cc

def count_near(Latitude, Longitude, type_obj, dist=300):
    house = (Latitude, Longitude)
    near_fac = pd.read_csv("data/near_fac_corrected.csv")
    cc.convert_lat_lon_to_tuple(near_fac, "Latitude", "Longitude")
    type_list = list(near_fac["類型"].unique())

    # print(type_list)

    count = 0
    min_dist = 1000000000000
    selected_data = near_fac[near_fac['類型'] == type_obj]
    if type_obj  not in type_list:
        return '沒有此類別的資料'
    else:
        for hs in selected_data["cor"]:
            # print(hs)
            distance = geodesic(house, hs).meters
            min_dist = min(distance, min_dist)
            if distance <= int(dist):
                count += 1
        # print(min_dist)
    # print(f"此物件在{dist}公尺內有{count}間{typeobj}") 
    result={}
    result["target_distance"] = int(dist)
    result[f"count_of_{type_obj}_in_{dist}m"] = int(count)
    result[f"minimun_distance_of_{type_obj}"] = int(round(min_dist, 1))
    
    result = json.dumps(result, ensure_ascii=False)
    return result
    # return f"此物件在{dist}公尺內有{count}間{type_obj},最近的{type_obj}距離{min_dist:.1f}公尺"

def get_near_list(row):
    '''
    輸入df行抓值，輸出比鄰敘述
    '''
    house = (row[Latitude], row[Longitude])
    near_fac = pd.read_csv("data/near_fac_corrected.csv")
    cc.convert_lat_lon_to_tuple(near_fac, "Latitude", "Longitude")
    type_list = list(near_fac["類型"].unique())
    dist = {
        '公共活動空間':250,
        '交流道出入口':1000,
        '捷運出口':250,
        '宗教場所':250, 
        '消防單位':500, 
        '商圈':500, 
        '圖書館':250, 
        '學校':250, 
        '藝文':250, 
        '醫院':500, 
        '加油站':250, 
        '幼兒園':250, 
        '托兒所':250, 
        '法院_檢察署':500, 
        '便利商店':150, 
        '發電廠':2000, 
        '清潔單位':500, 
        '焚化廠':2500, 
        '銀行':500, 
        '殯儀館':1500, 
        '警局':500, 
        '療養院':500, 
        '診所':250, 
        '藥局':250, 
        '醫療設施':250,
    }

    result = []
    for typeobj in type_list:    
        selected_data = near_fac[near_fac['類型'] == typeobj]
        for hs in selected_data["cor"]:
                distance = geodesic(house, hs).meters
                if distance <= int(dist[typeobj]):
                    result.append(f"近{typeobj}")
                    break

    return result


if __name__ == "__main__":
    Latitude = '25.0533099'
    Longitude = '121.616095'
    typeobj = '便利商店'
    dist = '100' # m
    print((count_near(Latitude, Longitude, typeobj, dist)))