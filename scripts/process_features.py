#!/usr/bin/env python

'''process_features.py : weight features, calculate similarities, find clusters
in reduced dimensions

adapted from nb/190130-combine-cats-ents-decade-features.ipynb

'''

import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction import DictVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn import metrics

from sklearn.cluster import KMeans
from sys import argv

# SVD and k means parameters
N_COMPONENTS = 200
N_CLUSTERS = 20

# file paths
FEAT_CSV_IN = '../data/190130-df-feature-counts.csv'

SIM_CSV_OUT = "../data/190130-df-sim-tfidf.csv"
CLUST_CSV_OUT = "../data/190130-km-labels.csv"

def calc_sim_matrix(feat_csv_in=FEAT_CSV_IN, sim_csv_out=SIM_CSV_OUT):
    df_all_counts = pd.read_csv(feat_csv_in, index_col='marker_id')
    print(df_all_counts.head())

    # ### Apply tf-idf to feature matrix
    # Already have used vectorizer, essentially, so just need to apply TfidfTransformer
    A_sparse = sparse.csr_matrix(df_all_counts)
    tfidf = TfidfTransformer()
    X = tfidf.fit_transform(A_sparse)
    similarities = cosine_similarity(X)

    # ### Make similarities dataframe and save to file
    df_sim_tfidf = pd.DataFrame(similarities, index=df_all_counts.index)
    df_sim_tfidf.columns = df_all_counts.index
    df_sim_tfidf.to_csv(sim_csv_out)
    return None

def calc_clusters(feat_csv_in=FEAT_CSV_IN, clust_csv_out=CLUST_CSV_OUT):
    # #### Perform SVD followed by k-means on TF-IDF weighted output.
    # Follow sklearn example:
    # https://scikit-learn.org/stable/auto_examples/text/plot_document_clustering.html#sphx-glr-auto-examples-text-plot-document-clustering-py

    df_all_counts = pd.read_csv(feat_csv_in, index_col='marker_id')
    A_sparse = sparse.csr_matrix(df_all_counts)
    tfidf = TfidfTransformer()
    X = tfidf.fit_transform(A_sparse)

    # Vectorizer results are normalized, which makes KMeans behave as
    # spherical k-means for better results. Since LSA/SVD results are
    # not normalized, we have to redo the normalization.
    svd = TruncatedSVD(n_components=N_COMPONENTS)
    normalizer = Normalizer(copy=False)
    lsa = make_pipeline(svd, normalizer)

    X = lsa.fit_transform(X)

    explained_variance = svd.explained_variance_ratio_.sum()

    km = KMeans(n_clusters=N_CLUSTERS, init='k-means++', max_iter=100, n_init=1,
                verbose=True)

    km.fit(X)

    print("Silhouette Coefficient: %0.3f"
          % metrics.silhouette_score(X, km.labels_, sample_size=1000))
    print()
    print("Top terms per cluster:")

    # since did LSA, need to return cluster centers to original space
    original_space_centroids = svd.inverse_transform(km.cluster_centers_)
    order_centroids = original_space_centroids.argsort()[:, ::-1]

    terms = df_all_counts.columns.values
    for i in range(N_CLUSTERS):
        print("Cluster %d:" % i, end='')
        for ind in order_centroids[i, :10]:
            print(' %s' % terms[ind], end='')
        print()

    # ### Output k-means labels
    df_km_label = pd.DataFrame({"km_label": km.labels_}, index=df_all_counts.index)
    df_km_label.to_csv(clust_csv_out)
    return None

if __name__ == '__main__':
    print("running collect_features.py from command line")
