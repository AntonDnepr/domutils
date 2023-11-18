## Purpose of the project

Main purpose of this project is to provide utils for [Dominions 5](http://www.illwinter.com/dom5) game

List of current utils:
1. Automated map generation for the Arena map.


## Credits
Original Arena map:
https://steamcommunity.com/sharedfiles/filedetails/?id=1404827698

Please support author of the Arena map: http://www.youtube.com/dastactic

Also this project make extensive use of the data from:
https://github.com/larzm42/dom5inspector

All credits for data dumps into csv format goes to them.


# Development guide
## Install & Run Locally

First you need to write your `.env` file with correct variables: when using the dockerized
local development setup, copy `.env.local` to `.env`, and modifiy accordingly.

This project contains docker integration.
You have to set or modify some variables in order to start the docker containers and the project as a whole.
All variables must be written without quotation marks and without spaces before and after the equal sign.
Read data from `.env` file into terminal with `set -o allexport; source .env; set +o allexport`
Now you can run docker with `docker-compose up` to start local backend

## Add git hooks

We are using prospectr + pre-commit to make things workable and clear. Before write any code you need to install
dev dependencies and run `pre-commit install -f` after that. Then whenever you run `git commit` you'll have a fancy
output with checks according to our code standards.

## Prepare a new branch for your work

Work on new `bug/features` will be done in a new branch (*)
There is a convention in the name of the branches used:
**`1-short-description-of-purpose`**

Naming a Branch:
    - Start branch name with the Issue Number: `#1 Initial Issue` > `1-initial-branch-name`
    - Use lowercase only
    - Use dashes to separate words

## Make awesome commits

Commits are the smallest portion of code that can be reviewed and has a
purpose in the codebase. Each commit counts in a branch, not only the full set
of changes.

Please follow this guideline:
https://udacity.github.io/git-styleguide/

To use cool github linking to the issue please add #taskNumber in the end. E.g.:

`docs: add changes to the Readme #123`

## Changelog
- 20/05/2021 - Cave map support
- 02/06/2021 - Add mapname change, tweaked text; Add Holy for magic paths;
- 30/07/2021 - Add DomEnh and DebugMod support
- ??/??/?? - Retired old implementation

## Plans for the future versions
- Automate pulling new data for dominions;
- Allow custom mods load;
- Add equipment screen for the commanders;
- Support for Dom6;


## License
GNU GPLv3 (see License.md)
