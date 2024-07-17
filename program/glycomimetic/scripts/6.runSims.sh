#!/bin/bash

if [[ ! -d simulation || $# -ne 1 ]]; then
    echo "$0 must be run in a folder that contains the simulation/ directory"
    echo "Usage: You must supply the location of MD_Utils Roe protocol folder"
    echo "Exmpl: $0 /programs/glycomimetic/internal/MD_Utils/protocols/RoeProtocol/"
    echo "Exiting"
    exit 1
fi
mdProtocolDirectory=$1

#Now make simulation directories, one for each analog
cd simulation/
for folder in analog_* natural; do
    #Use this to run md of glycomimetic analogs
    mkdir $folder/3_md/
    cd $folder/3_md/
     #Copy the MD_Utils folder
     rsync -avL $mdProtocolDirectory .  # the L resolves symlinks.
     rsync -av ../1_leap/cocomplex.prmtop MdInput.parm7
     rsync -av ../1_leap/cocomplex.rst7 MdInput.rst7
     sed -i "s/JOBNAME/$folder/g" submit.GPU.sh
     sbatch --no-requeue submit.GPU.sh
    cd ../../
done
echo "Finished $0. Ran from $PWD"
