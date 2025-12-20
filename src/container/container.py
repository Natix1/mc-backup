import os
import docker
import docker.errors

from dotenv import load_dotenv
from src.container.logger import logger
from pathlib import PosixPath

load_dotenv()


def getenv_assert(key: str) -> str:
    value = os.environ.get(key)
    if value is None:
        logger.critical(f"{key} not specified in environment")
        raise ValueError(f"{key} not specified in environment")

    return value


CONTAINER_NAME = getenv_assert("CONTAINER_NAME")
SERVER_DIRECTORY = PosixPath(getenv_assert("SERVER_DIRECTORY"))
BACKUPS_DIRECTORY = PosixPath(getenv_assert("BACKUPS_DIRECTORY"))
KEEP_LATEST = int(getenv_assert("KEEP_LATEST"))

docker_client = docker.from_env()


# Runs command via rcon-cli only if the docker container exists and is up. Optionally returns if the command ended up being executed fully
def rcon_safe(command: list[str]) -> bool:
    try:
        container = docker_client.containers.get(CONTAINER_NAME)
        if container.status != "running":
            logger.info(
                f"Container '{CONTAINER_NAME}' offline. Skipping command '{command}'"
            )
            return False

        logger.info(f"Container '{CONTAINER_NAME}' found, running '{command}'...")
        result = container.exec_run(["rcon-cli", *command])
        if result.exit_code != 0:
            errror_message = (
                "Non-0 exit after running command in docker. Remote output: "
                + result.output
            )
            logger.critical(errror_message)
            raise ValueError(errror_message)

        logger.info(f"Command ran successfully.")
        return True

    except docker.errors.NotFound:
        logger.info(
            f"Container '{CONTAINER_NAME}' not found. Skipping the command '{command}'"
        )
        return False

    except docker.errors.APIError as e:
        logger.critical(
            f"API error when trying to reach docker container '{CONTAINER_NAME}'. Check below for stack trace.\n"
        )
        return False


def get_container():
    return docker_client.containers.get(CONTAINER_NAME)
