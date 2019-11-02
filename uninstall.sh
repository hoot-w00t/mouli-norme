#!/bin/sh

INSTALL_PATH="/usr/local/bin/moulinorme"
CONFIG_FOLDER="$HOME/.config/moulinorme"

echo "Uninstalling Moulinorme installed on $INSTALL_PATH ..."
sudo rm -f "$INSTALL_PATH"

echo "Deleting configuration in $CONFIG_FOLDER ..."
rm -r "$CONFIG_FOLDER/addons/"
rmdir "$CONFIG_FOLDER"

echo "Done!"