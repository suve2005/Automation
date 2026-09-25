
FROM ubuntu:22.04


ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository -y ppa:kicad/kicad-8.0-releases \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    kicad \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    openjdk-21-jre \
    xvfb \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


RUN wget -O freerouting.jar "https://github.com/freerouting/freerouting/releases/download/v1.9.0/freerouting-1.9.0.jar"


COPY requirements.txt .
COPY server.py .


RUN pip3 install --ignore-installed -r requirements.txt

ENTRYPOINT ["python3", "-u", "server.py"]