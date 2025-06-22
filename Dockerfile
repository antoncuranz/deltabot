FROM --platform=linux/amd64 python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    firefox-esr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN GECKODRIVER_VERSION=0.36.0 && \
    wget https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -xzf geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["python", "main.py"]
