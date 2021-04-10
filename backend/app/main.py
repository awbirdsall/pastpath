from fastapi import FastAPI
import uvicorn 

from app import views

app = FastAPI(root_path="/api/v1")

app.include_router(views.router)


if __name__=='__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
