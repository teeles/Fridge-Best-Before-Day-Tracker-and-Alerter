#!/bin/bash

###############################################
#  V1.0 - 19/05/2025
#  Thomas Eeles. 
#  Fridge Best Besfore Day Tracker and Alerter AKA FridgeWatch - Update Script
###############################################

##### Veriables ######
APP_DIR="/opt/fridgewatch"
updateURL="https://api.github.com/repos/teeles/Fridge-Best-Before-Day-Tracker-and-Alerter/releases/latest"
versionFromGit=$(curl --silent --fail "https://api.github.com/repos/teeles/Fridge-Best-Before-Day-Tracker-and-Alerter/releases/latest" | awk -F '"' '/tag_name/ { print $4; exit }' | sed 's/^[vV]//')
downloadURL=$(curl --silent --fail "https://api.github.com/repos/teeles/Fridge-Best-Before-Day-Tracker-and-Alerter/releases/latest" | awk -F '"' "/zipball_url\"/ { print \$4; exit }")
localversion=$( [[ -f "$APP_DIR/version.txt" ]] && head -n 1 "$APP_DIR/version.txt" | sed 's/^V//' || echo "0.0" )

##### FUNCTIONS #####

function version_compare () {
    local IFS=.
    local i ver1=($1) ver2=($2)

    # Pad the shorter version with zeros
    for ((i=${#ver1[@]}; i<3; i++)); do ver1[i]=0; done
    for ((i=${#ver2[@]}; i<3; i++)); do ver2[i]=0; done

    for ((i=0; i<3; i++)); do
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 0  # true: $1 >= $2
        elif ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 1  # false: $1 < $2
        fi
    done

    return 0  # equal
}

function downloadUPDATE () {
	local upgrade_dir="$APP_DIR/upgrades"
	local zip_path="$upgrade_dir/fridgewatch_latest.zip"

	if curl -L --fail -o "$zip_path" "$downloadURL"; then
        echo "Download complete: $zip_path"
    else
        echo "Failed to download update from GitHub."
        return 1
    fi

    if unzip -o "$zip_path" -d "$upgrade_dir" >/dev/null; then
        echo "Extracted to: $upgrade_dir"
    else
        echo "Failed to extract ZIP file."
        return 1
    fi

    rm -f "$zip_path"
    echo "Cleaned up zip archive."

    return 0
}

function upgrade () {
	local upgrade_dir="$APP_DIR/upgrades"
    local new_folder
    new_folder=$(find "$upgrade_dir" -maxdepth 1 -type d -name "teeles-*" | head -n 1)

     if [[ -z "$new_folder" ]]; then
        echo "No extracted folder found in $upgrade_dir."
        return 1
    fi

    echo "Comparing files from $new_folder to live app at $APP_DIR..."

    find "$new_folder" -type f | while read -r new_file; do
        rel_path="${new_file#$new_folder/}"

        # Exclusion rules
        if [[ "$rel_path" == db/* || "$rel_path" == backups/* || "$rel_path" == data/* || "$rel_path" == venv/* || "$rel_path" == log/* ]]; then
            echo "Skipping excluded path: $rel_path"
            continue
        fi

        live_file="$APP_DIR/$rel_path"

        if [[ -f "$live_file" ]]; then
            new_hash=$(sha256sum "$new_file" | awk '{print $1}')
            live_hash=$(sha256sum "$live_file" | awk '{print $1}')

            if [[ "$new_hash" != "$live_hash" ]]; then
                echo "✏Updating changed file: $rel_path"
                cp "$new_file" "$live_file"
            else
                echo "No change: $rel_path"
            fi
        else
            echo "Adding new file: $rel_path"
            mkdir -p "$(dirname "$live_file")"
            cp "$new_file" "$live_file"
        fi
    done

    echo "File sync complete."

}

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run the script using the 'sudo' command"
  exit 1
fi

# Ensure unzip is installed
if ! command -v unzip &>/dev/null; then
    echo "'unzip' not found. Installing..."
    apt update && apt install -y unzip || {
        echo "Failed to install 'unzip'. Exiting."
        exit 1
    }
fi

if version_compare "$localversion" "$versionFromGit"; then
    echo "This script is the latest V:$localversion"
    echo "no need to update anything"
    exit 1
else
    echo "This script is V:$localversion, a newer V$versionFromGit is available"
    echo "update will start now..."
fi

echo "turning Fridgewatch off so it can be update"

systemctl stop fridgewatch

echo "updating the OS, this may take a while..."

apt update && apt upgrade -y

echo "downloading the update version"

downloadUPDATE

echo "comparing the new version with the old version and updating all files"

upgrade

echo "re-starting Fridgewatch"

systemctl start fridgewatch

echo "Thats the update completed"

