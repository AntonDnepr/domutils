from os import getenv

import sentry_sdk
from core.redis import get_redis_client
from domdata.models import VANILLA, Nation, Unit
from sanic import Sanic, json

sentry_sdk.init(
    dsn=getenv("SENTRY_SDK", ""),
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
)

app = Sanic("MapGenerator")
app.ctx.db = get_redis_client()


@app.get("/")
async def main(request):
    pass


@app.get("/autocomplete/units/")
async def autocomplete_units(request):
    mods = request.args.getlist("mods")
    search_term = request.args.get("search_term")
    mods_query = Unit.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Unit.mod == selected_mod
    units = Unit.find((Unit.name % f"{search_term}*") & mods_query).all()
    return json([x.model_dump() for x in units])


@app.get("/autocomplete/nations/")
async def autocomplete_nations(request):
    mods = request.args.getlist("mods")
    search_term = request.args.get("search_term")
    mods_query = Nation.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Nation.mod == selected_mod
    nations = Nation.find((Nation.name % f"{search_term}*") & mods_query).all()
    return json([x.model_dump() for x in nations])
