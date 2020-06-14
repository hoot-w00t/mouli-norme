#!/bin/sh

INSTALL_PATH="/usr/local/bin/moulinorme"

echo "Uninstalling Moulinorme installed on $INSTALL_PATH ..."
sudo rm -f "$INSTALL_PATH"

echo "Done!"