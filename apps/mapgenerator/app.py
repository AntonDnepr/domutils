import zipfile
from io import BytesIO, StringIO
from os import getenv
from urllib.parse import unquote_plus

import sentry_sdk
from apps.core.consts import ERAS, VANILLA
from apps.core.utils import check_if_int, clean_search_string
from apps.dom6data.models import Dom6Item, Dom6Nation, Dom6Unit
from apps.domdata.models import Nation, Unit
from apps.mapgenerator.mapgen import (
    data_into_map,
    dom6_data_into_map,
    dom6_process_data,
    dom6_substitute,
    process_data,
    substitute,
)
from sanic import Sanic, json, text
from sanic.request import Request
from sanic.response.types import HTTPResponse
from sanic_ext import render
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.sanic import (
    SanicIntegration,
    _hub_enter,
    _hub_exit,
    _set_transaction,
)

app = Sanic("DominionsUtils")
app.config.TEMPLATING_PATH_TO_TEMPLATES = "./apps/mapgenerator/templates"
app.static("/static/", "./apps/mapgenerator/templates/assets")


@app.listener("before_server_start")
async def init_sentry(_):
    if getenv("SENTRY_DSN", ""):
        sentry_sdk.init(
            dsn=getenv("SENTRY_DSN", ""),
            integrations=[AsyncioIntegration(), SanicIntegration()],
            enable_tracing=True,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=1.0,
        )


if getenv("SENTRY_DSN", ""):
    # we manually need to set the signals because sentry sanic integration doesn't work
    app.signal("http.lifecycle.request")(_hub_enter)
    app.signal("http.lifecycle.response")(_hub_exit)
    app.signal("http.routing.after")(_set_transaction)


@app.get("/")
async def main(request: Request):
    return await render("index.html", status=200)


@app.get("/error/100/always")
async def error_generator(request):
    1 / 0  # raises an error
    return text("Hello, world.")


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
async def autocomplete_units(request: Request) -> HTTPResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    search_term = clean_search_string(search_term)
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
    if not units:
        units = Unit.find((Unit.name % f"{search_term}") & mods_query).all()
    return await render(
        "dom5/includes/units_table.html",
        status=200,
        context={"units": [x.model_dump() for x in units]},
    )


@app.get("/dom5/autocomplete/nations/")
async def autocomplete_nations(request: Request) -> HTTPResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    search_term = clean_search_string(search_term)
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
    if not nations:
        nations = Nation.find((Nation.name % f"{search_term}") & mods_query).all()
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
async def dom6_autocomplete_units(request: Request) -> HTTPResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    search_term = clean_search_string(search_term)
    if not search_term:
        return await render(
            "dom6/includes/units_table.html",
            status=200,
            context={"units": []},
        )
    mods_query = Dom6Unit.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Dom6Unit.mod == selected_mod
    query = (
        (Dom6Unit.dominions_id == int(search_term))
        if check_if_int(search_term)
        else (Dom6Unit.name % f"{search_term}*")
    )
    units = Dom6Unit.find(query & mods_query).all()
    if not units:
        units = Dom6Unit.find((Dom6Unit.name % f"{search_term}") & mods_query).all()
    return await render(
        "dom6/includes/units_table.html",
        status=200,
        context={"units": [x.model_dump() for x in units]},
    )


@app.get("/dom6/autocomplete/nations/")
async def dom6_autocomplete_nations(request: Request) -> HTTPResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    search_term = clean_search_string(search_term)
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
    if not nations:
        nations = Dom6Nation.find(
            (Dom6Nation.name % f"{search_term}") & mods_query
        ).all()
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
async def dom6_autocomplete_items(request: Request) -> HTTPResponse:
    mods = request.args.getlist("mods", [])
    search_term = request.args.get("search_term", "")
    search_term = clean_search_string(search_term)
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
    if not items:
        items = Dom6Item.find((Dom6Item.name % f"{search_term}") & mods_query).all()
    return await render(
        "dom6/includes/items_table.html",
        status=200,
        context={"items": [{"name": x.name} for x in items]},
    )


@app.post("/dom6/generate-map/")
async def dom6_generate_map(request: Request):
    json_data = request.json
    only_map = json_data.get("only_map", False)
    returned_data = dom6_process_data(json_data)
    mapgenerated_text = dom6_data_into_map(returned_data)
    final_map = dom6_substitute(json_data, mapgenerated_text)
    map_as_bytes = StringIO(final_map)
    zip_buffer = BytesIO()
    dirname = "apps/dom6data/mapfiles/CustomArena"
    names = [
        "CustomArena_plane2.map",
        "CustomArena_plane2.tga",
        "CustomArena_winter.tga",
        "CustomArena.tga",
        "banner.png",
    ]
    if only_map:
        resp = await request.respond(content_type="text/plain; charset=utf-8")
        resp.headers["Content-Disposition"] = "attachment; filename=CustomArena.map"
        await resp.send(map_as_bytes.read())
        await resp.eof()
    else:
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name in names:
                with open(f"{dirname}/{file_name}", "rb") as f:
                    zip_file.writestr(f"CustomArena/{file_name}", f.read())
            zip_file.writestr("CustomArena/CustomArena.map", map_as_bytes.getvalue())
        resp = await request.respond(content_type="application/zip; charset=utf-8")
        resp.headers["Content-Disposition"] = "attachment; filename=CustomArena.zip"
        await resp.send(zip_buffer.getvalue())
        await resp.eof()


@app.get("/dom6/arena-mapgen/<name:str>/")
async def dom6_arena_units(request: Request, name: str):
    return await render(
        "dom6/units.html",
        status=200,
        context={"dom6_arena_active": True, "name": unquote_plus(name)},
    )


@app.get("/credits/")
async def credits(request: Request):
    return await render("credits.html", status=200)


@app.get("/history/")
async def history(request: Request):
    return await render("releases_history.html", status=200)


@app.get("/dom6/api/units/<name:str>/")
async def dom6_api_unit_data(request: Request, name: str):
    mods = request.args.getlist("mods", [])
    if not name:
        return json([])
    search_term = unquote_plus(name)
    search_term = clean_search_string(search_term)
    mods_query = Dom6Unit.mod == VANILLA
    for selected_mod in mods:
        mods_query |= Dom6Unit.mod == selected_mod
    units = Dom6Unit.find(Dom6Unit.name % f"{search_term}" & mods_query).all()
    while search_term and not units:
        units = Dom6Unit.find((Dom6Unit.name % f"{search_term}*") & mods_query).all()
        search_term = search_term[:-1]
        search_term = clean_search_string(search_term)
    if not units:
        return json([])
    final_data = []
    for unit in units:
        model_dump = unit.model_dump(mode="json")
        nation_dumps = []
        for nation_pk in model_dump["nations_ids"]:
            nation = Dom6Nation.get(pk=nation_pk)
            nation_dumps.append(nation.model_dump(mode="json"))
        model_dump["nations"] = nation_dumps
        final_data.append(model_dump)
    return json(final_data)
