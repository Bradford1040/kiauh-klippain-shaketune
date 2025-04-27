#!/bin/bash

# --- Configuration ---
# Default paths (can be overridden by detection or command-line args)
DEFAULT_KLIPPER_PATH="${HOME}/klipper"
DEFAULT_KLIPPER_VENV_PATH="${HOME}/klippy-env"
DEFAULT_K_SHAKETUNE_PATH="${HOME}/klippain_shaketune" # Where to clone the repo
DEFAULT_REPO_URL="https://github.com/Bradford1040/kiauh-klippain-shaketune.git"
DEFAULT_REPO_BRANCH="punisher"

# Variables to be determined / selected
USER_CONFIG_PATH=""
MOONRAKER_CONFIG=""
MOONRAKER_SERVICE_NAME=""
KLIPPER_PATH=""
KLIPPER_VENV_PATH=""
KLIPPER_SERVICE_NAME=""
K_SHAKETUNE_PATH="" # This will hold the final path used
INSTANCE_NAME=""    # Will store the derived name like 'punisher' or 'able'

# --- Script Setup ---
set -euo pipefail
export LC_ALL=C
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # Should be K_SHAKETUNE_PATH if run from repo

# --- Helper Functions ---

function print_error {
    # Bold Red
    echo -e "\e[1;31m[ERROR] $1\e[0m" >&2
}

function print_warning {
    # Yellow
    echo -e "\e[0;33m[WARNING] $1\e[0m" >&2
}

function print_info {
    echo "[INFO] $1"
}

function print_notice {
    # Bold Blue
    printf "\n\e[1;34m>>> %s <<<\e[0m\n\n" "$1"
}

function print_success {
    # Bold Green
    echo -e "\e[1;32m[SUCCESS] $1\e[0m"
}

# Function to check if a package is installed
function is_package_installed {
    dpkg -s "$1" &> /dev/null
}

# --- Selection Function ---
function prompt_for_selection {
    local prompt_message="$1"
    shift
    local options=("$@")
    local choice

    if [[ ${#options[@]} -eq 0 ]]; then
        print_error "No options provided for selection: $prompt_message"
        return 1
    fi

    echo "$prompt_message"
    for i in "${!options[@]}"; do
        printf "  %d) %s\n" $((i + 1)) "${options[$i]}"
    done

    while true; do
        read -rp "Enter the number of your choice: " choice
        if [[ "$choice" =~ ^[0-9]+$ && "$choice" -ge 1 && "$choice" -le ${#options[@]} ]]; then
            # Return the selected option (adjust index)
            echo "${options[$((choice - 1))]}"
            return 0
        else
            print_warning "Invalid input. Please enter a number between 1 and ${#options[@]}."
        fi
    done
}


# --- Detection Functions ---

function find_potential_config_paths {
    local search_pattern="${HOME}/*_data/config" # Pattern for multi-instance setups
    local common_paths=(
        "${HOME}/printer_data/config"  # Standard single instance
        "${HOME}/klipper_config"       # Older/Manual fallback
    )
    local potential_paths=()
    local expanded_path

    print_info "Searching for Klipper configuration directories..."

    # Check common single-instance paths first
    for path in "${common_paths[@]}"; do
        expanded_path=$(eval echo "$path")
        if [[ -d "$expanded_path" && -f "$expanded_path/printer.cfg" ]]; then
            # Check if already found via pattern below to avoid duplicates
            if ! printf '%s\n' "${potential_paths[@]}" | grep -qxF "$expanded_path"; then
                print_info "Found common config directory: $expanded_path"
                potential_paths+=("$expanded_path")
            fi
        fi
    done

    # Check multi-instance pattern
    # Use find for potentially better handling of names, but globbing is simpler here
    # Need to handle cases where the glob finds nothing gracefully
    shopt -s nullglob # Prevent glob from returning the pattern itself if no match
    for path in $search_pattern; do
        if [[ -d "$path" && -f "$path/printer.cfg" ]]; then
            # Check if already found to avoid duplicates
            if ! printf '%s\n' "${potential_paths[@]}" | grep -qxF "$path"; then
                print_info "Found potential multi-instance config directory: $path"
                potential_paths+=("$path")
            fi
        fi
    done
    shopt -u nullglob # Turn off nullglob

    # Return the list (caller needs to capture it)
    # Use newline separation for easy parsing by the caller
    printf "%s\n" "${potential_paths[@]}"
}

function find_potential_services {
    local service_type="$1" # "klipper" or "moonraker"
    local potential_services_list=()

    print_info "Searching for potential ${service_type^} services..."
    # Use systemctl list-units to find potential services
    # Exclude template instances like klipper@.service
    # Use process substitution for cleaner reading into array
    while IFS= read -r service; do
        # Trim leading/trailing whitespace just in case
        service=$(echo "$service" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -n "$service" ]]; then
            potential_services_list+=("$service")
            print_info "Found potential service: $service"
        fi
    done < <(systemctl list-units --full -all -t service --no-legend | grep -Eio "^\s*(${service_type}[^@]*)\.service" | awk '{print $1}' | sort -u)

    # Return the list
    printf "%s\n" "${potential_services_list[@]}"
}

# --- Argument Parsing ---
function parse_arguments {
    local parsed_opts
    parsed_opts=$(getopt -o hv \
        -l help,config-path:,klipper-path:,venv-path:,klipper-service:,moonraker-service:,repo-path:,repo-url:,repo-branch: \
        -n "$0" -- "$@")

    if [[ $? -ne 0 ]]; then
        usage
        exit 1
    fi

    eval set -- "$parsed_opts"

    # Initialize variables with defaults or empty strings for detection/selection
    KLIPPER_PATH="$DEFAULT_KLIPPER_PATH"
    KLIPPER_VENV_PATH="" # Let KLIPPER_VENV env var take precedence if set
    K_SHAKETUNE_PATH="$DEFAULT_K_SHAKETUNE_PATH"
    local repo_url="$DEFAULT_REPO_URL"
    local repo_branch="$DEFAULT_REPO_BRANCH"
    # Config path and services will be determined or selected if not specified

    # Temporary holders for arguments
    local arg_config_path=""
    local arg_klipper_service=""
    local arg_moonraker_service=""

    while true; do
        case "$1" in
            -h | --help)
                usage
                exit 0
                ;;
            --config-path)
                arg_config_path="$2"
                shift 2
                ;;
            --klipper-path)
                KLIPPER_PATH="$2" # Allow override of core klipper path
                shift 2
                ;;
            --venv-path)
                KLIPPER_VENV_PATH="$2" # Allow override of core venv path
                shift 2
                ;;
            --klipper-service)
                arg_klipper_service="$2"
                shift 2
                ;;
            --moonraker-service)
                arg_moonraker_service="$2"
                shift 2
                ;;
            --repo-path)
                K_SHAKETUNE_PATH="$2"
                shift 2
                ;;
            --repo-url)
                repo_url="$2"
                shift 2
                ;;
            --repo-branch)
                repo_branch="$2"
                shift 2
                ;;
            --)
                shift
                break
                ;;
            *)
                print_error "Invalid argument: $1"
                usage
                exit 1
                ;;
        esac
    done

    # --- Post-Argument Processing and Detection/Selection ---

    # Set Klipper Venv Path (respect environment variable, then argument, then default relative to klipper path)
    KLIPPER_VENV_PATH="${KLIPPER_VENV:-${KLIPPER_VENV_PATH:-${KLIPPER_PATH}/../klippy-env}}"
    # Normalize the path
    KLIPPER_VENV_PATH=$(readlink -f "$KLIPPER_VENV_PATH")

    # 1. Determine Config Path
    if [[ -n "$arg_config_path" ]]; then
        USER_CONFIG_PATH=$(readlink -f "$arg_config_path") # Normalize user input
        print_info "Using user-specified config path: $USER_CONFIG_PATH"
        if [[ ! -d "$USER_CONFIG_PATH" || ! -f "$USER_CONFIG_PATH/printer.cfg" ]]; then
            print_error "Specified config path is not a valid Klipper config directory: $USER_CONFIG_PATH"
            exit 1
        fi
    else
        print_info "No config path specified, attempting detection..."
        local detected_paths_str
        detected_paths_str=$(find_potential_config_paths)
        local detected_paths=()
        # Read newline-separated string into array
        while IFS= read -r line; do [[ -n "$line" ]] && detected_paths+=("$line"); done <<< "$detected_paths_str"

        if [[ ${#detected_paths[@]} -eq 0 ]]; then
            print_error "Could not detect any Klipper configuration directory."
            print_error "Please ensure Klipper is set up or specify the path using --config-path."
            exit 1
        elif [[ ${#detected_paths[@]} -eq 1 ]]; then
            USER_CONFIG_PATH="${detected_paths[0]}"
            print_info "Automatically detected single config directory: $USER_CONFIG_PATH"
        else
            print_notice "Multiple Klipper configuration directories detected."
            local selected_path
            selected_path=$(prompt_for_selection "Please choose the configuration to install Shake&Tune for:" "${detected_paths[@]}")
            if [[ $? -ne 0 || -z "$selected_path" ]]; then
                print_error "No selection made. Exiting."
                exit 1
            fi
            USER_CONFIG_PATH="$selected_path"
            print_info "User selected config path: $USER_CONFIG_PATH"
        fi
    fi
    # Set Moonraker config path based on chosen config path
    MOONRAKER_CONFIG="${USER_CONFIG_PATH}/moonraker.conf"

    # Derive instance name from config path (e.g., /home/pi/punisher_data/config -> punisher)
    # This assumes a pattern like 'INSTANCE_data'
    local config_parent_dir
    config_parent_dir=$(basename "$(dirname "$USER_CONFIG_PATH")") # e.g., punisher_data
    if [[ "$config_parent_dir" == "printer_data" ]]; then
        INSTANCE_NAME="printer" # Default name for standard setup
    elif [[ "$config_parent_dir" == "klipper_config" ]]; then
        INSTANCE_NAME="klipper" # Name for fallback
    elif [[ "$config_parent_dir" == *_data ]]; then
        INSTANCE_NAME="${config_parent_dir%_data}" # Remove _data suffix
    else
        INSTANCE_NAME=$(basename "$USER_CONFIG_PATH") # Fallback to just the config dir name if pattern fails
    fi
    print_info "Derived instance name: $INSTANCE_NAME"


    # 2. Determine Klipper Service Name
    if [[ -n "$arg_klipper_service" ]]; then
        KLIPPER_SERVICE_NAME="$arg_klipper_service"
        print_info "Using user-specified Klipper service: $KLIPPER_SERVICE_NAME"
    else
        print_info "No Klipper service specified, attempting detection..."
        local klipper_services_str
        klipper_services_str=$(find_potential_services "klipper")
        local klipper_services=()
        while IFS= read -r line; do [[ -n "$line" ]] && klipper_services+=("$line"); done <<< "$klipper_services_str"

        local preferred_klipper_service="klipper-${INSTANCE_NAME}.service"
        local found_preferred=false
        for service in "${klipper_services[@]}"; do
            if [[ "$service" == "$preferred_klipper_service" ]]; then
                KLIPPER_SERVICE_NAME="$service"
                print_info "Automatically detected matching Klipper service: $KLIPPER_SERVICE_NAME"
                found_preferred=true
                break
            fi
        done

        if ! $found_preferred; then
            if [[ ${#klipper_services[@]} -eq 0 ]]; then
                print_warning "Could not detect any Klipper services. Assuming default 'klipper.service'."
                KLIPPER_SERVICE_NAME="klipper.service"
            elif [[ ${#klipper_services[@]} -eq 1 ]]; then
                KLIPPER_SERVICE_NAME="${klipper_services[0]}"
                print_info "Automatically detected single Klipper service: $KLIPPER_SERVICE_NAME"
            else
                print_notice "Multiple Klipper services detected, none matching '${preferred_klipper_service}'."
                local selected_service
                selected_service=$(prompt_for_selection "Please choose the Klipper service for instance '$INSTANCE_NAME':" "${klipper_services[@]}")
                if [[ $? -ne 0 || -z "$selected_service" ]]; then
                    print_error "No selection made. Exiting."
                    exit 1
                fi
                KLIPPER_SERVICE_NAME="$selected_service"
                print_info "User selected Klipper service: $KLIPPER_SERVICE_NAME"
            fi
        fi
    fi

    # 3. Determine Moonraker Service Name
    if [[ -n "$arg_moonraker_service" ]]; then
        MOONRAKER_SERVICE_NAME="$arg_moonraker_service"
        print_info "Using user-specified Moonraker service: $MOONRAKER_SERVICE_NAME"
    else
        print_info "No Moonraker service specified, attempting detection..."
        local moonraker_services_str
        moonraker_services_str=$(find_potential_services "moonraker")
        local moonraker_services=()
        while IFS= read -r line; do [[ -n "$line" ]] && moonraker_services+=("$line"); done <<< "$moonraker_services_str"

        local preferred_moonraker_service="moonraker-${INSTANCE_NAME}.service"
        local found_preferred=false
        for service in "${moonraker_services[@]}"; do
            if [[ "$service" == "$preferred_moonraker_service" ]]; then
                MOONRAKER_SERVICE_NAME="$service"
                print_info "Automatically detected matching Moonraker service: $MOONRAKER_SERVICE_NAME"
                found_preferred=true
                break
            fi
        done

        if ! $found_preferred; then
            if [[ ${#moonraker_services[@]} -eq 0 ]]; then
                print_warning "Could not detect any Moonraker services. Assuming default 'moonraker.service'."
                MOONRAKER_SERVICE_NAME="moonraker.service"
            elif [[ ${#moonraker_services[@]} -eq 1 ]]; then
                MOONRAKER_SERVICE_NAME="${moonraker_services[0]}"
                print_info "Automatically detected single Moonraker service: $MOONRAKER_SERVICE_NAME"
            else
                print_notice "Multiple Moonraker services detected, none matching '${preferred_moonraker_service}'."
                local selected_service
                selected_service=$(prompt_for_selection "Please choose the Moonraker service for instance '$INSTANCE_NAME':" "${moonraker_services[@]}")
                if [[ $? -ne 0 || -z "$selected_service" ]]; then
                    print_warning "No selection made. Proceeding without a confirmed Moonraker service."
                    MOONRAKER_SERVICE_NAME="" # Set to empty if user cancels/fails selection
                else
                    MOONRAKER_SERVICE_NAME="$selected_service"
                    print_info "User selected Moonraker service: $MOONRAKER_SERVICE_NAME"
                fi
            fi
        fi
    fi


    # Assign repo details to globals needed by check_download
    REPO_URL="$repo_url"
    REPO_BRANCH="$repo_branch"

    # Expand K_SHAKETUNE_PATH if it uses ~
    K_SHAKETUNE_PATH=$(eval echo "$K_SHAKETUNE_PATH")

    # --- Display Determined Configuration ---
    print_notice "Using the following configuration for instance '$INSTANCE_NAME':"
    echo "Klipper Core Path:    $KLIPPER_PATH"
    echo "Klipper Env Path:     $KLIPPER_VENV_PATH"
    echo "Klipper Service:      $KLIPPER_SERVICE_NAME"
    echo "Config Path:          $USER_CONFIG_PATH"
    echo "Moonraker Config:     $MOONRAKER_CONFIG"
    echo "Moonraker Service:    $MOONRAKER_SERVICE_NAME"
    echo "Shake&Tune Repo Path: $K_SHAKETUNE_PATH"
    echo "Shake&Tune Repo URL:  $REPO_URL"
    echo "Shake&Tune Branch:    $REPO_BRANCH"
    echo "-------------------------------------------"
    # Add a small pause for user to review
    read -rp "Press Enter to continue or Ctrl+C to abort..." -t 10 || true # Timeout after 10s

}

function usage {
    echo "Usage: $0 [options]"
    echo ""
    echo "Installs the Klippain Shake&Tune module for a specific Klipper instance."
    echo "If multiple Klipper instances are detected, you will be prompted to choose."
    echo ""
    echo "Options:"
    echo "  -h, --help                    Show this help message."
    echo "  --config-path <path>        Explicitly set the Klipper configuration directory path."
    echo "                                (e.g., ~/punisher_data/config). Bypasses detection/prompt."
    echo "  --klipper-path <path>       Path to the Klipper installation directory (core)."
    echo "                                Default: ${DEFAULT_KLIPPER_PATH}"
    echo "  --venv-path <path>          Path to the Klipper Python virtual environment (core)."
    echo "                                Default: \${KLIPPER_VENV} or ${DEFAULT_KLIPPER_VENV_PATH} or relative to klipper-path."
    echo "  --klipper-service <name>    Explicitly set the Klipper systemd service name."
    echo "                                (e.g., klipper-punisher.service). Bypasses detection/prompt."
    echo "  --moonraker-service <name>  Explicitly set the Moonraker systemd service name."
    echo "                                (e.g., moonraker-punisher.service). Bypasses detection/prompt."
    echo "  --repo-path <path>          Path where the Shake&Tune repository should be cloned."
    echo "                                Default: ${DEFAULT_K_SHAKETUNE_PATH}"
    echo "  --repo-url <url>            URL of the Shake&Tune git repository."
    echo "                                Default: ${DEFAULT_REPO_URL}"
    echo "  --repo-branch <branch>      Branch of the Shake&Tune repository to clone."
    echo "                                Default: ${DEFAULT_REPO_BRANCH}"
    echo ""
}


# --- Installation Steps ---

function preflight_checks {
    print_notice "Running Pre-flight Checks for instance '$INSTANCE_NAME'"
    if [[ "$EUID" -eq 0 ]]; then
        print_error "This script must not be run as root!"
        exit 1
    fi

    # Check essential commands
    local missing_cmds=()
    for cmd in python3 git pip systemctl sudo grep awk readlink basename dirname; do
        if ! command -v $cmd &> /dev/null; then
            missing_cmds+=("$cmd")
        fi
    done
    if [[ ${#missing_cmds[@]} -gt 0 ]]; then
        print_error "Missing essential commands: ${missing_cmds[*]}"
        print_error "Please install them (e.g., using 'sudo apt install git python3 python3-pip ...')."
        exit 1
    fi

    # Validate Klipper Core Path
    if [[ ! -d "$KLIPPER_PATH" || ! -f "$KLIPPER_PATH/klippy/klippy.py" ]]; then
        print_error "Klipper core installation not found at: $KLIPPER_PATH"
        print_error "Please verify the path or specify the correct one using --klipper-path."
        exit 1
    fi
    print_info "Klipper core installation found: $KLIPPER_PATH"

    # Validate Klipper Venv Path
    if [[ ! -d "$KLIPPER_VENV_PATH" || ! -f "$KLIPPER_VENV_PATH/bin/python" ]]; then
        print_error "Klipper virtual environment not found or invalid at: $KLIPPER_VENV_PATH"
        print_error "Please verify the path or specify the correct one using --venv-path."
        exit 1
    fi
    print_info "Klipper virtual environment found: $KLIPPER_VENV_PATH"

    # Validate Selected Klipper Service
    if [[ -z "$KLIPPER_SERVICE_NAME" ]]; then
        print_error "Klipper service name could not be determined. Please specify using --klipper-service."
        exit 1
    elif ! systemctl status "$KLIPPER_SERVICE_NAME" &> /dev/null; then
        print_error "Selected Klipper service '$KLIPPER_SERVICE_NAME' not found or inactive."
        print_error "Please ensure the service exists and is correct for instance '$INSTANCE_NAME'."
        print_error "Use --klipper-service to specify the correct name if detection/selection failed."
        exit 1
    fi
    print_info "Klipper service found: $KLIPPER_SERVICE_NAME"

    # Validate Selected Config Path (already checked during selection/arg parsing, but double check)
    if [[ ! -d "$USER_CONFIG_PATH" || ! -f "$USER_CONFIG_PATH/printer.cfg" ]]; then
        print_error "Selected Klipper configuration directory is invalid: $USER_CONFIG_PATH"
        exit 1
    fi
    print_info "Klipper configuration directory confirmed: $USER_CONFIG_PATH"

    # Validate Moonraker Config (Warning only)
    if [[ ! -f "$MOONRAKER_CONFIG" ]]; then
        print_warning "Moonraker configuration file not found: $MOONRAKER_CONFIG"
        print_warning "Update manager entry cannot be added automatically."
    else
        print_info "Moonraker configuration file found: $MOONRAKER_CONFIG"
    fi

    # Validate Selected Moonraker Service (Warning only, needed for restart and updater)
    if [[ -z "$MOONRAKER_SERVICE_NAME" ]]; then
        print_warning "Moonraker service name is unknown or was not selected."
        print_warning "Automatic restart and update manager configuration might fail or be incomplete."
    elif ! systemctl status "$MOONRAKER_SERVICE_NAME" &> /dev/null; then
        print_warning "Selected Moonraker service '$MOONRAKER_SERVICE_NAME' not found or inactive."
        print_warning "Automatic restart and update manager configuration might fail."
        print_warning "Use --moonraker-service if needed."
    else
        print_info "Moonraker service found: $MOONRAKER_SERVICE_NAME"
    fi

    install_package_requirements # Check system packages
    print_success "Pre-flight checks passed."
}

function install_package_requirements {
    # Dependencies required by numpy/scipy often used in shaketune
    local packages=("libopenblas-dev" "libatlas-base-dev" "gfortran")
    local packages_to_install=()
    local needs_update=false

    print_info "Checking system package requirements..."
    for package in "${packages[@]}"; do
        if ! is_package_installed "$package"; then
            print_info "Package '$package' not found."
            packages_to_install+=("$package")
            needs_update=true
        else
            print_info "Package '$package' is already installed."
        fi
    done

    if [[ ${#packages_to_install[@]} -gt 0 ]]; then
        print_notice "Installing missing system packages: ${packages_to_install[*]}"
        if [[ "$needs_update" = true ]]; then
            print_info "Updating package lists (sudo apt-get update)..."
            sudo apt-get update || { print_error "Failed to update package lists."; exit 1; }
        fi
        print_info "Installing packages (sudo apt-get install -y)..."
        sudo apt-get install -y "${packages_to_install[@]}" || { print_error "Failed to install system packages."; exit 1; }
        print_success "System packages installed successfully."
    else
        print_info "All required system packages are already installed."
    fi
}

function check_download {
    print_notice "Checking Shake&Tune Repository"
    local repo_dir_name repo_base_name
    repo_dir_name="$(dirname "${K_SHAKETUNE_PATH}")"
    repo_base_name="$(basename "${K_SHAKETUNE_PATH}")"

    # Ensure parent directory exists
    mkdir -p "$repo_dir_name" || { print_error "Failed to create directory: $repo_dir_name"; exit 1; }

    if [[ ! -d "${K_SHAKETUNE_PATH}/.git" ]]; then
        # --- Clone if directory doesn't exist or isn't a git repo ---
        print_info "Cloning Klippain Shake&Tune module repository..."
        print_info "Repo URL: $REPO_URL"
        print_info "Branch:   $REPO_BRANCH"
        print_info "Target:   $K_SHAKETUNE_PATH"
        # Use -c advice.detachedHead=false to suppress detached head warning on specific branch clone
        if git clone --depth 1 -c advice.detachedHead=false -b "$REPO_BRANCH" "$REPO_URL" "$K_SHAKETUNE_PATH"; then
            print_success "Download complete!"
        else
            print_error "Download of Klippain Shake&Tune module git repository failed!"
            exit 1
        fi
    else
        # --- Verify existing repository ---
        print_info "Klippain Shake&Tune module repository already found at ${K_SHAKETUNE_PATH}."
        local git_ok=true
        local current_url=""
        local current_branch=""
        local needs_fetch=false

        # Check remote URL ('origin')
        print_info "Verifying remote URL..."
        if ! current_url=$(git -C "${K_SHAKETUNE_PATH}" remote get-url origin 2>/dev/null); then
            print_warning "Could not get remote URL for 'origin'. Is the remote configured correctly?"
            # Allow proceeding but flag potential issue for update manager later
            git_ok=false
        elif [[ "$current_url" != "$REPO_URL" ]]; then
            print_warning "Existing repository remote URL ('$current_url') does not match expected URL ('$REPO_URL')."
            print_warning "Moonraker updates might fail or pull from the wrong source."
            git_ok=false
        else
            print_info "Remote URL matches expected: $current_url"
        fi

        # Check current branch
        print_info "Verifying current branch..."
        # Fetch remote branches info first to get accurate comparison, but don't pull yet
        # This helps if the local branch exists but doesn't track the remote one correctly yet.
        # Suppress output unless there's an error.
        if git -C "${K_SHAKETUNE_PATH}" fetch origin "$REPO_BRANCH" --quiet; then
            print_info "Fetched latest info for branch '$REPO_BRANCH' from origin."
        else
            print_warning "Could not fetch latest info for branch '$REPO_BRANCH' from origin. Branch may not exist remotely or network issue."
            # Don't necessarily set git_ok=false here, branch check below will handle it.
        fi

        # Get the currently checked-out branch name
        if ! current_branch=$(git -C "${K_SHAKETUNE_PATH}" rev-parse --abbrev-ref HEAD 2>/dev/null); then
            print_warning "Could not determine the current branch name."
            git_ok=false
        elif [[ "$current_branch" == "HEAD" ]]; then
            # Detached HEAD state - check if it points to the expected branch tip
            local current_commit head_commit_msg
            current_commit=$(git -C "${K_SHAKETUNE_PATH}" rev-parse HEAD)
            head_commit_msg="(Commit: ${current_commit:0:7})" # Short hash
            if git -C "${K_SHAKETUNE_PATH}" show-ref --verify --quiet "refs/remotes/origin/${REPO_BRANCH}"; then
                local remote_branch_commit
                remote_branch_commit=$(git -C "${K_SHAKETUNE_PATH}" rev-parse "refs/remotes/origin/${REPO_BRANCH}")
                if [[ "$current_commit" == "$remote_branch_commit" ]]; then
                    print_info "Repository is in 'detached HEAD' state, but points to the latest commit of '$REPO_BRANCH'."
                    # Technically okay for install, but updates won't work via 'git pull' on this state.
                    # We'll still offer checkout later if git_ok remains true otherwise.
                    needs_fetch=true # Mark that we might want to checkout the branch properly
                else
                    print_warning "Repository is in 'detached HEAD' state $head_commit_msg, not matching the tip of '$REPO_BRANCH'."
                    git_ok=false
                fi
            else
                print_warning "Repository is in 'detached HEAD' state $head_commit_msg. Cannot verify against expected branch '$REPO_BRANCH'."
                git_ok=false
            fi

        elif [[ "$current_branch" != "$REPO_BRANCH" ]]; then
            print_warning "Existing repository branch ('$current_branch') does not match expected branch ('$REPO_BRANCH')."
            # Offer to switch branch if URL is okay?
            local switch_choice
            if [[ "$current_url" == "$REPO_URL" ]]; then # Only offer if URL matches
                read -rp "Do you want to attempt to switch to branch '$REPO_BRANCH'? (y/N): " switch_choice
                if [[ "$switch_choice" =~ ^[Yy]$ ]]; then
                    print_info "Attempting to switch to branch '$REPO_BRANCH'..."
                    # Use checkout, assumes no major conflicting local changes
                    if git -C "${K_SHAKETUNE_PATH}" checkout "$REPO_BRANCH"; then
                        print_success "Switched to branch '$REPO_BRANCH'."
                        current_branch="$REPO_BRANCH" # Update for subsequent checks
                        # git_ok remains true if checkout succeeded
                    else
                        print_error "Failed to switch to branch '$REPO_BRANCH'. Please check manually."
                        git_ok=false
                    fi
                else
                    print_info "Keeping current branch '$current_branch'."
                    git_ok=false # Mark as not okay since it's not the expected branch
                fi
            else
                print_warning "Cannot offer branch switch due to remote URL mismatch."
                git_ok=false
            fi
        else
            print_info "Current branch matches expected: $current_branch"
            needs_fetch=true # Mark that we can potentially pull
        fi

        # --- Offer to update if configuration seems correct ---
        if $git_ok && $needs_fetch; then
            local pull_choice
            # If we were in detached HEAD but it matched, offer checkout first
            if [[ "$(git -C "${K_SHAKETUNE_PATH}" rev-parse --abbrev-ref HEAD)" == "HEAD" ]]; then
                read -rp "Repo is detached but matches branch tip. Check out branch '$REPO_BRANCH' for future updates? (y/N): " pull_choice
                if [[ "$pull_choice" =~ ^[Yy]$ ]]; then
                    if git -C "${K_SHAKETUNE_PATH}" checkout "$REPO_BRANCH"; then
                        print_success "Checked out branch '$REPO_BRANCH'."
                    else
                        print_error "Failed to checkout branch '$REPO_BRANCH'. Updates may require manual intervention."
                        needs_fetch=false # Cannot pull if checkout failed
                    fi
                else
                    print_info "Keeping detached HEAD state. Automatic updates via Moonraker might require manual setup."
                    needs_fetch=false # Don't offer pull on detached head
                fi
            fi

            # Offer pull if we are on the correct branch (or just checked it out)
            if $needs_fetch; then
                read -rp "Repository configuration seems correct. Do you want to attempt to update it with 'git pull'? (y/N): " pull_choice
                if [[ "$pull_choice" =~ ^[Yy]$ ]]; then
                    print_info "Attempting to update repository with 'git pull'..."
                    # Pull on the correct branch
                    if git -C "${K_SHAKETUNE_PATH}" pull --ff-only; then # Use --ff-only for safety? Or allow merge? Let's try ff-only first.
                        print_success "Repository updated successfully (fast-forward)."
                    else
                        # Try regular pull if ff-only failed (might need merge)
                        print_warning "Fast-forward pull failed. Attempting a standard pull (may require merge)..."
                        if git -C "${K_SHAKETUNE_PATH}" pull; then
                                print_success "Repository updated successfully."
                        else
                                print_warning "Failed to update repository with 'git pull'. Please check manually (e.g., for conflicts)."
                        fi
                    fi
                else
                    print_info "Skipping repository update."
                fi
            fi
        elif ! $git_ok; then
            # Mismatch found and not resolved by user action (like branch switch)
            print_warning "The existing repository at ${K_SHAKETUNE_PATH} does not fully match the expected configuration (URL/Branch)."
            print_warning "Please resolve this manually or remove the directory '${K_SHAKETUNE_PATH}' and re-run the script to clone fresh."
            print_warning "Proceeding with installation using the existing repository, but Moonraker updates might not work correctly."
        fi
    fi

    # Ensure the script we are running from is the one in the repo path if possible
    # (This check remains the same)
    if [[ "$SCRIPT_DIR" != "$K_SHAKETUNE_PATH" ]]; then
        print_warning "Running script from $SCRIPT_DIR, but repository is at $K_SHAKETUNE_PATH."
        print_warning "Ensure requirements.txt path is correct for subsequent steps."
    fi
}

function setup_venv {
    print_notice "Setting up Python Virtual Environment Dependencies"
    # Venv path validity checked in preflight_checks

    # Clean up very old venv path if it exists (less relevant now, but keep for safety)
    local old_k_shaketune_venv="${HOME}/klippain_shaketune-env"
    if [[ -d "${old_k_shaketune_venv}" ]]; then
        print_info "Old K-Shake&Tune virtual environment found at ${old_k_shaketune_venv}, removing it."
        rm -rf "${old_k_shaketune_venv}"
    fi

    local requirements_file="${K_SHAKETUNE_PATH}/requirements.txt"
    if [[ ! -f "$requirements_file" ]]; then
        print_error "Cannot find requirements file: $requirements_file"
        exit 1
    fi

    print_info "Activating Klipper virtual environment: ${KLIPPER_VENV_PATH}"
    # shellcheck source=/dev/null
    source "${KLIPPER_VENV_PATH}/bin/activate"

    print_info "Upgrading pip..."
    # Use python -m pip for consistency
    python -m pip install --upgrade pip || { print_error "Failed to upgrade pip."; deactivate; exit 1; }

    print_info "Installing/Updating K-Shake&Tune dependencies from ${requirements_file}..."
    # Consider adding --no-cache-dir if issues arise
    python -m pip install -r "${requirements_file}" || { print_error "Failed to install dependencies from requirements.txt."; deactivate; exit 1; }

    print_info "Deactivating virtual environment."
    deactivate
    print_success "Virtual environment setup complete."
}

function link_extension {
    # This function cleans up old macro links specific to the *selected* config path.
    print_notice "Cleaning Up Old Macro Links (if any) in $USER_CONFIG_PATH"

    # Check for Klippain structure first (using .VERSION file as indicator)
    # Note: Klippain structure might be in ~/klippain_config, not necessarily related to INSTANCE_NAME
    # Let's simplify and just check within the selected USER_CONFIG_PATH
    local old_macro_path_scripts="${USER_CONFIG_PATH}/scripts/K-ShakeTune"
    local old_macro_path_root="${USER_CONFIG_PATH}/K-ShakeTune"

    if [[ -e "$old_macro_path_scripts" ]]; then # Check if file/dir/link exists
        print_info "Old K-Shake&Tune item found in scripts/, removing it: $old_macro_path_scripts"
        rm -rf "$old_macro_path_scripts"
    else
        print_info "No old K-Shake&Tune item found in scripts/."
    fi

    if [[ -e "$old_macro_path_root" ]]; then # Check if file/dir/link exists
        print_info "Old K-Shake&Tune item found in config root, removing it: $old_macro_path_root"
        rm -rf "$old_macro_path_root"
    else
        print_info "No old K-Shake&Tune item found in config root."
    fi

    print_success "Old macro link cleanup finished for $USER_CONFIG_PATH."
}

function link_module {
    # This links the single source install into the *core* Klipper extras directory.
    # This is done only once, regardless of how many instances use it.
    print_notice "Linking Shake&Tune Module to Klipper Core Extras"
    local target_link="${KLIPPER_PATH}/klippy/extras/shaketune"
    local source_dir="${K_SHAKETUNE_PATH}/shaketune" # The actual module code

    if [[ ! -d "$source_dir" ]]; then
        print_error "Shake&Tune source directory not found: $source_dir"
        print_error "Please check the repository structure in $K_SHAKETUNE_PATH."
        exit 1
    fi

    # Check if the link already exists and points to the correct place
    local current_link_target=""
    if [[ -L "$target_link" ]]; then
        current_link_target=$(readlink -f "$target_link")
    fi
    local expected_target
    expected_target=$(readlink -f "$source_dir") # Get absolute path

    if [[ -L "$target_link" && "$current_link_target" == "$expected_target" ]]; then
        print_info "Shake&Tune module already correctly linked in Klipper core."
    elif [[ -e "$target_link" ]]; then
        # It exists but is wrong (or not a link)
        print_warning "Existing file/directory/link found at $target_link. Removing it."
        # Try without sudo first, Klipper dir is often user-owned
        rm -rf "$target_link" || {
            print_warning "Failed to remove existing item (will try with sudo): $target_link"
            sudo rm -rf "$target_link" || { print_error "Failed to remove existing item at $target_link even with sudo. Check permissions."; exit 1; }
        }
        print_info "Linking Shake&Tune module to Klipper extras..."
        ln -sf "$source_dir" "$target_link" || { print_error "Failed to create symbolic link. Check permissions."; exit 1; }
        print_success "Link created successfully."
    else
        # Link doesn't exist
        print_info "Linking Shake&Tune module to Klipper extras..."
        ln -sf "$source_dir" "$target_link" || { print_error "Failed to create symbolic link. Check permissions."; exit 1; }
        print_success "Link created successfully."
    fi
}

function add_updater {
    # Adds an update manager section to the *selected* instance's moonraker.conf
    print_notice "Configuring Moonraker Update Manager for instance '$INSTANCE_NAME'"
    if [[ ! -f "$MOONRAKER_CONFIG" ]]; then
        print_warning "Moonraker config file not found ($MOONRAKER_CONFIG). Cannot add update manager entry."
        return
    fi

    # Use a unique identifier including the instance name
    local update_section_name="Klippain-ShakeTune-${INSTANCE_NAME}"
    local update_section_header="[update_manager ${update_section_name}]"

    # Check if the specific section already exists
    # Use grep -qF for fixed string matching, -x for whole line match might be safer if format is strict
    if grep -qF "$update_section_header" "$MOONRAKER_CONFIG"; then
        print_info "Update manager section '$update_section_name' already exists in $MOONRAKER_CONFIG."
        # Optional: Add logic to check/update existing entry if needed
        # Could compare existing path/branch/etc. and update if necessary
    else
        print_info "Adding update manager section '$update_section_name' to $MOONRAKER_CONFIG..."
        # Use relative paths from HOME in the config file where possible
        # Need to handle paths outside HOME gracefully (use absolute then)
        local config_repo_path
        if [[ "$K_SHAKETUNE_PATH" == "$HOME/"* ]]; then
            config_repo_path="~/${K_SHAKETUNE_PATH#$HOME/}"
        else
            config_repo_path="$K_SHAKETUNE_PATH" # Use absolute if not in HOME
        fi

        local config_venv_path
        if [[ "$KLIPPER_VENV_PATH" == "$HOME/"* ]]; then
            config_venv_path="~/${KLIPPER_VENV_PATH#$HOME/}"
        else
            config_venv_path="$KLIPPER_VENV_PATH" # Use absolute if not in HOME
        fi

        # Include the specific Klipper service for this instance
        # Moonraker service is implicitly managed if moonraker itself is restarted by the update
        local managed_services="$KLIPPER_SERVICE_NAME" # Always manage the specific klipper instance

        # Append the configuration block
        # Use printf for better control over formatting and variable expansion
        # Add a comment clearly indicating which instance this is for
        printf "\n%s\n" \
            "## Klippain Shake&Tune automatic update management for instance '${INSTANCE_NAME}' (${K_SHAKETUNE_PATH})" \
            "${update_section_header}" \
            "type: git_repo" \
            "origin: ${REPO_URL}" \
            "path: ${config_repo_path}" \
            "virtualenv: ${config_venv_path}" \
            "requirements: requirements.txt" \
            "# system_dependencies: system-dependencies.json # Add if you have this file" \
            "primary_branch: ${REPO_BRANCH}" \
            "managed_services: ${managed_services}" \
            "" >> "$MOONRAKER_CONFIG" || { print_error "Failed to write to $MOONRAKER_CONFIG. Check permissions."; exit 1; }

        print_success "Update manager section added."
        NEEDS_MOONRAKER_RESTART=true # Flag that moonraker needs restart
    fi
}

function restart_klipper {
    print_notice "Restarting Klipper Service for instance '$INSTANCE_NAME'"
    if [[ -z "$KLIPPER_SERVICE_NAME" ]]; then
        # This should have been caught in preflight, but double check
        print_error "Klipper service name unknown. Cannot restart."
        return
    fi
    print_info "Executing: sudo systemctl restart ${KLIPPER_SERVICE_NAME}"
    if sudo systemctl restart "${KLIPPER_SERVICE_NAME}"; then
        print_success "Klipper service '${KLIPPER_SERVICE_NAME}' restarted successfully."
    else
        print_error "Failed to restart Klipper service: ${KLIPPER_SERVICE_NAME}"
        # Don't exit, maybe user can restart manually
    fi
}

function restart_moonraker {
    # Only restart if needed (e.g., updater added)
    if [[ "${NEEDS_MOONRAKER_RESTART:-false}" != true ]]; then
        print_info "Moonraker restart not required for this operation."
        return
    fi

    print_notice "Restarting Moonraker Service for instance '$INSTANCE_NAME'"
    if [[ -z "$MOONRAKER_SERVICE_NAME" ]]; then
        print_warning "Moonraker service name unknown or not selected. Skipping restart."
        print_warning "Please restart it manually if needed: sudo systemctl restart <your-moonraker-service>"
        return
    fi
    print_info "Executing: sudo systemctl restart ${MOONRAKER_SERVICE_NAME}"
    if sudo systemctl restart "${MOONRAKER_SERVICE_NAME}"; then
        print_success "Moonraker service '${MOONRAKER_SERVICE_NAME}' restarted successfully."
    else
        print_error "Failed to restart Moonraker service: ${MOONRAKER_SERVICE_NAME}"
    fi
}

# --- Main Execution ---
function main {
    printf "\n\e[1;36m=============================================\n"
    echo "- Klippain Shake&Tune Module Install Script -"
    printf "=============================================\e[0m\n\n"

    # Initialize flag
    NEEDS_MOONRAKER_RESTART=false

    parse_arguments "$@"
    preflight_checks
    check_download
    setup_venv
    link_extension # Cleanup old links in the selected config dir
    link_module    # Create/verify the single link in klipper core extras
    add_updater    # Add updater section to the selected moonraker.conf
    restart_klipper # Restart the selected klipper service
    restart_moonraker # Restart the selected moonraker service (if needed)

    print_notice "Klippain Shake&Tune Installation Complete for instance '$INSTANCE_NAME'!"
    print_success "The core module is linked into Klipper."
    echo "Please ensure your Klipper configuration ('${USER_CONFIG_PATH}/printer.cfg')"
    echo "includes '[shaketune]' to enable the module for this instance."
    echo "Refer to the Klippain Shake&Tune documentation for configuration details."
    printf "\n\e[1;36m=============================================\e[0m\n\n"
}

# Run main function
main "$@"

exit 0
