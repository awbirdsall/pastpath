#!/usr/bin/env python

'''similarities.py : similarity calculations

Main task: take entities list at DF_ENT_CSV and calculate a similarities
matrix for a filtered subset of the entities, saved to csv_out (command line
argument)
'''

import pandas as pd
from scipy import sparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
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

def encode_entities_binary(df_ent):
    # prep df to binary encode each entity as feature
    entity_marker_df = df_ent.loc[:,['text','marker_id']].rename(columns={'text':'entity'})
    grouped = entity_marker_df.groupby('marker_id').entity.apply(lambda lst: tuple((k, 1) for k in lst))
    category_dicts = [dict(tuples) for tuples in grouped]
    v = DictVectorizer(sparse=False)

    X = v.fit_transform(category_dicts)

    # df_ent_obs is dataframe where each column is feature
    df_ent_obs = pd.DataFrame(X, columns=v.get_feature_names(), index=grouped.index)
    A_sparse = sparse.csr_matrix(df_ent_obs)
    return A_sparse

def encode_entities_tfidf(df_ent):
    # prep for TfidfVectorizer using split on _ as analyzer
    entity_str_per_marker = df_ent.groupby('marker_id').text.agg(lambda x: "_".join(x))

    vectorizer = TfidfVectorizer(analyzer=lambda x: x.split('_'))
    X = vectorizer.fit_transform(entity_str_per_marker)
    return X

def similarities_pipeline(csv_out, enc_type='binary'):
    df_ent = load_df_ent()

    # only keep entities on multiple markers
    df_ent = entities_to_encode(df_ent)

    if enc_type=='binary':
        # binary encoding of each entity
        sparse_encoding = encode_entities_binary(df_ent)
    elif enc_type=='tfidf':
        sparse_encoding = encode_entities_tfidf(df_ent)
    else:
        raise ValueError('invalid enc_type')

    # calculate similarity matrix
    similarities = cosine_similarity(sparse_encoding)

    # put into dataframe with columns and index of marker_id
    marker_ids = df_ent.groupby('marker_id').count().index
    df_sim = pd.DataFrame(similarities, index=marker_ids)
    df_sim.columns = marker_ids

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
    similarities_pipeline(csv_out, 'binary')
    print('similarities.py: done.')
