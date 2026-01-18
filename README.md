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

Run in wsl terminal to build (and run code)
```sh
./build/hello_vitals
```