#!/usr/bin/bash

dconf load /org/gnome/shell/ < "$2"/"$1".conf
