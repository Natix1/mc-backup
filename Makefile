run:
	./venv/bin/python backup.py
nuke-venv:
	rm -rf .venv
create-venv: nuke-venv
	python3 -m venv .venv
put-requirements:
	python3 -m pip freeze > requirements.txt
get-requirements:
	python3 -m pip install -r requirements.txt
setup: create-venv get-requirements