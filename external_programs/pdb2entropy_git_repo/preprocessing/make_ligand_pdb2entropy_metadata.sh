#for i in 14  16  2   25  27  29  50 15  1b  21  26  28  30; do 
if [[ ! -d ligand_pdb2entropy_metadata ]];then
    mkdir ligand_pdb2entropy_metadata
fi

for i in $(ls -d frames_ligand/*);do
    moiety_name=$(echo ${i} | sed 's/frames_ligand\///')
    echo ${moiety_name}
    pdbqt_parsed="cocomplex_pdbs/${moiety_name}_cocomplex_renamed.pdbqt"
    output_file="ligand_pdb2entropy_metadata/${moiety_name}.dat"

    #echo "${pdb_parsed} ${output_file}"
    ./make_ligand_pdb2entropy_metadata.out ${pdbqt_parsed} ${output_file}

    echo -e "Done ${moiety_name}\n\n" 

done
