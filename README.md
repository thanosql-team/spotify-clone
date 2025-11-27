# spotify-clone
University NoSQL course group project: a Spotify-like app handling large-scale data

# Installation:
If you haven't already set up **git**, see https://docs.github.com/en/get-started/git-basics/set-up-git

For setting up the environment, see the appropriate project's, located in assignments/, README.md

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

    WARNING:  WatchFiles detected changes in '1-mongodb-app/change_logs.py'. Reloading...
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
