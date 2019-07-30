#!/bin/bash
# download and install latest geckodriver for linux or mac.
# required for selenium to drive a firefox browser.

# command -v geckodriver >/dev/null 2>&1 || { echo >&2 "Geckodriver already installed. Aborting."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo >&2 "I require curl but it's not installed.\nInstall curl:\n\n"; exit sudo pacman -Syu curl; }
command -v jq >/dev/null 2>&1 || { echo >&2 "I require jq but it's not installed.\nInstall jq:\n\n"; sudo pacman -Syu jq; }

install_dir="/usr/local/bin"
json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
if [[ $(uname) == "Darwin" ]]; then
    url=$(echo "$json" | jq -r '.assets[].browser_download_url | select(contains("macos"))')
elif [[ $(uname) == "Linux" ]]; then
    url=$(echo "$json" | jq -r '.assets[].browser_download_url | select(contains("linux64"))')
else
    echo "can't determine OS"
    exit 1
fi
curl -s -L "$url" | tar -xz
chmod +x geckodriver
sudo mv geckodriver "$install_dir"

install_file="/geckodriver"
if test -f "$install_dir$install_file"; then
	echo "installed geckodriver binary in $install_dir"
else
	echo "something went wrong"
fi
