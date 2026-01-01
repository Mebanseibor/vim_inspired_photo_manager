FROM python:3.12-alpine

COPY . /app
WORKDIR /app

RUN pip install numpy pillow && \
  apk add python3-tkinter

CMD ["python", "-m", "core_modules.main"]
