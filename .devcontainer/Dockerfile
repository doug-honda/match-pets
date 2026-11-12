# Ambiente do Match Pets no GitHub Codespaces: Python com as dependências já instaladas.
FROM mcr.microsoft.com/devcontainers/python:3.12

COPY backend/requirements.txt backend/requirements-dev.txt /tmp/dependencias/
RUN pip install --no-cache-dir -r /tmp/dependencias/requirements-dev.txt
