from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import engine
import models
from routers import users, posts
from http import HTTPStatus
from fastapi.responses import HTMLResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(" [LIFESPAN] Iniciando a conexo e criando tabelas..")
    async with engine.begin() as conn:

        await conn.run_sync(models.Base.metadata.create_all)
    print(" [LIFESPAN] Tabelas criadas com sucesso!")

    yield


app = FastAPI(lifespan=lifespan)


app.include_router(users.router)
app.include_router(posts.router)

@app.get("/", status_code=HTTPStatus.OK, response_class=HTMLResponse)
def init():
    return """
    <h1>API rodando com sucesso!</h1>

    """