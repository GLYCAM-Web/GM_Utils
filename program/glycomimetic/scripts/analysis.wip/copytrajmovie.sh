#!/bin/bash

# Create "frames/summary/movies" directory if it doesn't exist
if [[ ! -d "frames/summary/movies" ]]; then
    mkdir -p frames/summary/movies
fi

# Loop through all ligand directories
for i in analog_* natural; do
    # Create ligand directory if it doesn't exist
    if [[ ! -d "frames/summary/movies/${i}" ]]; then
        mkdir frames/summary/movies/${i}
    fi
    
    # Copy prmtop and nc files to movies directory
    cp ${i}/1_leap/cocomplex_nowat_noion.prmtop frames/summary/movies/${i}
    cp ${i}/1_leap/cocomplex_nowat_noion.pdb frames/summary/movies/${i}
    cp ${i}/3_md/10.md.nc frames/summary/movies/${i}
done
