#!/bin/bash

if [ $# -ne 3 ]; then
    echo "GEMS must create a directory and put the file in there. Then run this script."
    echo "Usage: $0 userPdbFile inputFileName systemInformationFile"
    echo "Exmpl: $0 complex.pdb input.txt systemInfo.txt"
    echo "Exiting now"
    exit 1
fi

userPdb=$1
inputFile=$2
systemInfo=$3

mkdir -p glycomimetics/output
mkdir -p simulation/
cp $userPdb $inputFile $systemInfo glycomimetics/

echo "I am $0. I setup the folder structure."
echo "Finished $0. Ran from $PWD"

