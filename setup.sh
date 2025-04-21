#!/bin/bash

###############################################
#  V1.0 - 21/5/2025
#  Thomas Eeles. 
#  Fridge Best Besfore Day Tracker and Alerter AKA FridgeWatch - Setup Script
###############################################

#### Variables ####

#### Functions ####

#### THE SCRIPT ####

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run the script using the 'sudo' command"
  exit 1
fi

echo "This will setup FridgeWatch running on Port 80"
echo "Updating the OS"

apt update && apt upgrade -y


