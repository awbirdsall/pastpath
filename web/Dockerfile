FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

copy app-requirements.txt .

RUN pip install --upgrade pip &&\
    pip install -r app-requirements.txt

COPY ./app /app/app
