ifeq ($(OS),Windows_NT)
	VENVBIN := .venv/Scripts
else
	VENVBIN := .venv/bin
endif
PATH := $(VENVBIN):$(PATH)

.PHONY: update-requirements run clean docker all dev

all: 
	$(MAKE) -j2 --no-print-directory dev

dev: reload run

reload:
	websocketd --port=8080 watchexec -e js,css,html echo reload


update-requirements:
	python3 -m venv .venv
	$(VENVBIN)/pip freeze > requirements.txt

$(VENVBIN): requirements.txt
	python3 -m venv .venv
	$(VENVBIN)/pip install -Ur requirements.txt

run: $(VENVBIN)
	python main.py

clean:
	rm -rf .venv

test:
	rm cookies.txt
	./test.sh

prod: $(VENVBIN)/activate
	gunicorn --bind 0.0.0.0:5001 main:app
