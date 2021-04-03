from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn 

from app import views

app = FastAPI(root_path="/api/v1")
# TODO does this get served out of nginx or not
app.mount("/static", StaticFiles(directory="app/static"), name="static")

origins = [
    # TODO handle CORS appropriately, if needed
    "http://web",
    "http://web:8080",
    "127.18.0.3",
    "127.18.0.3:8080",
    "http://localhost",
    "http://localhost:8080",
    "http://pastpath.tours",
    "*"
]

app.include_router(views.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
