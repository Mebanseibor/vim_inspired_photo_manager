FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

RUN apt update && \
  apt install -y python3-tk && \
  rm -rf /var/lib/apt/lists/* && \
  pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "core_modules.main"]
