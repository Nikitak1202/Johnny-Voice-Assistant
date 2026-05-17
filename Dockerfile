FROM python:3.11-slim

# Minimal system deps commonly needed by audio, imaging and GPIO libraries.
RUN apt-get update \
     && apt-get install -y --no-install-recommends \
         build-essential \
         gcc \
         portaudio19-dev \
         libffi-dev \
         libsndfile1 \
         mpg123 \
         ffmpeg \
         flac \
         alsa-utils \
         libopenjp2-7 \
         libjpeg-dev \
     && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
WORKDIR /opt/app

# Copy only requirements first for better caching
COPY requirements.txt /opt/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /opt/app

# Ensure run script is executable
RUN chmod +x /opt/app/scripts/run.sh

CMD ["/opt/app/scripts/run.sh"]
