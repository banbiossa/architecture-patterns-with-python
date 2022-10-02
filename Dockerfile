FROM python:3.9

# RUN apt install gcc libpq (no longer needed bc we use psycopg2-binary)

WORKDIR /app

COPY poetry.lock pyproject.toml ./
COPY domain_modelling ./domain_modelling
COPY tests ./tests

ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install poetry

RUN poetry install --no-dev

ENV FLASK_APP=domain_modelling/entrypoints/flask_app.py
ENV FLASK_DEBUG=1
ENV PYTHONBUFFERED=1

ENTRYPOINT ["poetry", "run", "flask", "run"]
CMD ["--host=0.0.0.0", "--port=80"]
