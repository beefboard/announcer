FROM python:3.7.0
RUN pip install pipenv

WORKDIR /announcer

COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy

COPY announcer announcer
COPY run.py run.py

ENTRYPOINT [ "python", "/announcer/run.py" ]
