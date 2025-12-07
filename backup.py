import docker as docker
import docker.errors
import docker.types
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
KEEP_LATEST = int(getenv("KEEP_LATEST"))

docker_client = docker.from_env()

# Runs command via rcon-cli only if the docker container exists and is up. Optionally returns if the command ended up being executed fully
def rcon_safe(command: list[str]) -> bool:
    try:
        container = docker_client.containers.get(CONTAINER_NAME)
        logger.info(f"Container '{CONTAINER_NAME}' found, running '{command}'...")
        result = container.exec_run(["rcon-cli", *command])
        if result.exit_code != 0:
            errror_message = "Non-0 exit after running command in docker. Remote output: " + result.output
            logger.critical(errror_message)
            raise ValueError(errror_message)

        logger.info(f"Command ran successfully.")
        return True

    except docker.errors.NotFound:
        logger.info(f"Container '{CONTAINER_NAME}' not found. Skipping the command '{command}'")
        return False

    except docker.errors.APIError as e:
        logger.critical(f"API error when trying to reach docker container '{CONTAINER_NAME}'. Check below for stack trace.\n")
        return False

# Gives messsages a cool format
def announce_in_server(message: str):
    json_message = f'{{"text":"[SERVER] [CAPTAIN BACKUP] {message}","color":"blue"}}'
    rcon_safe(["tellraw", "@a", json_message])

def backup():
    announce_in_server("I, Captain Backup, came to protect. I will now copy files which can affect performance.")

    # Flush all chunk writes
    rcon_safe(["save-off"])
    rcon_safe(["save-all"])

    time_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y_%H_%M_%S")

    # Hot copy files into tempotary directory
    temp_dir_name = "mc-backup-tempotary-" + time_iso
    temp_dir_path = PosixPath("/var/tmp") / temp_dir_name

    shutil.copytree(SERVER_DIRECTORY, temp_dir_path)

    # Enable saving since we copied out files into temp dir
    rcon_safe(["save-on"])

    backup_directory = BACKUPS_DIRECTORY / ("backup-" + time_iso)

    # COMPRESS!!!!!
    announce_in_server("I, Captain backup, will start compressing the backup now (so that we dont run out of disk space). This can slow things down even more.")
    logger.info("Starting compression. This might take some time...")
    shutil.make_archive(str(backup_directory), "gztar", temp_dir_path)
    logger.info("Compression done.")

    # Clean up the hot copied directory
    logger.info("Cleaning up tempotary directory")
    shutil.rmtree(temp_dir_path)
    
    logger.info(f"Time to look for old backups to delete, will only keep {KEEP_LATEST} latest files")
    
    # Ok now we look for old files
    backups: list[PosixPath] = []

    for file in BACKUPS_DIRECTORY.iterdir():
        if not file.is_file():
            continue
        
        backups.append(file)

    def sort_key(file: PosixPath):
        return file.stat().st_mtime

    backups.sort(key=sort_key, reverse=True)
    for backup in backups[KEEP_LATEST:]:
        if not backup.is_file():
            continue

        logger.info(f"Removing file {backup.name}; too old, as rule configured to keep only latest {KEEP_LATEST} backups.")
        backup.unlink()

    logger.info("Done with everything")
    announce_in_server("I came, I saw, I concuered. And I've just mispelled 'conquered'. And I also wrote 'missspelled' wrong. Anyways. I'm done here. See you next time.")

if __name__ == "__main__":
    backup()