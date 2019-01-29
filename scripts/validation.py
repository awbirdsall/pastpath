#!/usr/bin/env python

'''validation.py : check whether similarity predictions are reasonable.
'''

import numpy as np
import pandas as pd
import random

MARKER_CSV = '../data/190121-all-markers-with-cats.csv'
ENT_CSV = "../data/190128-df-ent.csv"
SIM_TFIDF_CSV = "../data/190128-df-sim-tfidf.csv"
SIM_CSV = "../data/190128-df-sim.csv"

def top_similar_marker_id(marker_id, sim_csv, n=10):
    df_sim = pd.read_csv(sim_csv, index_col='marker_id')
    interest_row = df_sim.loc[marker_id]
    # top similarity scores
    top_n_sims = np.sort(interest_row)[-n:][::-1]
    # *idx* of top n
    top_n_idx = interest_row.argsort()[-n:][::-1]
    # look up marker_id values
    top_n_id = df_sim.iloc[:,top_n_idx].columns.values.astype(int)
    return top_n_id, top_n_sims

def top_similarities_random(marker_csv, sim_csv, n=10):
    df = pd.read_csv(marker_csv).query("cty=='washington_dc'")
    random_id = random.choice(df.marker_id.unique())
    return top_similar_marker_id(random_id, sim_csv, n)

def marker_text_from_id(marker_id, marker_csv):
    df = pd.read_csv(marker_csv).query("cty=='washington_dc'")
    marker = df[df.marker_id==marker_id]
    return marker.text.values[0]

def marker_ents_from_id(marker_id, ent_csv):
    df_ent = pd.read_csv(ent_csv)
    marker = df_ent[df_ent.marker_id==marker_id]
    marker_ents = marker.text.tolist()
    return marker_ents

def marker_cats_from_id(marker_id, marker_csv):
    df = pd.read_csv(marker_csv).query("cty=='washington_dc'")
    marker = df[df.marker_id==marker_id]
    return marker.categories.values[0]

def detailed_text_report(top_n_id, top_n_sims):
    primary_id = top_n_id[0]
    similar_ids = top_n_id[1:]
    print("primary marker id {}".format(primary_id))
    print("top similar ids: {}".format(similar_ids))
    print("similarity scores: {}".format(top_n_sims))
    print('+++')
    print('ENT COMPARISON')
    print('primary m{} ents:'.format(primary_id))
    print(marker_ents_from_id(primary_id, ENT_CSV))
    for mid in similar_ids:
        print('---')
        print("m{} entities: {}".format(mid, marker_ents_from_id(mid, ENT_CSV)))
    print('+++')
    print("CAT COMPARISON")
    print('primary m{} cats:'.format(primary_id))
    print(marker_cats_from_id(primary_id, MARKER_CSV))
    for mid in similar_ids:
        print('---')
        print('m{} categories: {}'.format(mid, marker_cats_from_id(mid, MARKER_CSV)))
    print('+++')
    print("RAW TEXT COMPARISON")
    print("primary m{} text: {}".format(primary_id, marker_text_from_id(primary_id, MARKER_CSV)))
    print('---')
    for mid in similar_ids:
        print("m{} text: {}".format(mid, marker_text_from_id(mid, MARKER_CSV)))
        print('---')
    return None

if __name__ == '__main__':
    print("running validation.py from command line")
    print("======")
    print("RANDOM MARKER")
    print("======")
    top_n_id, top_n_sims = top_similarities_random(MARKER_CSV, SIM_TFIDF_CSV, n=10)
    detailed_text_report(top_n_id, top_n_sims)

    print("======")
    print("BARTHOLDI FOUNTAIN MARKER")
    print("======")
    top_n_id, top_n_sims = top_similar_marker_id(110441, SIM_TFIDF_CSV, n=10)
    detailed_text_report(top_n_id, top_n_sims)
