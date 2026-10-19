## Purpose of the project

Main purpose of this project is to provide utils for [Dominions 6](https://www.illwinter.com/dom6) game

List of current utils:

1. Automated map generation for the Arena map for Dominions 5.
2. Automated map generation for the Arena map for Dominions 6.
3. Battle report screenshot parser for Dominions 6 (see below).

## Battle report parser

Turns a screenshot of the battle report table into JSON:

```json
{"Tir na n'Og": {"Sidhe Lords": {"quantity": 7, "killed": 220, "dead": 7}}}
```

`killed`/`dead` are `null` when the cell is empty, `0+3` is summed to `3`, and
"Province Defence of ..." blocks are skipped. No AI/LLM is involved: the table
layout is found with OpenCV, numbers are read by matching against glyph templates
of the game font, and unit/nation names are read with Tesseract OCR and snapped
to the bundled Dominions 6 unit/nation lists (`units.txt`, `nations.txt`, from
dom6inspector) to fix small OCR slips. Works on full-size reports and on the
small in-game "Battle Summary" window. Parsing an image takes a few seconds and
stays under ~300MB of RAM.

Requires the `tesseract-ocr` system package (installed in the Docker image).

- Web: `POST /dom6/battle-report/parse/` with the image as multipart field `image`
  (or as the raw body) returns `{"job_id": ...}`. Poll
  `GET /dom6/battle-report/parse/<job_id>/` until `status` is `done` (or `error`);
  the response has `result` and `warnings` (e.g. when unit counts don't add up to
  the Total row). Jobs expire after an hour.
- Worker: run one `python -m apps.battleparser.worker` process next to the app;
  it handles one image at a time.
- CLI: `python -m apps.battleparser screenshot.png [more.png ...]`.
- Digit templates are built from the labelled screenshots in
  `apps/battleparser/tests/fixtures/`; after adding fixtures, rebuild them with
  `python -m apps.battleparser.build_glyphs`.


## Credits
Original Arena map:
https://steamcommunity.com/sharedfiles/filedetails/?id=1404827698

Please support author of the Arena map: http://www.youtube.com/dastactic

Also this project make extensive use of the data from:
https://github.com/larzm42/dom6inspector

All credits for data dumps into csv format goes to them.

## Changelog
- 20/05/2021 - Cave map support
- 02/06/2021 - Add mapname change, tweaked text; Add Holy for magic paths;
- 30/07/2021 - Add DomEnh and DebugMod support;
- 15/04/2024 - Closed beta testing;
- 17/04/2024 - Retired old implementation;

## Plans for the future versions
- Allow custom mods load;

## License
GNU GPLv3 (see License.md) on files that are not map.
