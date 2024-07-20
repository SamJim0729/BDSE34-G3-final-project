import os

import pandas as pd


def partition_data(
    main_file_path: str,
    start_row_of_main_file: int,
    end_row_of_main_file: int,
    number_per_file: int,
):
    """將主資料集切分成較少筆數(ex: 100 row per file)的多個子資料集，並放在main_data_piece資料夾底下

    Args:
        main_file_path (str): 房屋主資料集的檔案位置
        start_row_of_main_file (int): 主資料集開始的筆數
        end_row_of_main_file (int): 主資料集的結束的筆數
        number_per_file (int): 每一個子資料集當中要有幾筆資料 (1000筆資料大概就要跑8小時...)
    """

    house_main_df = pd.read_csv(main_file_path)

    folderPath = f"./main_data_piece/"
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)

    # 將每x筆資料切成一個獨立的檔案
    for number_row in range(
        start_row_of_main_file,
        (end_row_of_main_file),
        number_per_file,
    ):
        house_df = house_main_df.iloc[
            number_row : (number_row + number_per_file), :
        ].copy()
        house_df.to_csv(
            f"{folderPath}/main_data_{number_row}_{number_row + number_per_file}.csv"
        )


if __name__ == "__main__":

    # 改成自己房屋主資料集的位置
    file_path = "../../all_data/主資料集/台北市_10101_11303_房價data.csv"

    # 主資料位置, 筆數開始位置, 筆數結束位置, 每個子檔案多少筆
    partition_data(file_path, 0, 8, 1)
