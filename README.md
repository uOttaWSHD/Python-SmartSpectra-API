## Presage SmartSpectra API - Python

Indirect API queries with python
See the python reference code (main.py) for how to use.

## How it works
1. Python code stores the video locally
2. Python code writes the video path to data/input.json
3. Python builds and executes C++ file through the terminal
4. C++ Code builds and executes
   - Reads the video path from data/input.json
   - Calls SmartSpectra API on the video at the specified path
   - Writes breathing and pulse in BPM to terminal (not returned)
   - Plays the video with visualizations from Presage (not returned)
   - Writes the returned info to data/output.json in the form {"breathing": [], "pulse": [], "timestamp": []}
       - Each key contains an array of the same size equal to the number of timestamps
       - Breathing and pulse may be null for some values but not timestamp
       - Breathing in (breaths / minute), pulse in (beats / minute)
5. C++ Code ends

## Installation

install tools needed to add the Presage repository:

```shell
sudo apt update
sudo apt install gpg curl
```

To compile C++ applications that use the SmartSpectra SDK, you need the complete development environment:

```shell
# Essential build tools and development libraries
sudo apt update
sudo apt install -y build-essential git lsb-release libcurl4-openssl-dev libssl-dev pkg-config libv4l-dev libgles2-mesa-dev libunwind-dev gpg curl

# Install CMake 3.27.0 or newer
curl -L -o cmake-3.27.0-linux-x86_64.sh https://github.com/Kitware/CMake/releases/download/v3.27.0/cmake-3.27.0-linux-x86_64.sh
chmod +x cmake-3.27.0-linux-x86_64.sh
sudo ./cmake-3.27.0-linux-x86_64.sh --skip-license --prefix=/usr/local
```

Add Presage repository

```shell
curl -s "https://presage-security.github.io/PPA/KEY.gpg" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/presage-technologies.gpg >/dev/null
sudo curl -s --compressed -o /etc/apt/sources.list.d/presage-technologies.list "https://presage-security.github.io/PPA/presage-technologies.list"
```

Install SDK (Ubuntu 22.04/Mint 21)

```sh
sudo apt update
sudo apt install libsmartspectra-dev=2.0.4
```

#### Get API Key
Obtain your free API key from <https://physiology.presagetech.com>

## Test C++ Code

```sh
./build/hello_vitals
```

## Dates
Created 2026, Jan 17
Last Updated 2026, Jan 18
