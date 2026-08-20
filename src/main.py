from fastapi import FastAPI

from src.routers import posts
from src.routers import users


from http import HTTPStatus

import src.models

app = FastAPI()

app.include_router(users.router)
app.include_router(posts.router)




@app.get(
    "/",
    status_code=HTTPStatus.OK,
)
def init():
    return
