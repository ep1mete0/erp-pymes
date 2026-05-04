from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="pos.html", context={}
    )


@app.get("/inventario")
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="inventario.html", context={}
    )


@app.get("/proveedores")
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="proveedores.html", context={}
    )


@app.get("/turnos_cajas")
def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="turnos_cajas.html", context={}
    )
