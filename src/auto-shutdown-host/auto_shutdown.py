import logging
import os
import src.container.container as docker_container
import subprocess
import sys
import time

"""
Electricity is expensive. I often go to sleep earlier than some of my friends that want to keep playing on Kebabland.
If they log off at e.g 2 AM, then the host OS is running pointlessly for the next 4 hours.

Pair this with the auto-stop functionality in itzg/minecraft-server and you get exactly this process:
- Server shuts down after no players for X seconds
- This script detects when it shuts down and stops the host OS via shutdown now
"""

logging.basicConfig()
logger = logging.getLogger()

REFETCH_TIME = int(os.getenv("AUTO_SHUTDOWN_REFECH_TIME") or 10)

def is_container_running() -> bool:
    container = docker_container.get_container()
    return container.status == "running"

def main_loop():
    if os.geteuid() != 0:
        logger.critical("The auto shutdown script has to run as root. Try using sudo.")
        sys.exit(1)

    if not is_container_running():
        logger.critical("Tried to start auto shutdown when the container isn't currently running")
        return

    while True:
        if is_container_running():
            time.sleep(10)
            continue

        logger.info("Container stopped running; shutting down host os in 30 seconds...")
        time.sleep(10)

        subprocess.run(["shutdown", "now"])
        break

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Keyboard interrupt detected, shutting down safely...", flush=True, end="\n\n")