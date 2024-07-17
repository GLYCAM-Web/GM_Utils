#!/bin/bash
analog_name=$1
cocomplex_box_size="10"
ligand_box_size="15"

echo "tleap sh analog name: ${analog_name}" 
receptor_pdb=${analog_name}_receptor.pdb

glycam_gaff_off=${analog_name}_glycam_gaff.off
glycam_gaff_frcmod=${analog_name}_glycam_gaff.frcmod
tleap_receptor_pdb="receptor_nowat_noion.pdb"
tleap_ligand_pdb="ligand_nowat_noion.pdb"

echo "source leaprc.GLYCAM_06j-1
#for wilde use
source leaprc.protein.ff14SB
#for frost use
#source leaprc.protein.ff14SB

source leaprc.gaff
#On Harper, amber 20, use the following ion param for calcium
loadamberparams frcmod.ions234lm_1264_tip3p

loadamberparams corona.frcmod
loadamberparams ${glycam_gaff_frcmod}

receptor = loadpdb ${receptor_pdb}
savepdb receptor receptor_nowat_noion.pdb
saveamberparm receptor receptor_nowat_noion.prmtop receptor_nowat_noion.rst7

#loadOff corona.lib
loadOff ${glycam_gaff_off}

ligand = sequence{corona}
savepdb ligand ligand_nowat_noion.pdb
saveamberparm ligand ligand_nowat_noion.prmtop ligand_nowat_noion.rst7


cocomplex = combine {receptor ligand}
savepdb cocomplex cocomplex_nowat_noion.pdb
saveamberparm cocomplex cocomplex_nowat_noion.prmtop cocomplex_nowat_noion.rst7

addIons receptor Na+ 0
addIons receptor Cl- 0
solvateoct receptor TIP3PBOX ${cocomplex_box_size} iso
saveamberparm receptor receptor.prmtop receptor.rst7

addIons ligand Na+ 0 
addIons ligand Cl- 0
solvateoct ligand TIP3PBOX ${ligand_box_size} iso
saveamberparm ligand ligand.prmtop ligand.rst7

addIons cocomplex Na+ 0
addIons cocomplex Cl- 0
solvateoct cocomplex TIP3PBOX ${cocomplex_box_size} iso
saveamberparm cocomplex cocomplex.prmtop cocomplex.rst7

quit
" > tleap.in

tleap -f tleap.in

ambpdb -p receptor_nowat_noion.prmtop <receptor_nowat_noion.rst7> receptor_nowat_noion.pdb
ambpdb -p ligand_nowat_noion.prmtop <ligand_nowat_noion.rst7> ligand_nowat_noion.pdb
ambpdb -p cocomplex_nowat_noion.prmtop <cocomplex_nowat_noion.rst7> cocomplex_nowat_noion.pdb

echo "$0 finished"
