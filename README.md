# pastpath: smarter historic marker discovery with NLP

## Overview

This service uses natural language processing to determine similarities between historic markers in Washington, D.C. based primarily on the text on the historic markers, along with metadata from associated Wikipedia pages, and is able to construct suggested walking tour routes for users.

## Web app

The code for a web app is in `app/`. The app is built in Flask and queries a PostgreSQL database containing historic marker information and the results of NLP analysis. The app has been deployed to an AWS EC2 instance using Gunicorn and Nginx and is hosted at <http://pastpath.tours>.

### Deployment

Install python, nginx, and miniconda (last has interactive prompts):

```bash
$ sudo apt-get update
$ sudo apt-get install -y python
$ sudo apt-get install -y nginx
$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
$ bash Miniconda3-latest-Linux-x86_64.sh
$ source ~/.bashrc
```

Clone project from git

```bash
$ git clone https://github.com/awbirdsall/pastpath.git
```

TODO: use pipenv to install pinned versions of required packages, as defined in Pipfile.lock.

```bash
$ pip install pipenv
$ pipenv install --deploy --ignore-pipfile
```

Set up postgresql

```bash
$ sudo apt install postgresql postgresql-contrib
$ sudo service postgresql start
```

Set password for user (postgres default username)

```bash
$ sudo passwd postgres
```

Populate the database on the EC2 instance over ssh tunnel:

1) on remote DB, command 

```sql
ALTER USER my-db-user WITH ENCRYPTED PASSWORD 'my-db-password';
```

2) make ssh tunnel from arbitrary local client port to postgresql port 5432: 

`$ ssh -L 63333:localhost:5432 defaultuser@remoteaddress`

3) use tunnel port to connect to db as my-db-user

```bash
$ psql -h localhost -p 63333 -U postgres
```

4) run pipeline script with `DB_LOC = 'production'` to write to production database. Only `--db` flag is required if all files already have been created.

```bash
$ python pipeline.py --db
```

Add pastpath/app/instance/config.py with values for that:

```
SQL_USER = USER_NAME_HERE
SQL_KEY = SQL_KEY_HERE
ORS_KEY = ORS_KEY_HERE
```

Transfer static image directory to app/histmark/static/img.

Start nginx and configure

```bash
$ sudo /etc/init.d/nginx start
$ sudo rm /etc/nginx/sites-enabled/default
$ sudo touch /etc/nginx/sites-available/application
$ sudo ln -s /etc/nginx/sites-available/application /etc/nginx/sites-enabled/application
```

Write configuration file for application:

```bash
$ sudo vim /etc/nginx/sites-enabled/application
```

Contents should be:

```
server {
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /static {
        alias /home/ubuntu/pastpath/app/pastpath/static;
    }
}
```

Restart nginx

```bash
$ sudo /etc/init.d/nginx restart
```

Run gunicorn as background process

```bash
$ cd ~/pastpath/app
$ gunicorn pastpath:app -D
```

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
