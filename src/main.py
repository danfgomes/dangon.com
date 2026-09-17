import os
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from src.routers import comments as comments_router
from src.routers import posts as posts_router
from src.routers import users

import src.models

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(users.router)
app.include_router(posts_router.router)
app.include_router(comments_router.router)


@app.get("/", status_code=HTTPStatus.OK, include_in_schema=False)
@app.get("/home", status_code=HTTPStatus.OK)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="layout.html")