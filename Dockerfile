FROM node:20-alpine AS build-stage

WORKDIR /react-app
COPY react-app/package.json react-app/package-lock.json ./
RUN npm ci
COPY react-app/. .
RUN npm run build

FROM python:3.12-slim

ENV FLASK_APP=app \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /var/www

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt psycopg2-binary

COPY . .
COPY --from=build-stage /react-app/build/ react-app/build/

EXPOSE 8000
# Heroku and most hosts set $PORT; default to 8000.
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} app:app
