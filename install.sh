#!/bin/sh

INSTALL_PATH="/usr/local/bin/moulinorme"

echo "Installing Moulinorme on $INSTALL_PATH ..."
sudo cp moulinorme.py "$INSTALL_PATH"
sudo chown root:root "$INSTALL_PATH"
sudo chmod 755 "$INSTALL_PATH"

echo "Done!"