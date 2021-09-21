#!/usr/bin/bash

mkdir -p ~/.local/share/gnome-shell/extensions/"$1"

cd ~/.local/share/gnome-shell/extensions/"$1"

unzip -qo ~/.config/layouts/extensions/"$1" -d ~/.local/share/gnome-shell/extensions/"$1"/

# rm ~/.config/layouts/extensions/"$1"

gnome-extensions enable "$1"

echo "$1 installed"
