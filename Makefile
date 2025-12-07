run:
	./venv/bin/python backup.py
nuke-venv:
	rm -rf .venv
create-venv: nuke-venv
	./venv/bin/python -m venv .venv
put-requirements:
	./venv/bin/python -m pip freeze > requirements.txt
get-requirements:
	./venv/bin/python -m pip install -r requirements.txt
setup: create-venv get-requirements