#FROM python:3.10-alpine
#
#RUN apk add libpq-dev gcc musl-dev libffi-dev
#
#WORKDIR /telegram_bot
#
#COPY requirements.txt .
#RUN pip install -r requirements.txt
#
#COPY . .
#
#ENV PYTHONPATH=/telegram_bot
#
#CMD ["python", "-m", "telegram_bot.telegram_bot"]


FROM python:3.10-alpine

RUN apk add libpq-dev gcc musl-dev libffi-dev

COPY requirements.txt requirements.txt

# Install Python dependencies
RUN python3 -m pip install -r requirements.txt

