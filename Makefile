nuke-venv:
	rm -rf .venv
	
create-venv: nuke-venv
	python3 -m venv .venv

put-requirements:
	./.venv/bin/python -m pip freeze > requirements.txt

get-requirements:
	./.venv/bin/python -m pip install -r requirements.txt

cleanup-code-remains:
	sudo rm -r /var/tmp/mc-backup-tempotary*

nuke: nuke-venv

setup: create-venv get-requirements
	chmod +x ./scripts/*