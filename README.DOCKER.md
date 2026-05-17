# Running Johnny-Voice-Assistant in Docker

This document explains how to run the project inside a Docker container. The app uses audio and GPIO hardware; containers need extra privileges and device access to work correctly on a Raspberry Pi.

Build the image:

```bash
docker build -t johnny-voice-assistant .
```

Run (recommended — with host networking and device access):

```bash
docker run -it --rm \
  --name johnny_raspi \
  --network host \
  --privileged \
  --device /dev/snd:/dev/snd \
  --device /dev/gpiomem:/dev/gpiomem \
  -v "$(pwd)/data:/opt/app/data" \
  -v "$(pwd)/configs:/opt/app/configs" \
  -e PYTHONUNBUFFERED=1 \
  johnny-voice-assistant
```

Or use `docker-compose` (already provided):

```bash
docker compose up --build
```

Notes and platform-specific considerations:
- Audio: the container maps `/dev/snd` and uses host audio devices; depending on your host you may need to adjust ALSA device indices or use PulseAudio socket mapping.
- GPIO: on Raspberry Pi, mapping `/dev/gpiomem` and running with `--privileged` usually allows access to GPIO from inside the container. Alternatively, use `--device /dev/gpiomem` without `--privileged`.
- Permissions: Docker must run as a user with permission to access host devices, or run with `sudo`.
- Network: host network mode makes audio/video device discovery and low-latency GPIO access easier.

If you want a less-privileged container, remove `--privileged` and add only the device mappings your setup requires; consult the Raspberry Pi documentation for secure device access.
