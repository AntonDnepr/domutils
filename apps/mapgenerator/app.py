from os import getenv

import sentry_sdk
from domdata.models import VANILLA, Nation, Unit
from sanic import Sanic, json

if getenv("ENV", "") != "test":
    sentry_sdk.init(
        dsn=getenv("SENTRY_SDK", ""),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )

app = Sanic("MapGenerator")


@app.get("/")
async def main(request):
    pass


@app.get("/autocomplete/units/")
async def autocomplete_units(request):
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


@app.get("/autocomplete/nations/")
async def autocomplete_nations(request):
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
