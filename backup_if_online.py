import backup

if __name__ == "__main__":
    exists = backup.rcon_safe(["help"])
    if exists:
        backup.backup()