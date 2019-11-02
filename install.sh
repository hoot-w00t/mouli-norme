#!/bin/sh

INSTALL_PATH="/usr/local/bin/moulinorme"
CONFIG_FOLDER="$HOME/.config/moulinorme"

echo "Installing Moulinorme on $INSTALL_PATH ..."
sudo cp moulinorme.py "$INSTALL_PATH"
sudo chown root:root "$INSTALL_PATH"
sudo chmod 755 "$INSTALL_PATH"

echo "Creating configuration on $CONFIG_FOLDER ..."
mkdir -p "$CONFIG_FOLDER/addons/"
cp ./addons/*.py "$CONFIG_FOLDER/addons/"
chmod 755 -R "$CONFIG_FOLDER/addons/"

echo "Done!"