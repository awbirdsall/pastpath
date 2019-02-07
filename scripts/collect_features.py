#!/usr/bin/env python

'''collect_features.py : collect per-marker features and generate matrix

Adapted from nb/190130-combine-cats-ents-decade-features.ipynb

'''

import pandas as pd
import re
import spacy
from sys import argv

import ast
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import MultiLabelBinarizer

# feature filtering parameters
MIN_FEATURES_PER_MARKER = 5
MIN_MARKERS_PER_FEATURE = 2
MAX_MARKERS_PER_FEATURE = 1000

# file paths
MARKER_CSV_IN = "../data/190121-all-markers-with-cats.csv"
WIKI_CSV_IN = "../data/wiki_text/190129-ent-pages.csv"
DECADE_CSV_IN = "../data/190129-decade-from-ent.csv"
NER_CSV_IN = "../data/190128-df-ent.csv"

FEAT_FULL_CSV_OUT = '../data/190130-df-feature-counts-full.csv'
FEAT_CSV_OUT = '../data/190130-df-feature-counts.csv'
MARKER_CSV_OUT = "../data/190130-df-marker.csv"

def standardize_text(df, col_name):
    text_series = df[col_name].copy()
    # remove one or more alternating series of periods and whitespace
    text_series = text_series.str.replace(r"\.\s+\.(\s+\.)*", ".")
    # remove multiple spaces after a period
    text_series = text_series.str.replace(r"\.(\s)+", ". ")
    # remove carriage returns
    text_series = text_series.str.replace(r"\n", "")
    # remove remaining multiple spaces
    text_series = text_series.str.replace(r"(\s)+", " ")
    # remove ' .' artifacts
    text_series = text_series.str.replace(r" \.", ".")
    # remove '?.' artifacts
    text_series = text_series.str.replace(r"\?\.", "?")
    return text_series



def feature_pipeline(ner_csv_in=NER_CSV_IN, feat_csv_out=FEAT_CSV_OUT,
        marker_csv_out=MARKER_CSV_OUT, feat_full_csv_out=FEAT_FULL_CSV_OUT):
    # load relevant DataFrames
    df_marker = pd.read_csv(MARKER_CSV_IN).query("cty=='washington_dc'")
    df_marker['text_clean'] = standardize_text(df_marker, 'text')

    df_wiki = pd.read_csv(WIKI_CSV_IN)
    df_wiki['summarize_clean'] = standardize_text(df_wiki, 'summarize')
    # quick and safe way to convert cats from string to actual list
    df_wiki['cats'] = df_wiki['cats'].apply(lambda x: ast.literal_eval(x))

    # remove parentheses from category list items
    remove_paren = lambda x: re.sub(r"[\(\)]", "", x)
    remove_paren_list = lambda l: [remove_paren(i) for i in l]
    df_wiki['cats'] = df_wiki['cats'].apply(remove_paren_list)

    df_wiki['summarize_clean'] = standardize_text(df_wiki, 'summarize')

    df_decade = pd.read_csv(DECADE_CSV_IN)

    df_ent = pd.read_csv(ner_csv_in).rename(columns={"text":"entity"})

    
    # Add decade to df_ent
    df_ent_decade = pd.merge(df_ent,
             df_decade.dropna(subset=['decade']).loc[:,['entity','decade']].drop_duplicates('entity'),
             how='left', on='entity')

    # ### Add wiki summary and categories to each entity in df_ent
    # 
    # - don't include DATE labelled entities
    df_ent_decade_wiki = pd.merge(df_ent_decade,
             df_wiki.query("label!='DATE'").drop_duplicates('entity').rename(columns={'title':'wikititle', 'cats':'wikicats', 'summarize_clean':'wikisum'}).loc[:,['wikititle','entity','wikicats','wikisum']],
             how='left', on='entity')


    # ### For each marker add entities, decade, wikicats, wikisums
    mrkrs_per_ent = df_ent_decade_wiki.groupby('entity').marker_id.apply(lambda x: len(x.unique()))
    ents_to_keep = mrkrs_per_ent[mrkrs_per_ent>=1].index.values

    df_edw_for_merge = df_ent_decade_wiki[df_ent_decade_wiki.entity.isin(ents_to_keep)]

    # ### Make column for each wikicat category
    # combine all wikicats for each marker into a single list
    df_wikicats = df_edw_for_merge.loc[:, ['marker_id','wikicats']].groupby('marker_id').aggregate(sum).dropna()
    # for whatever reason, need to remove 0 after removing notnull...
    # something related to the lists generated from ast
    df_wikicats = df_wikicats[df_wikicats.wikicats.notnull().values]
    df_wikicats = df_wikicats.query("wikicats!=0")

    mlb = MultiLabelBinarizer()
    df_wikicats_counts = pd.DataFrame(mlb.fit_transform(df_wikicats['wikicats']),
                 columns=mlb.classes_, index=df_wikicats.index)

    df_wikicats_counts.columns = [x+"_wc" for x in df_wikicats_counts.columns]

    # ### Make column for each entity
    # 
    # Don't include DATE
    grouped = df_edw_for_merge.query("label!='DATE'").groupby('marker_id').entity.apply(lambda lst: tuple((k, 1) for k in lst))
    category_dicts = [dict(tuples) for tuples in grouped]
    v = DictVectorizer(sparse=False)
    X = v.fit_transform(category_dicts)
    df_ent_counts = pd.DataFrame(X, columns=v.get_feature_names(), index=grouped.index)
    df_ent_counts.columns = [x+"_ne" for x in df_ent_counts.columns]

    # ### Make column for each decade
    grouped = df_edw_for_merge.dropna(subset=["decade"]).groupby('marker_id').decade.apply(lambda lst: tuple((k, 1) for k in lst))
    category_dicts = [dict(tuples) for tuples in grouped]
    v = DictVectorizer(sparse=False)
    X = v.fit_transform(category_dicts)
    df_decade_counts = pd.DataFrame(X, columns=v.get_feature_names(), index=grouped.index)
    # don't allow future dates
    df_decade_counts = df_decade_counts.loc[:, df_decade_counts.columns<=2010]
    df_decade_counts.columns = [str(int(x))+"_dc" for x in df_decade_counts.columns]

    bar_x = df_decade_counts.sum().index
    bar_height = df_decade_counts.sum()

    # dealt with markercats in ner.py

#     df_markercats_counts = pd.DataFrame(df_marker.set_index("marker_id").loc[:,'20th Century':'Women'])
#     df_markercats_counts.columns = [x+"_mc" for x in df_markercats_counts.columns]

    # ## Merge all features together

    # For each marker combine columns of counts of
    # 
    # - decades `df_decade_counts`
    # - entities (non-DATE) `df_ent_counts`
    # - marker categories `df_markercats_counts`
    # - wiki categories `df_wikicats_counts`
    # 
    # and then weight by tf idf.
    # 
    # Looks like sklearn has a way to treat a series of Columns in custom ways
    # with ColumnVectorizer, so I could have done the above more efficiently...

    # merge, keeping all marker_ids
    df_all_counts_full = pd.merge(
        pd.merge(
            df_ent_counts,
            df_decade_counts, how='outer', on='marker_id'),
        df_wikicats_counts, how='outer', on='marker_id').fillna(0).astype(bool)
    print("merged df_all_counts_full.head():")
    print(df_all_counts_full.head())
    df_all_counts_full.columns = df_all_counts_full.columns.astype(str)
    # alphabetize columns
    df_all_counts_full = df_all_counts_full.reindex(sorted(df_all_counts_full.columns), axis=1)

    # This is a big checkpoint! Save.
    print("collect_features: saving unfiltered, full output to {}".format(feat_full_csv_out))
    df_all_counts_full.to_csv(feat_full_csv_out)

    # Across the board filter features based on min and max number of markers they appear in.
    mrkrs_per_feature = df_all_counts_full.sum(axis=0)
    features_to_keep = mrkrs_per_feature[(mrkrs_per_feature>=MIN_MARKERS_PER_FEATURE)&(mrkrs_per_feature<=MAX_MARKERS_PER_FEATURE)].index.values
    df_all_counts_drop_features = df_all_counts_full.loc[:,features_to_keep]

    # Also remove markers without sufficient features.
    features_per_mrkr = df_all_counts_drop_features.sum(axis=1)
    mrkrs_to_keep = features_per_mrkr[(features_per_mrkr>=MIN_FEATURES_PER_MARKER)].index.values
    df_all_counts = df_all_counts_drop_features.loc[mrkrs_to_keep,:]

    print("collect_features: saving output to {}".format(feat_csv_out))
    df_all_counts.to_csv(feat_csv_out)

    # Some things might have leaked through the process above... but since it's
    # not really a hard cutoff, fine.

    # ### Report how many wiki categories survive
    features_series = pd.Series(df_all_counts.columns)
    wc_features = features_series[features_series.str.contains("_wc")]
    print("collect_features: wiki cats in output: {}".format(len(wc_features)))
    
    # ### Save corresponding marker array
    df_marker_out = df_marker[df_marker.marker_id.isin(mrkrs_to_keep)]
    print("collect_features: saving corresponding marker list to {}".format(marker_csv_out))
    df_marker_out.to_csv(marker_csv_out)


if __name__ == '__main__':
    print("running collect_features.py from command line")
    feature_pipeline(ner_csv_in=NER_CSV_IN, feat_csv_out=FEAT_CSV_OUT,
        marker_csv_out=MARKER_CSV_OUT, feat_full_csv_out=FEAT_FULL_CSV_OUT)
