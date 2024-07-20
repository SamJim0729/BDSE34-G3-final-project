import os

import pandas as pd


def combine_file_under_dir(target_dir: str, output_file: str):
    """資料夾底下的檔案必須需都有相同的column，作用像是沿著axis=0把所有資料表concat起來


    target_dir (str): 目錄最後面的斜線(/)要記得加 example: ./test_dir/
    output_file (str): 輸出合併後的檔案名稱
    """

    # 用來暫存所有讀進來的檔案df
    tmp_dataframes_list = []

    # 指定要查詢的路徑
    # 列出指定路徑底下所有檔案(包含資料夾)
    allFileList = os.listdir(target_dir)

    # 把資料夾底下全部檔案寫成"一個"完整的大檔案
    for file in allFileList:
        tmp_df = pd.read_csv(target_dir + file)
        tmp_dataframes_list.append(tmp_df)  # 把讀進來的所有dfs先放到list當中
        # tmp_df.to_csv(path_or_buf=output_file, mode="a", encoding="utf-8", index=False)

    # 將所有CSV檔案讀取成DataFrame並存入列表，然後使用 pd.concat 將這些DataFrame合併成一個(就不會有欄位值重複寫入的問題)，concat本來就是丟一個list進去，所以可以concat多個df
    combined_df = pd.concat(tmp_dataframes_list, axis=0, ignore_index=True)  

    # 寫入檔案
    combined_df.to_csv(path_or_buf=output_file, mode="a", encoding="utf-8", index=False)


# 目前用在房價資料集可能會有問題
def remove_duplicated(csv_file, column: str):
    """
    column (str): 選擇用以判斷rows是否重複的欄位名稱
    """

    db = pd.read_csv(csv_file, encoding="utf-8")
    # 找出所有唯一的值
    unique_set = set()
    for index, value in enumerate(db[column]):
        unique_set.add(value)
    print(f"There are {len(unique_set)} unique rows.")

    # 寫成list格式，方便後續操作
    sort_list = []
    for i in unique_set:
        sort_list.append(i)

    # 去除df中重複的row
    count_drop_rows = 0
    for index, value in enumerate(db[column]):
        try:  # sort_list是一個已經去重複的清單
            sort_list.index(
                value
            )  # 迭代dataframe，若當中有這個值(意思是這是第一次出現) >>若是第二次出現，因為list當中已經沒有這個值了，會報ValueError
            sort_list.remove(value)  # 就把這個值從list當中移除
        except ValueError:  # 抓這個Error
            print(index, value)
            db.drop(
                index, inplace=True
            )  # 然後把這個row從dataframe當中刪除 ，drop預設為axis=0丟row
            count_drop_rows += 1
    print(f"There are {count_drop_rows} duplicated rows, have been drop")

    # 還沒寫檔喔


if __name__ == "__main__":

    ##### 測試 #####
    combine_file_under_dir("C:/Users/student/Desktop/test_dir/", "./test_file.csv")

    # 用在房價資料有點問題
    # remove_duplicated("./test_file.csv", "address")
