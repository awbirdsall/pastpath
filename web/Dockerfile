FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

copy app-requirements.txt .

RUN pip install --upgrade pip &&\
    pip install -r app-requirements.txt

# create the appropriate directories
# ENV APP=/app/app/
# RUN mkdir $APP
# RUN mkdir $APP/static
# WORKDIR $APP_HOME

COPY ./app /app
