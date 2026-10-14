import os
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from src.routers import comments as comments_router
from src.routers import posts as posts_router
from src.routers import users
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
MANIFEST_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "site.webmanifest"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(users.router)
app.include_router(posts_router.router)
app.include_router(comments_router.router)


@app.get("/site.webmanifest", include_in_schema=False)
def web_manifest():
    return FileResponse(MANIFEST_FILE, media_type="application/manifest+json")


def render_error_page(request: Request, status_code: int, message: str):
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "request": request,
            "status_code": status_code,
            "message": message,
        },
        status_code=status_code,
    )


@app.get("/posts", status_code=HTTPStatus.OK, include_in_schema=False)
def homepost(request: Request):
    return templates.TemplateResponse(
        request=request, name="posthome.html", context={"request": request}
    )


@app.get("/article", status_code=HTTPStatus.OK, include_in_schema=False)
def article_post(request: Request):
    return templates.TemplateResponse(
        request=request, name="post_detail.html", context={"request": request}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = (
        exc.detail
        if isinstance(exc.detail, str)
        else "Não foi possível concluir essa solicitação."
    )
    return render_error_page(request, exc.status_code, detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return render_error_page(
        request,
        422,
        "Os dados enviados estão incompletos ou inválidos. Verifique e tente novamente.",
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return render_error_page(
        request,
        500,
        "Aconteceu um erro inesperado. Tente novamente em instantes.",
    )
