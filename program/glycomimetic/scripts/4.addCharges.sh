#!/bin/bash

# This script assumes it is being launched from the workingDirectory

if [ $# -ne 1 ]; then
    echo "Usage: $0 inputFile"
    echo "Exmpl: $0 input.txt"
    echo "Exiting"
    exit 1
fi
inputFile=$1

naturalCharge=$(grep "naturalCharge" $inputFile | cut -d : -f2)

>simulation/charges.txt
for pathToLibrary in $(grep "OpenValence" $inputFile | cut -d - -f2 | sort -u)
do
    for line in $(cat $pathToLibrary/charges.txt)
    do
        moietyName=$(echo $line | cut -d : -f1)
        moietyCharge=$(echo $line | cut -d : -f2)
        echo "$moietyName:$(($moietyCharge + $naturalCharge))" >> simulation/charges.txt
    done
done
echo "natural:$naturalCharge" >> simulation/charges.txt
printf "Finished $0 . It created ./simulation/charges.txt using the user provided natural charge ($naturalCharge) found in $inputFile.\n"
