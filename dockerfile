FROM python:3.13-alpine

COPY . /app
WORKDIR /app

CMD ["python", "-m", "core_modules.main"]
