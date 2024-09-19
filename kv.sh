#!/bin/sh

if [ -z $1 ]; then
    echo "correct usage: kv.sh <site_id>"
else    
    python3 "./bin/kv.py" $1
fi