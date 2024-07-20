# to define function we need to import pandas first
import pandas as pd


def convert_lat_lon_to_tuple(df: pd.DataFrame, lat_c: str, lon_c: str):
    """convert latitude and longitude columns to a tuple form and create a new column "cor" to store it.

    Args:
        df (pd.DataFrame): the dataframe which has latitude and longitude columns
        lat_c (str): latitude column name
        lon_c (str): longitude column name
    """

    listtt = []
    for v in df.loc[:, [lat_c, lon_c]].values:
        listtt.append((v[0], v[1]))
    df["cor"] = listtt


def distance_caculate_and_cat_counts(
    house_df: pd.DataFrame,
    item_df: pd.DataFrame,
    group_name: str,
    categorical_list: list,
):
    """Caculating the distance between each house and items (ex: high_speed_road, MRT etc). You can use categorical_list to set category criteria by circumstances and create each category to columns in house_df. Columns values is the frequency of items counted by criteria.

    *** Each dataframe need to use convert_lat_lon_to_tuple() first to create "cor" column.

    Args:
        house_df (pd.DataFrame): house dataframe which is contain "cor" column.
        item_df (pd.DataFrame): other facilities dataframe (ex: high_speed_road, MRT etc) which is contain "cor" column.
        group_name (str): facility name (to create columns name).
        categorical_list (list): each element in the list is a number which means under how many meters. List is used to set category criteria (ex: [1000, 3000, 5000], it means under 1000m, 3000m, 5000m )
    """

    # otherwise it is better to import module when we need to use it
    from geopy.distance import geodesic

    # we need a number ascending sorted list
    categorical_list.sort()

    for index, house in enumerate(house_df["cor"]):

        # use categorical_list to create dictionary, and initialize it each time
        counter_dict = {}
        for cat in categorical_list:
            counter_dict[cat] = 0

        # create dictinoary key list (each key is a certain criteria) in order to determine distance is belonged to which interval
        key_list = []
        for num in counter_dict:
            key_list.append(num)

        for hs in item_df["cor"]:
            distance = geodesic(house, hs).meters
            for cp in key_list:
                if distance < cp:
                    counter_dict[cp] += 1
                    break  # using break >> interval, if not >> accumulation

        # each house cor finished and then to assign value to corresponse column
        for cp in key_list:
            house_df.loc[index, f"{group_name}_under_{cp}_m"] = counter_dict[cp]
