#! /bin/bash

# TODO: extend the installation to other contexts

system_dependencies=("firefox" "python" "geckodriver")

venv_directory="$1"

if [[ "$venv_directory" ]]; then
    if [[ ! -d "$venv_directory" ]]; then
        echo "Invalid directory for the virtual environment"
        exit 1
    fi
else
    venv_directory="."
fi

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
    python -m venv "$venv_directory/.venv"
    source "$venv_directory/.venv/bin/activate"
    pip install .
    echo "Done."
else
    echo "Unsupported OS, you'll have to do it manually :("
fi
