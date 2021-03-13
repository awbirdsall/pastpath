# pastpath: smarter historic marker discovery with NLP

## Overview

This service uses natural language processing to determine similarities between historic markers in Washington, D.C. based primarily on the text on the historic markers, along with metadata from associated Wikipedia pages, and is able to construct suggested walking tour routes for users.

## Web app

The app is built using FastAPI and queries a PostgreSQL database containing historic marker information and the results of NLP analysis. The app has been deployed to an AWS EC2 instance using Gunicorn and Nginx and is hosted at <http://pastpath.tours>.

### Local testing

The app has been Dockerized using an image built on top of `tiangolo/uvicorn-gunicorn-fastapi:python3.7`.

To test the image locally:

```bash
$ docker build -t pastpath .
$ docker run --network=host pastpath
```

This serves the app at `localhost:80`. The flag `--network=host` is used to make it easy not just to connect to the served app but also for the app to connect to a locally running postgresql database instance.

TODO for deployment don't just use network=host, be more specific -- see below on postgresql

### Deployment

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

Install nginx

```bash
$ sudo apt-get update
$ sudo apt-get install -y nginx
```


Transfer static image directory to app/static/img.

Start nginx and configure

```bash
$ sudo /etc/init.d/nginx start
$ sudo rm /etc/nginx/sites-enabled/default
$ sudo touch /etc/nginx/sites-available/application
$ sudo ln -s /etc/nginx/sites-available/application /etc/nginx/sites-enabled/application
```

Write configuration file for application (this will be included as part of the `nginx.conf`):

```bash
$ sudo vim /etc/nginx/sites-enabled/application
```

Contents should be:

```
server {
  listen 80;
  client_max_body_size 4G;

  server_name pastpath.tours www.pastpath.tours;

  location / {
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
    proxy_buffering off;
    proxy_pass http://uvicorn;
  }

  location /static {
    alias /home/ubuntu/pastpath/app/pastpath/static;
  }
}

upstream uvicorn {
  server unix:/tmp/uvicorn.sock;
}

server {
  listen 80;
  server_name "";
  return 444;
}
```

This is adapted from https://www.uvicorn.org/deployment/ and also includes a server block to disconnect when the host is not provided (i.e., attempted to connect directly to IP).

TODO base on https://docs.gunicorn.org/en/stable/deploy.html because using uvicornworker in gunicorn, not uvicorn directly.

Restart nginx

```bash
$ sudo /etc/init.d/nginx restart
```

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
