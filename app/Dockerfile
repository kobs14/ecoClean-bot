FROM python:3.10-alpine

RUN apk add libpq-dev gcc musl-dev libffi-dev

COPY requirements.txt requirements.txt

# Install Python dependencies
RUN python3 -m pip install -r requirements.txt


