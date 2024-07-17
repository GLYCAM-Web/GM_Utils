#!/bin/bash

if [[ ! -d simulation || $# -ne 1 ]]; then
    echo "$0 must be called from the folder that contains simulation/"
    echo "Usage: $0 systemInfoFile"
    echo "Exmpl: $0 systeminfo.txt"
    echo "Exiting."
    exit 1
fi
systemInfo=$1
source $systemInfo # $installPath
cd simulation/

for dirname in $( ls -d analog_* ); 
do
    analog_name=$(echo ${dirname} | sed "s/analog_//")
    echo "Calling next step like this:"
    echo "$installPath/scripts/5b.setupRunTleap.sh $analog_name ../$systemInfo"
    $installPath/scripts/5b.setupRunTleap.sh $analog_name ../$systemInfo
done
#Now do natural:
$installPath/scripts/5b.setupRunTleap.sh natural ../$systemInfo

echo "$0 finished setting up and running tleap for each system."
