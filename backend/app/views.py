import ast

from fastapi import APIRouter, Request, Query
from fastapi.staticfiles import StaticFiles
import pandas as pd
import psycopg2

from app.markers import get_closest_starting_markers, get_top_locations_close
from app.models import StartChoice, Marker, NearbyOptions, Route, RouteRequest
from app.route import get_distance_matrix_response, optimal_route_from_matrix, directions_route_duration
from app.settings import get_app_settings, get_instance_settings

router = APIRouter()

# connect to postgres
con = psycopg2.connect(
        database=get_app_settings().db_name,
        user=get_instance_settings().sql_user,
        host=get_app_settings().host,
        port=get_app_settings().port,
        password=get_instance_settings().sql_key
        )


@router.post('/choose_start')
async def choose_start(start_choice: StartChoice) -> NearbyOptions:
    # start is limited by choice of clusters and distance from location
    clusters = start_choice.cluster
    print("clusters: {}".format(clusters))

    # get places in selected clusters
    clusters_str = ", ".join(clusters)
    query = "SELECT marker_id, title, lat, lon, text, categories, url, text_clean, images FROM hmdb_data_table WHERE km_label in ({});".format(clusters_str)
    print("choose_start query: {}".format(query))
    df_markers = pd.read_sql_query(query, con)
    print(df_markers['text_clean'].head())

    # calculate N closest markers
    # returns rows of df_markers
    markers = get_closest_starting_markers(start_choice.lat, start_choice.lon,
            df_markers, 7).copy()
    print("choose_start(): markers")
    print(markers)
    print(markers.columns)
    print(markers['text_clean'].head())

    # add img_src
    img_urls = [x[0] for x in markers['images'].apply(ast.literal_eval)]
    img_ids = [x.split("/")[-1][5:-5].zfill(6) for x in img_urls]
    marker_id_strs = [str(x).zfill(6) for x in markers['marker_id']]
    img_srcs = ["static/img/{}_{}_small.jpg".format(x,y) for (x,y) in zip(marker_id_strs, img_ids)]
    markers['img_src'] = img_srcs
    map_center = [markers.lat.mean(), markers.lon.mean()]

    # convert dataframe to marker objects for json response
    marker_objs = [Marker(**marker) for marker in markers.to_dict("records")]
    print(f"creating nearby_options with {marker_objs}, {map_center}")
    nearby_options = NearbyOptions(
        markers=marker_objs,
        map_center=map_center
    )
    return nearby_options


@router.post('/output')
async def get_route(route_request: RouteRequest) -> Route:
    radius = route_request.radius * 1.61 # convert miles to km

    # get places dataframe
    markers_query = "SELECT marker_id, title, lat, lon, text, text_clean, images, categories, url FROM hmdb_data_table WHERE cty='washington_dc';"
    df_markers = pd.read_sql_query(markers_query, con)
    print("get_route df_markers.head():")
    print(df_markers.head())

    # get similarities dataframe
    sim_query = "SELECT * FROM similarities_data_table"
    df_similarities = pd.read_sql_query(sim_query, con, index_col='marker_id')
    print("get_route df_similarities.head():")
    print(df_similarities.head())

    top_n_id = get_top_locations_close(route_request.start_marker, df_similarities, 7,
            df_markers, radius)
    print("get_route top_n_id:")
    print(top_n_id)
    # routing function requires having the start/end point first.
    # first entry in top_n_id should always start_marker since it has highest
    # similarity with itself
    # start with first marker and then add the rest
    markers = df_markers[df_markers.marker_id==top_n_id[0]]
    markers = markers.append(df_markers[df_markers.marker_id.isin(top_n_id[1:])])

    map_center = [markers.lat.mean(), markers.lon.mean()]
    marker_coords = [(x.lon, x.lat) for x in markers.itertuples()]
    print(marker_coords)

    marker_names = [x.text[:30] for x in markers.itertuples()]

    # solve TSP
    dist_matrix_response = get_distance_matrix_response(marker_coords)
    dist_matrix = dist_matrix_response["durations"]
    optimal_coords, marker_order, _ = optimal_route_from_matrix(marker_coords,
        marker_names, dist_matrix, start=0)
    optimal_route, optimal_duration = directions_route_duration(optimal_coords)
    optimal_duration = int(optimal_duration)
    # reorder marker order to reflect walking tour order
    markers = markers.reset_index().reindex(marker_order)
    route_str = " ⇨ ".join(markers.title)

    # get entities (2 tables due to number of columns)
    marker_ids_str = ", ".join(markers.marker_id.values.astype(str))
    ent_query_1 = "SELECT * FROM entities_data_table_1 WHERE marker_id IN ({})".format(marker_ids_str)
    df_ent_1 = pd.read_sql_query(ent_query_1, con, index_col='marker_id')
    ent_query_2 = "SELECT * FROM entities_data_table_2 WHERE marker_id IN ({})".format(marker_ids_str)
    df_ent_2 = pd.read_sql_query(ent_query_2, con, index_col='marker_id')
    df_ent = df_ent_1.merge(df_ent_2, how='outer', on='marker_id')
    marker_ents = []
    for marker_id in markers.marker_id.values:
        raw_one_marker_ents = df_ent.columns[df_ent.loc[marker_id]!=0].tolist()
        one_marker_ents = [x.split("_")[0].capitalize() for x in raw_one_marker_ents]
        marker_ents.append(one_marker_ents)
    markers['marker_ents'] = marker_ents

    # decode route to geojson-ready form
    route_polylines_flip = optimal_route['features'][0]['geometry']['coordinates']
    route_polylines = [[y,x] for [x,y] in route_polylines_flip]

    # add img_src
    img_urls = [x[0] for x in markers['images'].apply(ast.literal_eval)]
    img_ids = [x.split("/")[-1][5:-5].zfill(6) for x in img_urls]
    marker_id_strs = [str(x).zfill(6) for x in markers['marker_id']]
    img_srcs = ["static/img/{}_{}_small.jpg".format(x,y) for (x,y) in zip(marker_id_strs, img_ids)]
    markers['img_src'] = img_srcs

    marker_objs = [Marker(**marker) for marker in markers.to_dict("records")]
    route = Route(
        markers=marker_objs,
        map_center=map_center,
        route_polylines=route_polylines,
        marker_order=marker_order,
        route_str=route_str,
        optimal_duration=optimal_duration
    )
    return route
