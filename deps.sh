#! /bin/bash

install_pip=0

detectOS(){
    local os=""
    if [[ "$OSTYPE" == "linux-gnu" ]]; then
        os=$(cat /etc/os-release | grep -m 1 "NAME" | cut -f 2 -d '=' | tr -d '"')
    else
        echo "Unsupported OS, you'll have to do it manually :("
        exit 1
    fi

    echo "$os"
}

echo "Checking dependencies..."
if [[ ! -x $(command -v pip) ]]; then
    install_pip=1
fi

echo "Detecting OS..."
if [[ $(detectOS) == "Arch Linux" ]]; then
    echo "Installing dependencies, selenium and the WebDriver..."
    if [[ $install_pip -eq 1 ]]; then
        sudo pacman -S python-pip
    fi
    sudo pacman -S geckodriver
    pip install selenium
else
    echo "Unsupported OS, you'll have to do it manually :("
fi
