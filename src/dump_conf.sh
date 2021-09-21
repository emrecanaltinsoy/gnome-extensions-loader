#!/usr/bin/bash

dconf dump /org/gnome/shell/ > /home/emrecan/.config/layouts/"$1".conf
