#!/bin/bash

if [[ ! -d glycomimetics/output/ ]]; then
    echo "Usage: $0 must be run from working directory that contains folders: simulation and glycomimetics/output/"
    echo "We are currently here: $PWD"
    echo "Exiting"
    exit 1
fi
glycomimetic_output_dir="glycomimetics/output/"
simulation_workdir="simulation"

cd ${glycomimetic_output_dir}
for i in *_ligand.pdb; do
    #This gets the name. 
    x=$(echo ${i} | sed 's/_ligand.pdb//')
    if [[ -f *${x}*clash* ]];then
        echo "${i} is too large to fit in the binding site. Won't run it through MD"
        continue
    fi
    #If x isn't "natural", prefix "analog".
    if [[ ${i} != "natural"* ]]; then
        dirname="analog_"${x}
        full_path=../../${simulation_workdir}/${dirname}
    else
        full_path=../../${simulation_workdir}/${x}
    fi
    #Create the folders for sims, copy files and remove CONECT records.
    mkdir -p ${full_path}/1_leap
    cp ${i} ${x}_receptor.pdb ${x}_pdb2glycam.log ${full_path}/1_leap
    sed '/CONECT/d' ${i} > ${full_path}/1_leap/${x}_ligand_noconect.pdb
done
cd ../../
echo "Finished $0. Ran from $PWD"
