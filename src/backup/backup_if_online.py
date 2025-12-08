import src.backup.backup as backup
import src.container.container as docker_container

if __name__ == "__main__":
    exists = docker_container.rcon_safe(["help"])
    if exists:
        backup.backup()