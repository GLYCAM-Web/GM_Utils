#!/bin/bash

# Create "frames/summary/rmsf" directory if it doesn't exist
if [[ ! -d "frames/summary/rmsf" ]]; then
    mkdir -p frames/summary/rmsf
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
rms first :209&@C4,O6,C7,C22,C32,C36
average crdset RefAvg
run
rms ref RefAvg nofit
atomicfluct out frames/summary/rmsf/${i}_glycomimetic_rmsf.txt byres
" > frames/cpptraj_rmsf_calc.in

    # Run cpptraj to calculate RMSD and save to text file
    cpptraj < frames/cpptraj_rmsf_calc.in

    # Check if output file was generated
    if [[ -f "frames/summary/rmsf/${i}_glycomimetic_rmsf.txt" ]]; then
        # Rename output file to include moiety name
        mv frames/summary/rmsf/${i}_glycomimetic_rmsf.txt frames/summary/rmsf/${i}.txt
    else
        echo "Error: RMSF calculation for ${i} failed"
    fi
done
