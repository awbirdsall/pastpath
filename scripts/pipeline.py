#!/usr/bin/env python

'''pipeline.py : end-to-end set of processing steps to work up and analyze data
for app deployment

"This really would make more sense as a makefile," he realizes.
'''

import argparse
import ner
import collect_features as cf
import process_features as pf
import db

# SVD and k means parameters, used in process_features
N_COMPONENTS = 100
N_CLUSTERS = 10

# database (dev or production)
DB_LOC = 'dev'
# DB_LOC = 'production'

## preexisting files
# processed CSV with marker text and hmdb category labels
MARKER_CSV_IN = '../data/190206-all-markers-with-cats-credits.csv'

## files created/passed along in pipeline
# recognized entities
NER_CSV = '../data/190206-ner.csv'
# counts of all features, per marker
FEAT_CSV = '../data/190206-feat-count.csv'
# marker filtered to only include markers listed in FEAT_CSV
MARKER_CSV_OUT = "../data/190206-marker-out.csv"
# like FEAT_CSV, but without filtering for number of markers or features
FEAT_FULL_CSV = '../data/190206-feat-full-count.csv'
# similarity matrix, with index_col = marker_id and columns=marker_id
SIM_CSV = '../data/190206-sim-tfidf.csv'
# labels for markers in MARKER_CSV_OUT
CLUST_CSV = '../data/190206-km-labels.csv'
CLUST_TOP_TERMS_CSV = '../data/190206-km-top-terms.csv'

## SQL DB table names
OUTPUT_TABLE = 'hmdb_data_table'
OUTPUT_SIM_TABLE = 'similarities_data_table'
OUTPUT_ENT_TABLE_1 = 'entities_data_table_1'
OUTPUT_ENT_TABLE_2 = 'entities_data_table_2'
OUTPUT_CLUST_TABLE = 'clust_table'

# other pipeline file dependencies hard coded into individual steps:
# - decades
# - wiki text

def run_pipeline(ner_step=True, cf_step=True, pf_step=True, db_step=True):
    if ner_step:
        print("pipeline.py: running ner")
        ner.ne_pipeline(NER_CSV, MARKER_CSV_IN)

    if cf_step:
        print("pipeline.py: running collect_features")
        cf.feature_pipeline(NER_CSV, FEAT_CSV, MARKER_CSV_OUT, FEAT_FULL_CSV)

    if pf_step:
        print("pipeline.py: running process_features.calc_sim_matrix()")
        pf.calc_sim_matrix(FEAT_CSV, SIM_CSV)

        print("pipeline.py: running process_features.calc_clusters()")
        pf.calc_clusters(FEAT_CSV, CLUST_CSV, CLUST_TOP_TERMS_CSV,
                N_COMPONENTS, N_CLUSTERS)

    if db_step:
        # split features into two parts
        print("pipeline.py: running db.add_to_sql_pipeline()")
        db.add_to_sql_pipeline(DB_LOC, SIM_CSV, OUTPUT_SIM_TABLE,
                        MARKER_CSV_OUT, OUTPUT_TABLE,
                        FEAT_CSV, OUTPUT_ENT_TABLE_1,
                        OUTPUT_ENT_TABLE_2,
                        CLUST_CSV, OUTPUT_CLUST_TABLE)

    return None

if __name__ == '__main__':
    print('running pipeline.py from command line')

    parser = argparse.ArgumentParser(description='run pastpath pipeline')
    parser.add_argument('--ner', action='store_true')
    parser.add_argument('--cf', action='store_true')
    parser.add_argument('--pf', action='store_true')
    parser.add_argument('--db', action='store_true')
    args = parser.parse_args()
    run_pipeline(args.ner, args.cf, args.pf, args.db)
