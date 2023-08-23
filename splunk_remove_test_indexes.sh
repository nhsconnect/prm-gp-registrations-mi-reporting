#!/bin/bash
cd "$SPLUNK_HOME/bin" || exit

INDEXES=$(./splunk list index)
for INDEX in $INDEXES
do
    if [[ $INDEX == test_* ]];
    then
        echo "Removing index {$INDEX}"
        ./splunk remove index "$INDEX"
    fi
   
done