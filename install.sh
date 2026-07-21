#!/bin/bash

USER_CONFIG_PATH="${HOME}/punisher_data/config"
MOONRAKER_CONFIG="${HOME}/punisher_data/config/moonraker.conf"
MOONRAKER_SERVICE_NAME="moonraker-punisher.service"
KLIPPER_PATH="${HOME}/klipper"
KLIPPER_VENV_PATH="${KLIPPER_VENV:-${HOME}/klippy-env}"
KLIPPER_SERVICE_NAME="klipper-punisher.service"

OLD_K_SHAKETUNE_VENV="${HOME}/klippain_shaketune-env"
K_SHAKETUNE_PATH="${HOME}/klippain_shaketune"

set -eu
export LC_ALL=C

function preflight_checks {
    if [ "$EUID" -eq 0 ]; then
        echo "[PRE-CHECK] This script must not be run as root!"
        exit 1
    fi

    # OS Identification check
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        case "${ID:-}" in
        debian | raspbian | ubuntu)
            echo "[PRE-CHECK] Detected supported OS: ${PRETTY_NAME:-$ID}"
            ;;
        *)
            echo "[ERROR] This installer only supports Debian-based systems (Debian, Raspbian, Ubuntu)."
            echo "[ERROR] Detected ID: ${ID:-unknown}"
            exit 1
            ;;
        esac
    else
        echo "[ERROR] Cannot determine OS distribution (/etc/os-release missing)."
        exit 1
    fi

    if ! command -v python3 &>/dev/null; then
        echo "[ERROR] Python 3 is not installed!"
        exit 1
    fi

    # Check if Klipper service file exists on system (even if currently stopped)
    if systemctl list-unit-files --type=service --no-legend | grep -Fq "${KLIPPER_SERVICE_NAME}"; then
        printf "[PRE-CHECK] Klipper service (%s) found! Continuing...\n\n" "${KLIPPER_SERVICE_NAME}"
    else
        echo "[ERROR] Klipper service '${KLIPPER_SERVICE_NAME}' not found!"
        exit 1
    fi

    install_package_requirements
}

function is_package_installed {
    dpkg -s "$1" &>/dev/null
    return $?
}

function install_package_requirements {
    # Added python3-dev and gfortran to guarantee scipy/numpy wheel builds succeed
    local packages=("libopenblas-dev" "python3-dev" "gfortran")
    local packages_to_install=()

    for package in "${packages[@]}"; do
        if is_package_installed "$package"; then
            echo "[INFO] $package is already installed"
        else
            packages_to_install+=("$package")
        fi
    done

    if [ "${#packages_to_install[@]}" -gt 0 ]; then
        echo "[INSTALL] Installing missing dependencies: ${packages_to_install[*]}"
        sudo apt update && sudo apt install -y "${packages_to_install[@]}"
    fi
}

function check_download {
    if [ ! -d "${K_SHAKETUNE_PATH}" ]; then
        echo "[DOWNLOAD] Downloading Klippain Shake&Tune module repository..."
        if git clone -b punisher --single-branch https://github.com/Bradford1040/kiauh-klippain-shaketune.git "${K_SHAKETUNE_PATH}"; then
            chmod +x "${K_SHAKETUNE_PATH}/install.sh"
            printf "[DOWNLOAD] Download complete!\n\n"
        else
            echo "[ERROR] Download of Klippain Shake&Tune git repository failed!"
            exit 1
        fi
    else
        printf "[DOWNLOAD] Klippain Shake&Tune repository found locally. Continuing...\n\n"
    fi
}

function setup_venv {
    if [ ! -d "${KLIPPER_VENV_PATH}" ]; then
        echo "[ERROR] Klipper Python virtual environment not found at ${KLIPPER_VENV_PATH}!"
        exit 1
    fi

    if [ -d "${OLD_K_SHAKETUNE_VENV}" ]; then
        echo "[INFO] Old K-Shake&Tune virtual environment found, cleaning it..."
        rm -rf "${OLD_K_SHAKETUNE_VENV}"
    fi

    # shellcheck source=/dev/null
    source "${KLIPPER_VENV_PATH}/bin/activate"
    echo "[SETUP] Installing/Updating Shake&Tune dependencies in Klipper venv..."
    pip install --upgrade pip
    pip install -r "${K_SHAKETUNE_PATH}/requirements.txt"
    deactivate
    printf "\n"
}

function link_extension {
    # Fixed rm -d to rm -rf so non-empty legacy macro folders are removed cleanly
    if [ -d "${HOME}/klippain_config" ] && [ -f "${USER_CONFIG_PATH}/.VERSION" ]; then
        if [ -d "${USER_CONFIG_PATH}/scripts/K-ShakeTune" ]; then
            echo "[INFO] Old K-Shake&Tune macro folder found, cleaning it..."
            rm -rf "${USER_CONFIG_PATH}/scripts/K-ShakeTune"
        fi
    else
        if [ -d "${USER_CONFIG_PATH}/K-ShakeTune" ]; then
            echo "[INFO] Old K-Shake&Tune macro folder found, cleaning it..."
            rm -rf "${USER_CONFIG_PATH}/K-ShakeTune"
        fi
    fi
}

function link_module {
    if [ ! -d "${KLIPPER_PATH}/klippy/extras/shaketune" ]; then
        echo "[INSTALL] Linking Shake&Tune module to Klipper extras..."
        ln -frsn "${K_SHAKETUNE_PATH}/shaketune" "${KLIPPER_PATH}/klippy/extras/shaketune"
    else
        printf "[INSTALL] Shake&Tune Klipper module is already linked. Continuing...\n\n"
    fi
}

function add_updater {
    if [ ! -f "$MOONRAKER_CONFIG" ]; then
        echo "[WARNING] Moonraker config not found at $MOONRAKER_CONFIG. Skipping update_manager setup."
        return 0
    fi

    update_section=$(grep -c '\[update_manager[a-z ]* Klippain-ShakeTune\]' "$MOONRAKER_CONFIG" || true)
    if [ "$update_section" -eq 0 ]; then
        echo "[INSTALL] Adding update manager section to moonraker.conf..."
        cat <<EOF >>"$MOONRAKER_CONFIG"

## Klippain Shake&Tune automatic update management
[update_manager Klippain-ShakeTune]
type: git_repo
origin: https://github.com/Bradford1040/kiauh-klippain-shaketune.git
path: ~/klippain_shaketune
virtualenv: ~/klippy-env
requirements: requirements.txt
system_dependencies: system-dependencies.json
primary_branch: punisher
managed_services: klipper moonraker
EOF
    fi
}

function restart_klipper {
    echo "[POST-INSTALL] Restarting Klipper service (${KLIPPER_SERVICE_NAME})..."
    sudo systemctl restart "${KLIPPER_SERVICE_NAME}"
}

function restart_moonraker {
    echo "[POST-INSTALL] Restarting Moonraker service (${MOONRAKER_SERVICE_NAME})..."
    sudo systemctl restart "${MOONRAKER_SERVICE_NAME}"
}

printf "\n=============================================\n"
echo "- Klippain Shake&Tune module install script -"
printf "=============================================\n\n"

# Execution flow
preflight_checks
check_download
setup_venv
link_extension
link_module
add_updater
restart_klipper
restart_moonraker

echo "[COMPLETE] Shake&Tune installation finished successfully!"
