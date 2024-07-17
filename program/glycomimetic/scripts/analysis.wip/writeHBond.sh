#!/bin/bash

# Create "frames/summary/rmsd" directory if it doesn't exist
if [[ ! -d "frames/summary/hbond" ]]; then
    mkdir -p frames/summary/hbond
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
hbond :1-210 avgout frames/summary/hbond/${i}_avg.dat series uuseries frames/summary/hbond/${i}_hbond.gnu nointramol
" > frames/cpptraj_hbond.in

    # Run cpptraj to calculate RMSD and save to text file
    cpptraj < frames/cpptraj_hbond.in

    # Check if output file was generated
    if [[ -f "frames/summary/rmsd/${i}_hbond.gnu" ]]; then
        # Rename output file to include moiety name
        mv frames/summary/rmsd/${i}_hbond.gnu frames/summary/rmsd/${i}.gnu
    else
        echo "Error: Hbond calculation for ${i} failed"
    fi
done
