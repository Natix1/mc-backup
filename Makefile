run:
	./.venv/bin/python backup.py
nuke-venv:
	rm -rf .venv
nuke-autorun:
	rm -f ./backup.sh
create-venv: nuke-venv
	python3 -m venv .venv
put-requirements:
	./.venv/bin/python -m pip freeze > requirements.txt
get-requirements:
	./.venv/bin/python -m pip install -r requirements.txt
create-autorun:
	echo "#!/bin/bash" > backup.sh
	echo "$(shell pwd)/.venv/bin/python backup.py" >> backup.sh
	chmod +x backup.sh
purge-tmp:
	sudo rm -r /var/tmp/mc-backup-tempotary*
nuke: nuke-venv nuke-autorun
setup: create-venv get-requirements create-autorun