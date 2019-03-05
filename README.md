# pastpath: smarter historic marker discovery with NLP

## Overview

This service uses natural language processing to determine similarities between historic markers in Washington, D.C. based primarily on the text on the historic markers, along with metadata from associated Wikipedia pages, and is able to construct suggested walking tour routes for users.

## Web app

The code for a web app is in `app/`. The app is built in Flask and queries a PostgreSQL database containing historic marker information and the results of NLP analysis. The app has been deployed to an AWS EC2 instance using Gunicorn and Nginx and is hosted at <http://pastpath.tours>.

## Analysis scripts

Much of the NLP analysis is performed ahead of time, before the user interacts with the web app. The folder `scripts/` contains scripts used to take input data from the historic marker database (<https://www.hmdb.org>), process it, and load it to a SQL database to be used by the Flask app in `app/`. The entire pipeline of scripts from input to output can be run from the command line using `scripts/pipeline.py`, with command-line flags to control which portions of the pipeline are run. In brief, the four steps and associated command-line flags are:

- `--ner`: Take a csv file of historic markers, pre-process the historic marker texts, perform named entity recognition using Spacy, and perform manual cleaning of the resulting named entities. Output csv of which named entities are in each historic marker text. (code in `scripts/ner.py`)
- `--cf`: Collect features from csv files of named entities, Wikipedia page categories (previously collected with `/scripts/wikitext.py`), decade features (previously collected from date entities), and HMDB categories. Merge into single DataFrame which binary encodes each marker for the presence or absence of each feature, and filter out very infrequently (or frequently) appearing features. Output to csv. (code in `scripts/collect_features.py`)
- `--pf`: Process features: weight features by TF-IDF, calculate similarities of weighted feature vectors (cosine similarity), find clusters (k-means) in reduced dimensions (latent semantic analysis). Output csv of similarity scores, cluster labels, and top terms associated with each cluster. (code in `scripts/process_features.py`)
- `--db`: Interact with postreSQL database. Take csv files of marker data, similarity matrix, named entity counts per marker, and cluster labels, and write them as the appropriate tables in a PostgreSQL database. Can deploy either to local machine or to AWS EC2 instance hosting the web app via ssh tunnel. (code in `scripts/db.py`)

## Web app dependencies

- `flask`
- `numpy`
- `openrouteservice`
- `ortools`
- `pandas`
- `psycopg2`
- `sqlalchemy`
- `sqlalchemy_utils`

## Analysis script dependencies

- `numpy`
- `pandas`
- `scipy`
- `sklearn`
- `spacy` (with `en_core_web_lg` language model)
- `sqlalchemy`
- `sqlalchemy_utils`
