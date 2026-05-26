from FastApi import FastAPI
from schemas import UserCreate
from database import SessionLocal, engine, get_db



app = FastAPI()

@app.post("/users/", response_model=UserCreate):
    pass