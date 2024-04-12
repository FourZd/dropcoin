FROM python:3.11-slim-buster

WORKDIR /app

RUN apt-get update \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry

COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
    && poetry config installer.max-workers 10 \
    && poetry install --no-interaction --no-ansi

COPY . /app

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]