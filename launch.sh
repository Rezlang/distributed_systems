#!/bin/bash

# Close all existing Terminal windows
# osascript -e 'tell application "Terminal" to quit'
pkill Terminal

# Function to run a command in a new Terminal window
run_in_new_terminal() {
  command=$1
  osascript -e "tell application \"Terminal\" to do script \"cd '$PWD'; $command\""
}

# Run the initial commands
run_in_new_terminal "python3 view.py view"
run_in_new_terminal "python3 client.py client1"
run_in_new_terminal "python3 kv.py alpha"

# Run additional kv.py instances with command-line arguments
for arg in "$@"
do
  run_in_new_terminal "python3 kv.py $arg"
done

# Rearrange the windows
osascript <<EOF
tell application "Terminal"
  activate
  set windowList to every window
  set windowCount to count of windowList

  if windowCount ≥ 1 then
    set the bounds of window 1 to {0, 23, 720, 461} -- Top Left
  end if
  if windowCount ≥ 2 then
    set the bounds of window 2 to {720, 23, 1440, 461} -- Top Right
  end if
  if windowCount ≥ 3 then
    set the bounds of window 3 to {0, 461, 720, 900} -- Bottom Left
  end if
  if windowCount ≥ 4 then
    set the bounds of window 4 to {720, 461, 1440, 900} -- Bottom Right
  end if
  if windowCount ≥ 5 then
    set the bounds of window 5 to {360, 230, 1080, 692} -- Center
    set index of window 5 to 1 -- Bring to front
  end if
end tell
EOF

exit