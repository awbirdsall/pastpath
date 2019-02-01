#!/usr/bin/env python

'''db.py : interact with postresql database

Main task: take INPUT_CSV of marker data, INPUT_SIM of similarity matrix, and
INPUT_ENT_1 and INPUT_ENT_2 of named entity counts per marker, and write them
as the appropriate tables in cfg.postgres['DB_NAME'].
'''

import config as cfg
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd

INPUT_CSV = '../data/190130-df-marker.csv'
INPUT_SIM = "../data/190130-df-sim-tfidf.csv"
INPUT_ENT = "../data/190130-df-feature-counts.csv"
INPUT_CLUST = '../data/190131-km-labels.csv'
OUTPUT_TABLE = 'hmdb_data_table'
OUTPUT_SIM_TABLE = 'similarities_data_table'
OUTPUT_ENT_TABLE_1 = 'entities_data_table_1'
OUTPUT_ENT_TABLE_2 = 'entities_data_table_2'
OUTPUT_CLUST_TABLE = 'clust_table'

def create_connection():
    # Create connection engine to postgres db
    engine_template = 'postgresql://{}:{}@{}:{}/{}'
    engine = create_engine(engine_template.format(cfg.postgres['USER'],
                                                  cfg.postgres['KEY'],
                                                  cfg.postgres['HOST'],
                                                  cfg.postgres['PORT'],
                                                  cfg.postgres['DB_NAME']))
    if not database_exists(engine.url):
        create_database(engine.url)
    print("create_connection: database engine url {}".format(engine.url))
    return engine

def add_df_sim(input_csv, output_table, engine):
    # add similarity matrix
    # downcasted to float32 to pack in (otherwise row too wide)
    df_sim = pd.read_csv(input_csv, index_col=0).astype(np.float32)
    print('adding similarity matrix as {}'.format(output_table))
    df_sim.to_sql(output_table, engine, if_exists='replace')
    return None

def add_df_hmdb_data(input_csv, output_table, engine, cluster_csv):
    # add HMDB data array. already filtered down to what is useful
    df = pd.read_csv(input_csv)
    # ugly hack to add cluster_csv column here...
    df_cluster = pd.read_csv(cluster_csv)
    df_total = pd.merge(df, df_cluster, on="marker_id", how="left")
    print('adding hmdb data as {}'.format(output_table))
    df_total.to_sql(output_table, engine, if_exists='replace', index=False)
    return None

def add_df_ent_two_parts(input_csv, output_table_1, output_table_2, engine):
    df = pd.read_csv(input_csv, index_col='marker_id')
    # split input into two parts because too many columns...
    num_cols = len(df.columns)
    halfway_col = num_cols//2

    df_ent_1 = df.iloc[:,:halfway_col]
    df_ent_2 = df.iloc[:,halfway_col:]

    print('adding first half of entity data as {}'.format(output_table_1))
    df_ent_1.to_sql(OUTPUT_ENT_TABLE_1, engine, if_exists='replace',
            index=True)

    print('adding second half of entity data as {}'.format(output_table_2))
    df_ent_2.to_sql(OUTPUT_ENT_TABLE_2, engine, if_exists='replace',
            index=True)

    return None

def add_df_clust(input_csv, output_table, engine):
    # add clusters
    df_clust = pd.read_csv(input_csv, index_col=0)
    print('adding cluster df as {}'.format(output_table))
    df_clust.to_sql(output_table, engine, if_exists='replace')
    return None

def add_to_sql_pipeline(input_sim=INPUT_SIM, output_sim_table=OUTPUT_SIM_TABLE,
        input_csv=INPUT_CSV, output_table=OUTPUT_TABLE, input_ent=INPUT_ENT,
        output_ent_table_1=OUTPUT_ENT_TABLE_1,
        output_ent_table_2=OUTPUT_ENT_TABLE_2, input_clust=INPUT_CLUST,
        output_clust_table=OUTPUT_CLUST_TABLE):
    engine = create_connection()
    add_df_sim(input_sim, output_sim_table, engine)
    add_df_hmdb_data(input_csv, output_table, engine, input_clust)
    add_df_ent_two_parts(input_ent, output_ent_table_1, output_ent_table_2,
            engine)
    add_df_clust(input_clust, output_clust_table, engine)
    return None

if __name__ == '__main__':
    print('running db.py from command line')
    add_to_sql_pipeline(INPUT_SIM, OUTPUT_SIM_TABLE,
                        INPUT_CSV, OUTPUT_TABLE,
                        INPUT_ENT, OUTPUT_ENT_TABLE_1,
                        OUTPUT_ENT_TABLE_2,
                        INPUT_CLUST, OUTPUT_CLUST_TABLE)
    print('db.py: done.')
