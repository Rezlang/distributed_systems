#!/bin/bash

# Function to run a command in a new Terminal window
run_in_new_terminal() {
  command=$1
  osascript -e "tell application \"Terminal\" to do script \"cd '$PWD'; $command\""
}


# Run additional kv.py instances with command-line arguments
for arg in "$@"
do
  run_in_new_terminal "python3 kv.py $arg"
done