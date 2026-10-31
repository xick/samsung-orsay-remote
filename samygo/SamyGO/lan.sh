#!/bin/sh
cp "$1/SamyGO/samyGOso" /tmp/
cp "$1/SamyGO/libNetSwitch.so" /tmp/
chmod +x /tmp/samyGOso
/tmp/samyGOso -d -A -r -l /tmp/libNetSwitch.so WIRED
