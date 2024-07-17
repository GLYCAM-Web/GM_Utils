#!/bin/bash
num_frames=10000
interval=50

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
trajin ${i}/3_md/10.md.nc 1 ${num_frames} ${interval}
autoimage
trajout frames/summary/movies/${i}/ShortMD.nc
" > frames/cpptraj_short_MD.in

    # Run cpptraj to make and save short movie
    cpptraj < frames/cpptraj_short_MD.in

    # Check if output file was generated
    if [[ -f "frames/summary/movies/${i}/ShortMD.nc" ]]; then
        # Rename output file to include moiety name
        mv frames/summary/movies/${i}/ShortMD.nc frames/summary/movies/${i}/Step50_MD.nc
    else
        echo "Error: Short movie for ${i} failed"
    fi
done
