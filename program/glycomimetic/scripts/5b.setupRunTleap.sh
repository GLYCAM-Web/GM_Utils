#!/bin/bash
# This script assumes it is being launched from inside the folder called simulation/

if [ $# -ne 2 ]; then
    echo "$# should have been 2"
    echo "1 is $1, and 2 is $2"
    echo "Usage: $0 nameOfLigand systemInfoFile"
    echo "Exmpl: $0 10_6MC_0 ../systemInfo.txt"
    echo "Exiting"
    exit 1
fi
analog_name=$1
systemInfo=$2
source $systemInfo # installPath AMBERHOME
if [ -z ${installPath} ]; then
    echo "Exiting as sourcing systemInfo didn't work in $0"
    exit 1
fi
glycomimetics_scripts_dir=$installPath/scripts/
interface_glycam_gaff_path=$installPath/internal/glycam_gaff_interfacing/

if [ $analog_name == "natural" ]; then
    dirname=$analog_name
else
    dirname=analog_$analog_name
fi

cd $dirname

echo "#!/bin/bash
#SBATCH --partition=gm
#SBATCH -D 1_leap
#SBATCH -J E-${analog_name}
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=2

source /etc/profile.d/modules.sh
source ${AMBERHOME}/amber.sh

" > slurm_submit.sh


echo "#Antechamber:
nc=\$(grep \"\b${analog_name}:\" ../../charges.txt | sed \"s/${analog_name}://\")
echo \"Net charge: \${nc}\"

echo \"antechamber -i ${analog_name}_ligand.pdb -fi pdb -o corona.mol2 -fo mol2 \"
antechamber -i ${analog_name}_ligand.pdb -fi pdb -o corona.mol2 -fo mol2

#Frcmod
parmchk2 -i corona.mol2 -f mol2 -o corona.frcmod

#Interfacing
mol2=corona.mol2
ligand_pdb=${analog_name}_ligand.pdb
pdb2glycam_log=${analog_name}_pdb2glycam.log
amber_gaff_dat=\"${interface_glycam_gaff_path}/gaff.dat\"
antechamber_frcmod=corona.frcmod
output_glycam_gaff_frcmod=${analog_name}_glycam_gaff.frcmod
output_glycam_gaff_off=${analog_name}_glycam_gaff.off

${interface_glycam_gaff_path}/glycamGaffInterfacing.exe \${mol2} ${analog_name}_ligand_noconect.pdb \${pdb2glycam_log} \${amber_gaff_dat} \${antechamber_frcmod} none \${output_glycam_gaff_frcmod} \${output_glycam_gaff_off} \${nc}

#tleap
${glycomimetics_scripts_dir}/5c.tleap.sh ${analog_name}
" >> slurm_submit.sh

echo "$0 is submitting slurm and waiting"
sbatch --wait slurm_submit.sh
cd ../
echo "$0 is finished."
