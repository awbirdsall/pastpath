# pastpath: smarter historic marker discovery with NLP

## Overview

This service uses natural language processing to determine similarities between historic markers in Washington, D.C. based primarily on the text on the historic markers, along with metadata from associated Wikipedia pages, and is able to construct suggested walking tour routes for users.

## Web app

The app is built using FastAPI and queries a PostgreSQL database containing historic marker information and the results of NLP analysis. The app has been deployed to an AWS EC2 instance using Gunicorn and Nginx and is hosted at <http://pastpath.tours>.

### Local testing

The app has been Dockerized using an image built on top of `tiangolo/uvicorn-gunicorn-fastapi:python3.7`.

To test the image locally:

```bash
$ docker-compose up
```

This starts up the database and app and makes it accessible at `localhost:8080`. The `web` container running the app is connected to the `db` postgres container within a `pastpath_app_local` network via port 5436, which is only accessible via the network.

Local docker-compose:

- serves app at localhost:8080
- mounts local volumes with both app and database data
- uses `.env` and `.env.db` env_files

### Deployment

#### Overview

1) Add static files not maintained in repo (web/app/static/img)
2) Seed database
3) Bring up db: `docker-compose -f docker-compose.prod.yml up -d db`
3) Bring up web: `docker-compose -f docker-compose.prod.yml up -d web`
3) Bring up nginx: `docker-compose -f docker-compose.prod.yml up -d nginx`

#### Details

Deployment is defined in `docker-compose.prod.yml` inspired by [this](https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/#production-dockerfile).

Production docker-compose:

- adds container running nginx that publishes to ports 80 and 443
- uses a static_volume attached to both the nginx and web services containing the static files
- uses `.env.prod` and `.env.prod.db` env_files
- uses a postgres_data volume attached to the db service
- containers reside in `pastpath_app` network

The entire application runs behind nginx as a proxy server, which quickly handles requests from the internet and is configured to serve the static files. Behind nginx, Gunicorn is used as a process manager for the app, and is run using Uvicorn workers. Uvicorn uses the asynchronous ASGI interface used by FastAPI.

The app runs out of a Docker container built on top of the `tiangolo/uvicorn-gunicorn-fastapi` image. The PostgreSQL database runs in a separate Docker container.

#### Start and seed database

Assume existing database already exists and seed script exists (e.g. dumped to file with `$ pg_dump -d <db_name> > /path/to/seed/seed.sql`).

```bash
$ docker-compose up -d db
$ docker-compose run -v /path/to/seed:/backup/ db bash
```

Within database container, seed database:

```bash
$ psql -U <username> -h db.pastpath_app -p <port> -f /backup/seed.sql
$ exit
```

#### Start web container

```bash
$ docker-compose up -d web
```

Configured to serve at port 8080.

#### Start nginx

TODO base on https://docs.gunicorn.org/en/stable/deploy.html because using uvicornworker in gunicorn, not uvicorn directly.

## Analysis scripts

Much of the NLP analysis is performed ahead of time, before the user interacts with the web app. The folder `scripts/` contains scripts used to take input data from the historic marker database (<https://www.hmdb.org>), process it, and load it to a SQL database to be used by the FastAPI app in `app/`. The entire pipeline of scripts from input to output can be run from the command line using `scripts/pipeline.py`, with command-line flags to control which portions of the pipeline are run. In brief, the four steps and associated command-line flags are:

- `--ner`: Take a csv file of historic markers, pre-process the historic marker texts, perform named entity recognition using Spacy, and perform manual cleaning of the resulting named entities. Output csv of which named entities are in each historic marker text. (code in `scripts/ner.py`)
- `--cf`: Collect features from csv files of named entities, Wikipedia page categories (previously collected with `/scripts/wikitext.py`), decade features (previously collected from date entities), and HMDB categories. Merge into single DataFrame which binary encodes each marker for the presence or absence of each feature, and filter out very infrequently (or frequently) appearing features. Output to csv. (code in `scripts/collect_features.py`)
- `--pf`: Process features: weight features by TF-IDF, calculate similarities of weighted feature vectors (cosine similarity), find clusters (k-means) in reduced dimensions (latent semantic analysis). Output csv of similarity scores, cluster labels, and top terms associated with each cluster. (code in `scripts/process_features.py`)
- `--db`: Interact with postreSQL database. Take csv files of marker data, similarity matrix, named entity counts per marker, and cluster labels, and write them as the appropriate tables in a PostgreSQL database. Can deploy either to local machine or to AWS EC2 instance hosting the web app via ssh tunnel. (code in `scripts/db.py`)

## Web app dependencies

See `web/app-requirements.in` and `web/app-requirements.txt` (generated with pip-tools).

## Analysis script dependencies

- `numpy`
- `pandas`
- `scipy`
- `sklearn`
- `spacy` (with `en_core_web_lg` language model)
- `sqlalchemy`
- `sqlalchemy_utils`
