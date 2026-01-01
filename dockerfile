FROM python:3.12-slim

RUN apt update && \
  apt install -y python3-tk && \
  rm -rf /var/lib/apt/lists/* && \
  pip install --no-cache-dir numpy pillow customtkinter

COPY . /app
WORKDIR /app

CMD ["python", "-m", "core_modules.main"]
