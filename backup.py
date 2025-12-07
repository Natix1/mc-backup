import docker as docker
import docker.errors
import logging
import os
import shutil
import datetime

from dotenv import load_dotenv
from uuid import uuid4
from pathlib import PosixPath

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mc-backup")

def getenv(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        logger.critical(f"{key} not specified in environment")
        raise ValueError(f"{key} not specified in environment")

    return value

CONTAINER_NAME = getenv("CONTAINER_NAME")
SERVER_DIRECTORY = PosixPath(getenv("SERVER_DIRECTORY"))
BACKUPS_DIRECTORY = PosixPath(getenv("BACKUPS_DIRECTORY"))

docker_client = docker.from_env()

# Runs command via rcon-cli only if the docker container exists and is up
def rcon_safe(command: list[str]):
    try:
        container = docker_client.containers.get(CONTAINER_NAME)
        logger.info(f"Container '{CONTAINER_NAME}' found, running '{command}'...")
        container.exec_run(["/bin/sh", "rcon-cli", *command])
        logger.info(f"Command ran successfully.")

    except docker.errors.NotFound:
        logger.info(f"Container '{CONTAINER_NAME}' not found. Skipping the command '{command}'")
        pass

    except docker.errors.APIError as e:
        logger.critical(f"API error when trying to reach docker container '{CONTAINER_NAME}'. Check below for stack trace.\n")
        raise e

def backup():
    rcon_safe([r'tellraw @a {"text": "Server backing up; degraded performance possible", "color":"red"}'])

    # Flush all chunk writes
    rcon_safe(["save-off"])
    rcon_safe(["save-all"])

    time_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Hot copy files into tempotary directory
    temp_dir_name = "mc-backup-tempotary-" + time_iso
    temp_dir_path = PosixPath("/var/tmp") / temp_dir_name

    shutil.copytree(SERVER_DIRECTORY, temp_dir_path)

    # Enable saving since we copied out files into temp dir
    rcon_safe(["save-on"])

    backup_directory = BACKUPS_DIRECTORY / ("backup-" + time_iso)

    # COMPRESS!!!!!
    logger.info("Starting compression. This might take some time...")
    shutil.make_archive(str(backup_directory), "gztar", temp_dir_path)
    logger.info("Compression done.")

    rcon_safe([r'tellraw @a {"text": "Server backed up", "color":"red"}'])

    # Clean up the hot copied directory
    logger.info("Cleaning up tempotary directory")
    shutil.rmtree(temp_dir_path)
    
    logger.info("Done with everything")

if __name__ == "__main__":
    backup()