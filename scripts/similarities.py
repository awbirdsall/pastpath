#!/usr/bin/env python

'''similarities.py : similarity calculations
'''

import pandas as pd
from scipy import sparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sys import argv

DF_ENT_CSV = '/home/abirdsall/insight/histmark/data/190128-df-ent.csv'

def load_df_ent():
    df_ent = pd.read_csv(DF_ENT_CSV)
    return df_ent

def entities_to_encode(df_ent):
    # only include entities that appear on at least two plaques
    mrkrs_per_ent = df_ent.groupby('text').marker_id.apply(lambda x: len(x.unique()))
    ents_to_keep = mrkrs_per_ent[mrkrs_per_ent>1].index.values
    df_ent = df_ent[df_ent.text.isin(ents_to_keep)]
    return df_ent

def encode_entities(df_ent):
    # prep df to binary encode each entity as feature
    entity_marker_df = df_ent.loc[:,['text','marker_id']].rename(columns={'text':'entity'})
    grouped = entity_marker_df.groupby('marker_id').entity.apply(lambda lst: tuple((k, 1) for k in lst))
    category_dicts = [dict(tuples) for tuples in grouped]
    v = DictVectorizer(sparse=False)

    X = v.fit_transform(category_dicts)

    # df_ent_obs is dataframe where each column is feature
    df_ent_obs = pd.DataFrame(X, columns=v.get_feature_names(), index=grouped.index)
    return df_ent_obs

def calc_similarities(df_ent_obs):
    A_sparse = sparse.csr_matrix(df_ent_obs)
    similarities = cosine_similarity(A_sparse)
    return similarities

def similarities_pipeline(csv_out):
    df_ent = load_df_ent()

    # only keep entities on multiple markers
    df_ent = entities_to_encode(df_ent)

    # binary encoding of each entity
    df_ent_obs = encode_entities(df_ent)

    # calculate similarity matrix
    similarities = calc_similarities(df_ent_obs)
    # put into dataframe with columns and index of marker_id
    df_sim = pd.DataFrame(similarities, index=df_ent_obs.index)
    df_sim.columns = df_ent_obs.index

    print("similarities matrix made. head:")
    print(df_sim.head())

    if csv_out is not None:
        print('writing output to {}'.format(csv_out))
        df_sim.to_csv(csv_out)

    return df_sim


if __name__ == '__main__':
    print('running similarities.py from command line')
    if len(argv)>1:
        csv_out = argv[1]
    else:
        csv_out = None
    similarities_pipeline(csv_out)
