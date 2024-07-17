A utility program to interface GLYCAM (sugar) and GAFF (R group) for mixed use. 
Compilation
g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ main.cpp -lgmml -pthread -o ./main.exe -lgmml -lpthread

Before using this program: 
Run the output ligand file from the glycomimetic program through Antechamber to obtain a mol2 file of the ligand. GAFF types and charges will be read from this file.
Run the mol2 file through parmchk to obtain non-standard GAFF parameters.

Usage:
/home/yao/GLYCAM_Dev_Env/V_2/Web_Programs/gems/glycomimetics/glycam_gaff_interfacing/main.exe mol2_path ligand_pdb_path pdb2glycam_logfile gaff.dat_path antechamber_frcmod_path output_glycam_gaff_frcmod output_glycam_gaff_off

mol2_path: Antechamber mol2 file
ligand_pdb_path: Ligand pdb file from glycomimetic program
pdb2glycam_logfile Pdb2glycam log file for this ligand from glycomimetic program
gaff.dat_path: path to the standard gaff parameter file (either gaff.dat or gaff2.dat I believe).
antechamber_frcmod_path: Parmchk frcmod file
output_glycam_gaff_frcmod: Path and filename of the output frcmod file containing glycam-gaff interfacing parameters.
output_glycam_gaff_off: Path and filename of the output OFF file of the entire ligand. Using OFF bypasses difficult bonding manipulation of the input pdb file to be used with tleap. 

