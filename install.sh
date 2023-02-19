#! /bin/bash

system_dependencies=("firefox" "python" "python-pip" "geckodriver")

function detectOS(){
    local os=""
    if [[ "$OSTYPE" == "linux-gnu" ]]; then
        os=$(cat /etc/os-release | grep -m 1 "NAME" | cut -f 2 -d '=' | tr -d '"')
    else
        echo "Unsupported OS, you'll have to do it manually :("
        exit 1
    fi

    echo "$os"
}

function check_dependencies(){
    local -a dependencies_to_install
    for dependency in "$@"
    do
        if [[ $(pacman -Q "$dependency" | grep error) ]]; then
            dependencies_to_install+=("$dependency")
        fi
    done
    echo "${dependencies_to_install[@]}"
}

echo "Detecting OS..."
if [[ $(detectOS) == "Arch Linux" ]]; then
    echo "Checking system dependencies..."
    dependencies_to_install=$(check_dependencies "${system_dependencies[@]}")
    if [[ ${dependencies_to_install[@]} ]]; then
        echo "The following dependencies are missing: ${dependencies_to_install[@]}. Proceeding to install..."
        sudo pacman -S ${dependencies_to_install[@]}
    fi
    echo "Creating virtual environment for python and installing the package dependencies..."
    python -m venv venv
    source ./venv/bin/activate
    pip install build
    pip install -r requeriments.txt
    python -m build
    pip install "./dist/bolsar_scrapper-$(grep version pyproject.toml | grep -o '.\..\..')-py3-none-any.whl"
    echo "Done."
else
    echo "Unsupported OS, you'll have to do it manually :("
fi
