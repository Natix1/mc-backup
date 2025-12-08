import docker as docker
import os
import shutil
import datetime
import src.container.container as docker_container

from src.container.logger import logger
from src.container.container import getenv_assert

"""
This allows me to backup my minecraft server, both when it's live and offline, by interacting with docker via the SDK.
It was originally made for the Kebabland minecraft server
"""

from dotenv import load_dotenv
from pathlib import PosixPath


CONTAINER_NAME = getenv_assert("CONTAINER_NAME")
SERVER_DIRECTORY = PosixPath(getenv_assert("SERVER_DIRECTORY"))
BACKUPS_DIRECTORY = PosixPath(getenv_assert("BACKUPS_DIRECTORY"))
KEEP_LATEST = int(getenv_assert("KEEP_LATEST"))

docker_client = docker.from_env()

# Gives messsages a cool format
def announce_in_server(message: str):
    json_message = f'{{"text":"[SERVER] [CAPTAIN BACKUP] {message}","color":"blue"}}'
    docker_container.rcon_safe(["tellraw", "@a", json_message])

def backup():
    announce_in_server("I, Captain Backup, came to protect. I will now copy files which can affect performance.")

    # Flush all chunk writes
    docker_container.rcon_safe(["save-off"])
    docker_container.rcon_safe(["save-all"])

    time_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y_%H_%M_%S")

    # Hot copy files into tempotary directory
    temp_dir_name = "mc-backup-tempotary-" + time_iso
    temp_dir_path = PosixPath("/var/tmp") / temp_dir_name

    shutil.copytree(SERVER_DIRECTORY, temp_dir_path)

    # Enable saving since we copied out files into temp dir
    docker_container.rcon_safe(["save-on"])

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