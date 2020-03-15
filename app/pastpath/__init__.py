from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
app = FastAPI(
        # __name__, 
        # instance_relative_config=True
        )
# app.config.from_object('config')
# app.config.from_pyfile('config.py')
app.mount("/static", StaticFiles(directory="pastpath/static"), name="static")
from pastpath import views
