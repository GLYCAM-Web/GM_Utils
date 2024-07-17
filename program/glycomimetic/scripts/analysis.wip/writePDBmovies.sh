#!/bin/bash
num_frames=10000
interval=25

if [[ ! -d "frames" ]];then
    mkdir -p frames/summary
fi

for i in analog_* natural; do
    if [[ ! -d "frames/summary/movies/${i}/pdb" ]]; then
        mkdir -p frames/summary/movies/${i}/pdb
    fi

    rm -f frames/summary/movies/${i}/pdb/*

    prefix="frame_"
    path="frames/summary/movies/${i}/pdb/"

echo "parm ${i}/1_leap/cocomplex_nowat_noion.prmtop
trajin ${i}/3_md/10.md.nc 1 ${num_frames} ${interval}
# trajin ${i}/3_md/10.md.nc 1 10000 50
autoimage
trajout ${path}frame_ pdb multi nobox
go
" > frames/cpptraj_writePDBmovie.in

    cpptraj < frames/cpptraj_writePDBmovie.in

    for j in $(ls ${path}*);do
        x=$(echo $j | sed "s/${prefix}.//")
        x+=".pdb"
        mv ${j} ${x}
    done

    # Renaming step
    i=1
    max_digits=0

    # Find the number of digits in the largest file number
    for file in $(ls ${path}*); do
        file_number=$(basename "$file" | sed 's/[^0-9]*//g')  # Extract numeric part of the filename
        num_digits=${#file_number}
        if ((num_digits > max_digits)); then
            max_digits=$num_digits
        fi
    done

    for file in $(ls ${path}*); do
        file_number=$(basename "$file" | sed 's/[^0-9]*//g')  # Extract numeric part of the filename
        new_number=$(printf "%0${max_digits}d" $file_number)  # Pad with leading zeros
        new_name="${new_number}.pdb"
        # echo "Renaming: $file to $new_name"
        mv "$file" "$(dirname "$file")/$new_name"
        i=$((i+1))
    done

done

