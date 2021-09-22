#!/usr/bin/bash

echo $(loginctl show-session $(loginctl show-user $(whoami) -p Display --value) -p Type --value)
