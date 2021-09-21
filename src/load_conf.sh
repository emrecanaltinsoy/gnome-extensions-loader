#!/usr/bin/bash

dconf load /org/gnome/shell/ < /home/emrecan/.config/layouts/"$1".conf
