
import logging
import time
import argparse
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import src.garmin_service as garmin_service
from datetime import timedelta
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.NOTSET,
    format='[%(asctime)s] [%(levelname)s] %(name)-25s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logging.Formatter.converter = time.gmtime  # Use UTC
logger = logging.getLogger(__name__)


# Load args
ap = argparse.ArgumentParser()
ap.add_argument("-e", "--env", required=False,
                help="Path of .env file", type=str, default=".env")
args = vars(ap.parse_args())


async def main():
    env_path: str = args["env"]
    if not Path(env_path).exists():
        raise IOError(f"No .env file found at '{env_path}'")

    logging.info(f"Loading .env from {env_path}")

    # Load environment
    load_dotenv(dotenv_path=env_path)

    while True:
        logger.info("Getting health summary...")
        health_summary = await garmin_service.get_health_summary()
        print(health_summary)
        logger.info("Waiting for next run at: " + str(datetime.utcnow() + timedelta(days=1)))
        await asyncio.sleep(timedelta(days=1).total_seconds())

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e