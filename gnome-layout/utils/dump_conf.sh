#!/usr/bin/bash

dconf dump /org/gnome/shell/ > "$2"/"$1".conf
