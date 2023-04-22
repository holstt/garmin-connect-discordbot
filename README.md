# garmin-health-discordbot

Discord bot providing a daily summary of your Garmin Connect health metrics

## Features

- Get daily summary as soon as yesterday's metrics become available on Garmin Connect (i.e. when your Garmin device has synced with the phone)
- Monitor metrics: Currently includes Sleep, HRV ...
- Spot trends: Compares the most recent metric value to its weekly average
- Docker support: Easy deployment using Docker Compose

**TODO:**

- Add more metrics
- Customize which metrics to include in the daily update
- End of week summary with activity overview, weekly distance, frequency for each activity etc.
- Generate chart and include as image in the daily update to visualize progress

## Requirements

- A [Garmin Connect](https://connect.garmin.com/) account and a Garmin device to collect the data
- A [Discord webhook URL](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) (interaction with the bot is not relevant with current feature set, so we don't need to create a bot account)
- The Poetry package manager, see [installation instructions](https://python-poetry.org/docs/#installation)
- (Only if running with Docker) [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

**1. Clone the repository**:

```
git clone https://github.com/holstt/garmin-health-discordbot.git
cd garmin-health-discordbot
```

**2. Set up configuration**

The bot is configured using environment variables, which can be specified in a `.env` file or set directly in the environment.

`./env.example` provides an example of the required format. Rename the file to `.env` and edit the values as needed:

```bash
# URL for the Discord webhook
WEBHOOK_URL=https://discordapp.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz

# The hour (in 24-hour format) when the daily health summary should be fetched.
# If data is not available at this time, the program will schedule a retry at a
# later time until the data becomes available
NOTIFY_AT_HOUR=6

# The IANA time zone in which the NOTIFY_AT_HOUR is specified.
# See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE=Europe/Berlin

# OPTIONAL: Garmin Connect credentials. If not provided, you will be prompted to
# enter them when the program runs.
GARMIN_EMAIL=my@email.com
GARMIN_PASSWORD=mypassword

# OPTIONAL: Path to the session directory location. If a session file already
# exists in this directory (e.g., from a previous run), it will be reused if still
# valid. If no path is specified, the session will only be stored in memory.
# Please note that if the session is not persisted and you repeatedly restart the
# program, you might experience rate limiting issues due to logging in too often.
SESSION_DIRECTORY_PATH=path/to/session/directory
```

## Local Installation 💻

**3. Install the dependencies and create a virtual environment**

```
poetry install
```

**4. Activate the virtual environment**

```
poetry shell
```

**5. Run the bot**

```
python ./main.py
```

- If you use an `.env` file to configure the environment, it is asummed to be placed in the root of the project folder. Alternatively, you can provide a custom path for your environment file using `./main.py -e path/to/env`

## Docker 🐳

**3. From project root, navigate to the `./docker` folder**

```
cd docker
```

Inspect the configuration in `docker-compose.yml`, especially the `volumes` option, and verify that the assumed host paths match your file structure.

**4. Build and run the Docker Compose project**

```
docker-compose up --build
```

To prevent the container from running as root, you can set the `UID` environment variable to match the current user's ID. The Docker Compose configuration is set up such that it will run the container as this user rather than as root:

Bash:
`export UID && docker-compose up --build`

Powershell:
`$env:UID=$(id -u); docker-compose up --build`

NB: Remember this user must have the necessary permissions to access the volumes specified in `docker-compose.yml`.
