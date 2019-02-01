#!/usr/bin/env python

'''validation.py : check whether similarity predictions are reasonable.
'''

import numpy as np
import pandas as pd
import random
from sys import argv

MARKER_CSV = '../data/190130-df-marker.csv'
FEAT_CSV = "../data/190130-df-feature-counts.csv"
SIM_CSV = "../data/190130-df-sim-tfidf.csv"

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

def marker_title_from_id(marker_id, marker_csv):
    df = pd.read_csv(marker_csv).query("cty=='washington_dc'")
    marker = df[df.marker_id==marker_id]
    return marker.title.values[0]

def marker_text_from_id(marker_id, marker_csv):
    df = pd.read_csv(marker_csv).query("cty=='washington_dc'")
    marker = df[df.marker_id==marker_id]
    return marker.text_clean.values[0]

def marker_feats_from_id(marker_id, feat_csv):
    df_feat = pd.read_csv(feat_csv, index_col='marker_id')
    marker_has_feat = df_feat.loc[marker_id]
    marker_feats = df_feat.columns[marker_has_feat].tolist()
    return marker_feats

def short_text_report(top_n_id, top_n_sims):
    primary_id = top_n_id[0]
    similar_ids = top_n_id[1:]
    print("primary: {} (#{})".format(marker_title_from_id(primary_id, MARKER_CSV),
                                     primary_id))
    print("similar:")
    for similar_id in similar_ids:
        print("{} (#{})".format(marker_title_from_id(similar_id, MARKER_CSV),
                                     similar_id))
    print("scores: {}".format(top_n_sims))

    return None

def detailed_text_report(top_n_id, top_n_sims):
    primary_id = top_n_id[0]
    similar_ids = top_n_id[1:]
    print("primary marker id {}".format(primary_id))
    print("top similar ids: {}".format(similar_ids))
    print("similarity scores: {}".format(top_n_sims))
    print('+++')
    print('FEAT COMPARISON')
    print('primary m{} feats:'.format(primary_id))
    print(marker_feats_from_id(primary_id, FEAT_CSV))
    for mid in similar_ids:
        print('---')
        print("m{} feats: {}".format(mid, marker_feats_from_id(mid, FEAT_CSV)))
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
    print('MARKER_CSV = {}'.format(MARKER_CSV))
    print('FEAT_CSV = {}'.format(FEAT_CSV))
    print('SIM_CSV = {}'.format(SIM_CSV))

    print("======")
    print("RANDOM MARKER")
    print("======")
    top_n_id, top_n_sims = top_similarities_random(MARKER_CSV, SIM_CSV, n=10)
    short_text_report(top_n_id, top_n_sims)
    detailed_text_report(top_n_id, top_n_sims)

    print("======")
    print("BARTHOLDI FOUNTAIN MARKER")
    print("======")
    top_n_id, top_n_sims = top_similar_marker_id(110441, SIM_CSV, n=10)
    short_text_report(top_n_id, top_n_sims)

    print("=====")
    print("FREDERICK DOUGLAS MARKER")
    print("=====")
    top_n_id, top_n_sims = top_similar_marker_id(40846, SIM_CSV, n=10)
    short_text_report(top_n_id, top_n_sims)

    print("=====")
    print("MARY CHURCH TERRELL MARKER")
    print("=====")
    top_n_id, top_n_sims = top_similar_marker_id(100863, SIM_CSV, n=10)
    short_text_report(top_n_id, top_n_sims)

    # pseudocode for validation with clusters:
    # for cluster in clusters:
    #   choose (random?) marker near cluster centroid
    #   find similar markers
    #   report cluster features and markers
