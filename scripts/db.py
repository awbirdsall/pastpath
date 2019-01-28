#!/usr/bin/env python

'''db.py : interact with postresql database
'''

import config as cfg
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd

INPUT_CSV = '../data/190121-all-markers-with-cats.csv'
INPUT_SIM = "../data/190123-similarity-matrix-dc.csv"
INPUT_ENT_1 = "../data/190123-dc-named-entities-counts-per-marker-pt1.csv"
INPUT_ENT_2 = "../data/190123-dc-named-entities-counts-per-marker-pt2.csv"
OUTPUT_TABLE = 'hmdb_data_table'
OUTPUT_SIM_TABLE = 'similarities_data_table'
OUTPUT_ENT_TABLE_1 = 'entities_data_table_1'
OUTPUT_ENT_TABLE_2 = 'entities_data_table_2'
 

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

def add_df_hmdb_data(input_csv, output_table, engine, input_sim_csv=INPUT_SIM):
    # add HMDB data array
    df = pd.read_csv(input_csv).query("cty=='washington_dc'")
    # also need marker_ids for which similarity metric exists
    sim_marker_ids = pd.read_csv(input_csv, index_col=0).index.values

    # limit marker table to markers for which similarity metric exists
    df_to_sql = df[df['marker_id'].isin(sim_marker_ids)]

    print('adding hmdb data as {}'.format(output_table))
    df_to_sql.to_sql(output_table, engine, if_exists='replace', index=False)
    return None

def add_df_ent_two_parts(input_csv_1, input_csv_2, output_table_1,
        output_table_2, engine):
    df_ent_1 = pd.read_csv(INPUT_ENT_1)

    print('adding first half of entity data as {}'.format(output_table_1))
    df_ent_1.to_sql(OUTPUT_ENT_TABLE_1, engine, if_exists='replace',
            index=False)

    df_ent_2 = pd.read_csv(INPUT_ENT_2)

    print('adding second half of entity data as {}'.format(output_table_2))
    df_ent_2.to_sql(OUTPUT_ENT_TABLE_2, engine, if_exists='replace',
            index=False)

    return None

if __name__ == '__main__':
    print('running db.py from command line')
    engine = create_connection()
    add_df_sim(INPUT_SIM, OUTPUT_SIM_TABLE, engine)
    add_df_hmdb_data(INPUT_CSV, OUTPUT_TABLE, engine, INPUT_SIM)
    add_df_ent_two_parts(INPUT_ENT_1, INPUT_ENT_2, OUTPUT_ENT_TABLE_1,
        OUTPUT_ENT_TABLE_2, engine)
    print('db.py: done.')
