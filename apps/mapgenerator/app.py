from io import StringIO
from os import getenv
from urllib.parse import unquote_plus

import sentry_sdk
from apps.mapgenerator.mapgen import (
    data_into_map,
    dom6_data_into_map,
    dom6_process_data,
    dom6_substitute,
    process_data,
    substitute,
)
from core.consts import ERAS, VANILLA
from dom6data.models import Dom6Item, Dom6Nation, Dom6Unit
from domdata.models import Nation, Unit
from sanic import Sanic
from sanic.request import Request
from sanic.response.types import JSONResponse
from sanic_ext import render

if getenv("ENV", "") != "test":
    sentry_sdk.init(
        dsn=getenv("SENTRY_SDK", ""),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )

app = Sanic("DominionsUtils")
app.config.TEMPLATING_PATH_TO_TEMPLATES = "./apps/mapgenerator/templates"
app.static("/static/", "./apps/mapgenerator/templates/assets")


@app.get("/")
async def main(request: Request):
    return await render("index.html", status=200)


@app.get("/dom5/arena-mapgen/")
async def dom5_arena(request: Request):
    return await render(
        "dom5/arena.html", status=200, context={"dom5_arena_active": True}
    )


@app.get("/dom5/arena-mapgen/select-nations/")
async def dom5_arena_nations_select(request: Request):
    return await render(
        "dom5/arena_nations_select.html",
        status=200,
        context={"dom5_arena_active": True},
    )


@app.get("/dom5/autocomplete/units/")
async def autocomplete_units(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return await render(
            "dom5/includes/units_table.html",
            status=200,
            context={"units": []},
        )
    mods_query = Unit.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Unit.mod == selected_mod
    units = Unit.find((Unit.name % f"{search_term}*") & mods_query).all()
    return await render(
        "dom5/includes/units_table.html",
        status=200,
        context={"units": [x.dict() for x in units]},
    )


@app.get("/dom5/autocomplete/nations/")
async def autocomplete_nations(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return await render(
            "dom5/includes/nations_table.html",
            status=200,
            context={"nations": []},
        )
    mods_query = Nation.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Nation.mod == selected_mod
    nations = Nation.find((Nation.name % f"{search_term}*") & mods_query).all()
    return await render(
        "dom5/includes/nations_table.html",
        status=200,
        context={
            "nations": [
                {
                    "era": ERAS[x.era],
                    "name": x.name,
                    "dominions_id": x.dominions_id,
                }
                for x in nations
            ]
        },
    )


@app.post("/dom5/generate-map/")
async def generate_map(request: Request):
    json_data = request.json
    returned_data = process_data(json_data)
    mapgenerated_text = data_into_map(returned_data)
    final_map = substitute(json_data, mapgenerated_text)
    map_as_bytes = StringIO(final_map)
    resp = await request.respond(content_type="text/plain; charset=utf-8")
    resp.headers["Content-Disposition"] = "attachment; filename=MyArena.map"
    await resp.send(map_as_bytes.read())
    await resp.eof()


@app.get("/dom5/arena-mapgen/<name:str>/")
async def dom5_arena_units(request: Request, name: str):
    return await render(
        "dom5/units.html",
        status=200,
        context={"dom5_arena_active": True, "name": unquote_plus(name)},
    )


@app.get("/dom6/arena-mapgen/")
async def dom6_arena(request: Request):
    return await render(
        "dom6/arena.html", status=200, context={"dom6_arena_active": True}
    )


@app.get("/dom6/arena-mapgen/select-nations/")
async def dom6_arena_nations_select(request: Request):
    return await render(
        "dom6/arena_nations_select.html",
        status=200,
        context={"dom6_arena_active": True},
    )


@app.get("/dom6/autocomplete/units/")
async def dom6_autocomplete_units(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return await render(
            "dom6/includes/units_table.html",
            status=200,
            context={"units": []},
        )
    mods_query = Dom6Unit.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Dom6Unit.mod == selected_mod
    units = Dom6Unit.find((Dom6Unit.name % f"{search_term}*") & mods_query).all()
    return await render(
        "dom6/includes/units_table.html",
        status=200,
        context={"units": [x.dict() for x in units]},
    )


@app.get("/dom6/autocomplete/nations/")
async def dom6_autocomplete_nations(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return await render(
            "dom6/includes/nations_table.html",
            status=200,
            context={"nations": []},
        )
    mods_query = Dom6Nation.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Dom6Nation.mod == selected_mod
    nations = Dom6Nation.find((Dom6Nation.name % f"{search_term}*") & mods_query).all()
    return await render(
        "dom6/includes/nations_table.html",
        status=200,
        context={
            "nations": [
                {
                    "era": ERAS[x.era],
                    "name": x.name,
                    "dominions_id": x.dominions_id,
                }
                for x in nations
            ]
        },
    )


@app.get("/dom6/autocomplete/items/")
async def dom6_autocomplete_items(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return await render(
            "dom6/includes/items_table.html",
            status=200,
            context={"items": []},
        )
    mods_query = Dom6Item.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Dom6Item.mod == selected_mod
    items = Dom6Item.find((Dom6Item.name % f"{search_term}*") & mods_query).all()
    return await render(
        "dom6/includes/items_table.html",
        status=200,
        context={"items": [{"name": x.name} for x in items]},
    )


@app.post("/dom6/generate-map/")
async def dom6_generate_map(request: Request):
    json_data = request.json
    returned_data = dom6_process_data(json_data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    final_map = dom6_substitute(json_data, mapgenerated_text)
    map_as_bytes = StringIO(final_map)
    resp = await request.respond(content_type="text/plain; charset=utf-8")
    resp.headers["Content-Disposition"] = "attachment; filename=MyArena.map"
    await resp.send(map_as_bytes.read())
    await resp.eof()


@app.get("/dom6/arena-mapgen/<name:str>/")
async def dom6_arena_units(request: Request, name: str):
    return await render(
        "dom6/units.html",
        status=200,
        context={"dom6_arena_active": True, "name": unquote_plus(name)},
    )
