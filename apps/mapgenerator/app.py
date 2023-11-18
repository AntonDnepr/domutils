from io import StringIO
from os import getenv

import sentry_sdk
from apps.mapgenerator.mapgen import data_into_map, process_data, substitute
from domdata.models import VANILLA, Nation, Unit
from sanic import Sanic, json
from sanic.request import Request
from sanic.response.types import JSONResponse

if getenv("ENV", "") != "test":
    sentry_sdk.init(
        dsn=getenv("SENTRY_SDK", ""),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )

app = Sanic("DominionsUtils")


@app.get("/")
async def main(request: Request):
    pass


@app.get("/dom5/autocomplete/units/")
async def autocomplete_units(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return json([])
    mods_query = None
    if not mods:
        mods_query = Unit.mod == VANILLA
    for selected_mod in mods:
        if mods_query is None:
            mods_query = Unit.mod == selected_mod
        else:
            mods_query |= Unit.mod == selected_mod
    units = Unit.find((Unit.name % f"{search_term}*") & mods_query).all()
    return json([x.dict() for x in units])


@app.get("/dom5/autocomplete/nations/")
async def autocomplete_nations(request: Request) -> JSONResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    if not search_term:
        return json([])
    mods_query = None
    if not mods:
        mods_query = Nation.mod == VANILLA
    for selected_mod in mods:
        if mods_query is None:
            mods_query = Nation.mod == selected_mod
        else:
            mods_query |= Nation.mod == selected_mod
    nations = Nation.find((Nation.name % f"{search_term}*") & mods_query).all()
    return json([x.dict() for x in nations])


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
