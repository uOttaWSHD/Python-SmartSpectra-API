#!/usr/bin/env bash
set -e

apt update
apt install -y gpg curl

# Essential build tools and development libraries
apt update
apt install -y \
  build-essential \
  git \
  lsb-release \
  libcurl4-openssl-dev \
  libssl-dev \
  pkg-config \
  libv4l-dev \
  libgles2-mesa-dev \
  libunwind-dev \
  gpg \
  curl

# Install CMake 3.27.0
curl -L -o cmake-3.27.0-linux-x86_64.sh \
  https://github.com/Kitware/CMake/releases/download/v3.27.0/cmake-3.27.0-linux-x86_64.sh
chmod +x cmake-3.27.0-linux-x86_64.sh
./cmake-3.27.0-linux-x86_64.sh --skip-license --prefix=/usr/local

# Add Presage repository
curl -s "https://presage-security.github.io/PPA/KEY.gpg" \
  | gpg --dearmor \
  | tee /etc/apt/trusted.gpg.d/presage-technologies.gpg >/dev/null

curl -s --compressed \
  -o /etc/apt/sources.list.d/presage-technologies.list \
  "https://presage-security.github.io/PPA/presage-technologies.list"

# Install SmartSpectra SDK
apt update
apt install -y libsmartspectra-dev=2.0.4

