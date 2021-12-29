from python:3.9.9-slim-buster
run apt-get update && apt-get install --yes make
workdir /app
copy . /app
run make .venv/bin
expose 8000
cmd ["make", "prod"]
