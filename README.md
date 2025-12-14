# spotify-clone
University NoSQL course group project: a Spotify-like app handling large-scale data

# Installation:
If you haven't already set up **git**, see https://docs.github.com/en/get-started/git-basics/set-up-git

For setting up the environment, see the **Setting up the environment** section

## Running the Program

Install dependencies:  
* In terminal run `uv sync`

Got to the root: 
* Go to this folder in terminal `..\Github\spotify-clone`

Start the full stack: 
* Once in the right root run `docker compose up -d`

Update changes:

* Whenever you modify backend Python files, you should verify that the backend container detects and reloads the changes. Run `docker logs -f spotify-backend`

You should see something similar to:

    WARNING:  WatchFiles detected changes in 'app/change_logs.py'. Reloading...
    INFO:     Shutting down
    INFO:     Waiting for application shutdown.
    INFO:     Application shutdown complete.
    INFO:     Finished server process [727]
    INFO:     Started server process [791]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.

Stop and clean up containers:
* Once you finish using the program run `docker compose down`

**Important Note — Avoid Data Loss & Cassandra Corruption**

Cassandra requires a clean and graceful shutdown to ensure data integrity.
Always run `docker compose down` before closing your environment or powering off your machine.

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
For setting up the environment, see the appropriate project's, located in assignments/, README.md
