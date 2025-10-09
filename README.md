# spotify-clone
University NoSQL course group project: a Spotify-like app handling large-scale data

# Installation:
If you haven't already set up **git**, see https://docs.github.com/en/get-started/git-basics/set-up-git

For setting up the environment, see the **Setting up the environment** section

# 1 Aplikacija su MongoDB

Parašykite programą pagal pasirinktą temą naudodami MongoDB.

Reikalavimai:

1. Ne mažiau nei 4 esybės (fizinių kolekcijų gali ir tikėtina bus - mažiau).
1. Programos funkcionalumą pademonstruoti naudojant API kvietimus (pvz. naudojant Postman, Insomnia, ARC, curl) arba vartotojo sąsają
1. Pridėti duomenų modelio diagramą

Programa turi būti prasminga ir įgyvendinti funkcionalumą laikydamasi šių prielaidų:

1. Programos funkcionalumas turi būti realistiškas.
2. Duomenų gali būti daug, taigi modelis ir sprendimai turi į tai atsižvelgti.

! UŽDUOTIS įkelia komandos kapitonas !

## Setting up environment

### Installing project / dependencies

1. Follow https://docs.astral.sh/uv/getting-started/ to install and get introduced to **uv** - a Python package and project manager

1. See https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion for getting autocompletion in your terminal for uv and uvx commands

1. Make sure uv is updated to the latest version:\
`uv self update`

1. Change current directory to the project folder:\
`cd assignments/1-mongodb-app`

1. Update the project's environment:\
`uv sync`

1. `uv run fastapi dev` should then successfully run fastapi, https://fastapi.tiangolo.com/, which would automatically locate the modules in the project's working directory

### Linter/formatter

Ruff: see https://docs.astral.sh/ruff/editors/setup/ to setup ruff in your Python editor

### Type checking

Pylance: see https://docs.pydantic.dev/latest/integrations/visual_studio_code/#configure-your-environment to set up Pylance in VSCode (set the Type Checking Mode to `basic`), or equivalently set it up in your Python editor
