from flask import render_template, request
from histmark import app
from histmark.markers import get_closest_starting_markers, get_top_locations_close
from histmark.route import calc_distance_matrix, optimal_route_from_matrix, directions_route_duration
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2

# connect to postgres
db = create_engine('postgres://%s%s/%s'%(app.config['SQL_USER'],
                                         app.config['HOST'],
                                         app.config['DB_NAME']))
con = psycopg2.connect(database=app.config['DB_NAME'],
        user=app.config['SQL_USER'],
        host=app.config['HOST'],
        password=app.config['SQL_KEY'])

@app.route('/')
@app.route('/index')
@app.route('/input_loc')
def input_loc():
    return render_template("input.html")

@app.route('/choose_start')
def choose_start():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    # get entire dc places dataframe
    query = "SELECT marker_id, title, lat, lon, text, categories, url FROM hmdb_data_table WHERE cty='washington_dc';"
    df_markers = pd.read_sql_query(query, con)
    # calculate N closest markers
    # returns rows of df_markers
    markers = get_closest_starting_markers(lat, lon, df_markers, 7)
    return render_template("choose_start.html", markers=markers)

@app.route('/output')
def get_route():
    start_marker = int(request.args.get('start_marker'))
    radius = float(request.args.get("radius"))*1.61 # convert miles to km

    # get places dataframe
    markers_query = "SELECT marker_id, title, lat, lon, text, categories, url FROM hmdb_data_table WHERE cty='washington_dc';"
    df_markers = pd.read_sql_query(markers_query, con)

    # get similarities dataframe
    sim_query = "SELECT * FROM similarities_data_table"
    df_similarities = pd.read_sql_query(sim_query, con, index_col='marker_id')

    top_n_id = get_top_locations_close(start_marker, df_similarities, 7,
            df_markers, radius)
    # routing function requires having the start/end point first.
    # first entry in top_n_id should always start_marker since it has highest
    # similarity with itself
    # start with first marker and then add the rest
    markers = df_markers[df_markers.marker_id==top_n_id[0]]
    markers = markers.append(df_markers[df_markers.marker_id.isin(top_n_id[1:])])

    map_center = [markers.lat.mean(), markers.lon.mean()]
    marker_coords = [(x.lon, x.lat) for x in markers.itertuples()]

    marker_names = [x.text[:30] for x in markers.itertuples()]

    # solve TSP
    dist_matrix = calc_distance_matrix(marker_coords)
    optimal_coords, marker_order, route_str = optimal_route_from_matrix(marker_coords,
        marker_names, dist_matrix, start=0)
    optimal_route, optimal_duration = directions_route_duration(optimal_coords)
    optimal_duration = int(optimal_duration)
    # reorder marker order to reflect walking tour order
    markers = markers.reset_index().reindex(marker_order)

    # get entities (2 tables due to number of columns)
    marker_ids_str = ", ".join(markers.marker_id.values.astype(str))
    ent_query_1 = "SELECT * FROM entities_data_table_1 WHERE marker_id IN ({})".format(marker_ids_str)
    df_ent_1 = pd.read_sql_query(ent_query_1, con, index_col='marker_id')
    ent_query_2 = "SELECT * FROM entities_data_table_2 WHERE marker_id IN ({})".format(marker_ids_str)
    df_ent_2 = pd.read_sql_query(ent_query_2, con, index_col='marker_id')
    df_ent = df_ent_1.merge(df_ent_2, how='outer', on='marker_id')
    marker_ents = []
    for marker_id in markers.marker_id.values:
        marker_ents.append(df_ent.columns[df_ent.loc[marker_id]!=0].tolist())
    markers['marker_ents'] = marker_ents

    # decode route to geojson-ready form
    route_polylines_flip = optimal_route['features'][0]['geometry']['coordinates']
    route_polylines = [[y,x] for [x,y] in route_polylines_flip]

    return render_template("output.html", markers=markers,
            map_center=map_center, route_polylines=route_polylines,
            marker_order=marker_order, route_str=route_str,
            optimal_duration=optimal_duration)
