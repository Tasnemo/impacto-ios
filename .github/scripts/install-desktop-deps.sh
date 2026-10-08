#!/usr/bin/env bash
# Debian 12 / Ubuntu 24.04. Run as root (or with sudo).
set -euo pipefail
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates git python3 python3-venv ninja-build build-essential \
  nasm curl zip unzip pkg-config autoconf autoconf-archive automake libtool \
  libx11-dev libxft-dev libxext-dev libwayland-dev libxkbcommon-dev \
  libegl1-mesa-dev libibus-1.0-dev libxrandr-dev libltdl-dev libdrm-dev \
  libasound2-dev libpulse-dev libaudio-dev libfribidi-dev libjack-dev \
  libsndio-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libxtst-dev \
  libgbm-dev libgl1-mesa-dev libgles2-mesa-dev libdbus-1-dev libudev-dev \
  libthai-dev libusb-1.0-0-dev libpipewire-0.3-dev libdecor-0-dev liburing-dev \
  xvfb xauth mesa-utils libgl1-mesa-dri
