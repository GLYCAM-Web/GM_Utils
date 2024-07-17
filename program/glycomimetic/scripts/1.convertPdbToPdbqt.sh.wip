#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 userCoComplexFile systemInfoFile"
    echo "Exmpl: $0 complex.pdb systeminfo.txt"
    echo "Exiting now"
    exit 1
fi
userPdb=$1
systemInfo=$2
source $systemInfo # installPath variable

# Use oliver's prepreprocessor to fix partial occupancy, rename to ATOM, do CYS bonds, etc
$installPath/internal/gmml2/tests/gmPreProcessor.exe $userPdb glycomimetics/processed-$userPdb

# Prepare User Provided Co-Complex. This is very picky about format.
mglPath=$installPath/external/MGLTools-1.5.4/
export MGLUTIL=$mglPath/MGLToolsPckgs/AutoDockTools/Utilities24/
export PYTHONPATH="${PYTHONPATH}:${mglPath}MGLToolsPckgs/"
$MGLPY $MGLUTIL/prepare_receptor4.py -r glycomimetics/processed-$userPdb -A hydrogens -U None -o glycomimetics/cocomplex.pdbqt -v

echo "Finished $0. Ran from $PWD"

#-r receptor file name
#-A hydrogens = add hydrogens to receptor file as needed
#-U none = don't delete/make any significant changes **Important otherwise will delete all nonstandard residues (which will delete the sugars)
#-o = output file name
#-v = verbose mode
