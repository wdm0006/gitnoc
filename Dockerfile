FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /gitnoc

COPY requirements.txt /gitnoc/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /gitnoc

EXPOSE 5050

CMD ["python", "manage.py", "server-prod"]
