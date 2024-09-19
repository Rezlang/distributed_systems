#!/bin/sh

if [ -z $1 ]; then
    echo "correct usage: client.sh <site_id>"
else    
    python3 "./bin/client.py" $1
fi