'''histmark.markers : functions for historic marker calculations
'''
import math
import numpy as np
import sys

def get_closest_starting_markers(lat, lon, df, n):
    print(df.shape)
    distances = np.array([distance((lat,lon), (lat2, lon2))
        for (lat2, lon2) in zip(df.lat, df.lon)])
    return df.iloc[distances.argsort()[:n]]

# Haversine formula example in Python
# Author: Wayne Dyck
def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

def get_top_locations_close(marker_id, df_similarities, n, df, radius):
    lat, lon = df.query("marker_id=={}".format(marker_id)).loc[:, ['lat','lon']].values[0]
    # calculate distances and filter df_similarities df
    distances = np.array([distance((lat,lon), (lat2, lon2)) for (lat2, lon2) in zip(df.lat, df.lon)])
    close_marker_ids = df.iloc[np.where(distances<radius)]['marker_id'].values
    # print(type(close_marker_ids.astype(str)))
    # close_marker_ids = np.array([114658, 113216])
    print(df_similarities.head())
    # can only return len(close_marker_ids) worth of points
    if len(close_marker_ids)<n:
        n = len(close_marker_ids)

    similarities_filtered = df_similarities[close_marker_ids.astype(str)]
    
    interest_row = similarities_filtered.loc[marker_id]
    # *index* of top n
    # (last n in ascending order, then reversed)
    top_n_idx = interest_row.values.argsort()[-n:][::-1]
    # look up marker_id values
    top_n_id = similarities_filtered.iloc[:,top_n_idx].columns.values.astype(int)
    return top_n_id
