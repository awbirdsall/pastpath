from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn 

from app import views

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(views.router)


if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
