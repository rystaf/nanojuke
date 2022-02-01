ifeq ($(OS),Windows_NT)
	VENVBIN := .venv/Scripts
else
	VENVBIN := .venv/bin
endif
PATH := $(VENVBIN):$(PATH)

.PHONY: update-requirements run prod

all: 
	$(MAKE) -j2 --no-print-directory dev

dev: reload run

reload:
	websocketd --port=8080 watchexec -e js,css,html echo reload

update-requirements: $(VENVBIN)
	$(VENVBIN)/pip freeze > requirements.txt

$(VENVBIN): requirements.txt
	python3 -m venv .venv
	$(VENVBIN)/pip install -Ur requirements.txt

run: $(VENVBIN)
	python3 main.py

prod: $(VENVBIN)
	gunicorn --bind 0.0.0.0:8000 main:app
