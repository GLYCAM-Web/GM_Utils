#!/bin/bash

# Create "frames/summary/rmsd" directory if it doesn't exist
if [[ ! -d "frames/summary/rmsd" ]]; then
    mkdir -p frames/summary/rmsd
fi

# Loop through all ligand directories
for i in analog_* natural; do
    # Create ligand directory if it doesn't exist
    #if [[ ! -d "frames/${i}" ]]; then
        #mkdir frames/${i}
    #fi

    # Set prefix and path for file naming
    prefix="frame_"
    path="frames/${i}/${prefix}"
    
    # Generate cpptraj input file
    echo "parm ${i}/1_leap/cocomplex_nowat_noion.prmtop
trajin ${i}/3_md/10.md.nc
rmsd first :1-208@CA
rmsd first :23,138 out frames/summary/rmsd/${i}_glycomimetic_rmsd.txt nofit
" > frames/cpptraj_rmsd_calc.in

    # Run cpptraj to calculate RMSD and save to text file
    cpptraj < frames/cpptraj_rmsd_calc.in

    # Check if output file was generated
    if [[ -f "frames/summary/rmsd/${i}_glycomimetic_rmsd.txt" ]]; then
        # Rename output file to include moiety name
        mv frames/summary/rmsd/${i}_glycomimetic_rmsd.txt frames/summary/rmsd/${i}.txt
    else
        echo "Error: RMSD calculation for ${i} failed"
    fi
done
