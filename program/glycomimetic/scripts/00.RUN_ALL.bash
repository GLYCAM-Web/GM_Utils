#!/bin/bash

if [ $# -ne 3 ]; then
    echo "GEMS must create a working directory and put the necessary files in there. Then run this script."
    echo "Usage: $0 userPdbFile inputFileName systemInformationFile"
    echo "Exmpl: $0 complex.pdb input.txt systemInfo.txt"
    echo "Exiting now"
    exit 1
fi

userPdb=$1
inputFile=$2
systemInfo=$3

source $systemInfo #installPath variable 
scripts=$installPath/scripts

output=out.txt
>$output
statusFile=status.txt
echo "$0 has been started with these arguments: <$1> <$2> <$3>" >$statusFile
# Running the scripts in order
$scripts/0.setupFolders.sh $userPdb $inputFile $systemInfo >> $output
if [ $? -ne 0 ]; then
    echo !!
    echo "Failed. $0 is exiting."
    exit 1;
fi

$scripts/1.convertPdbToPdbqt.sh.wip $userPdb $systemInfo >> $output
if [ $? -ne 0 ]; then
    echo "Failed. $0 is exiting."
    exit 1;
fi
if [ ! -f glycomimetics/cocomplex.pdbqt ]; then
    echo "pdb to pdbqt converstion failed. $0 is exiting.."
    grep "Sorry" $output >> $statusFile
    exit 1;
fi

$scripts/2.glycomimetic.sh $inputFile $systemInfo >> $output
if [[ $? -ne 0 || ! -f glycomimetics/output/natural_ligand.pdb || ! -f glycomimetics/output/natural_receptor.pdb ]]; then
    echo "Glycomimetic Step Failed. glycomimetics/output/natural_ligand.pdb and glycomimetics/output/natural_receptor.pdb should exist. $0 is exiting." >> $statusFile
    exit 1;
fi

$scripts/3.setupTleapFolders.sh >> $output
if [ $? -ne 0 ]; then
    echo "Failed. $0 is exiting." >> $statusFile
    exit 1;
fi

$scripts/4.addCharges.sh $inputFile >> $output
if [ $? -ne 0 ]; then
    echo "Failed. $0 is exiting." >> $statusFile
    exit 1;
fi

$scripts/5a.runScript.sh $systemInfo >> $output
if [[ $? -ne 0 || ! -f simulation/1_leap/receptor_nowat_noion.rst7 || ! -f simulation/1_leap/ligand_nowat_noion.rst7]]; then
    echo "Tleap step failed. $0 is exiting." >> $statusFile
    exit 1;
fi

$scripts/6.runSims.sh $installPath/internal/MD_Utils/protocols/RoeProtocol/ >> $output
if [ $? -ne 0 ]; then
    echo "Failed. $0 is exiting." >> $statusFile
    exit 1;
fi

#Some how figure out the sims are done. Edit no just do it at the end of the sims in the submit script.
#$scripts/7.setupRunMmgbsa.sh >> $output
#if [ $? -ne 0 ]; then
#    echo "Failed. $0 is exiting." >> $statusFile
#    exit 1;
#fi
#echo "$0 is finished." >> $statusFile
