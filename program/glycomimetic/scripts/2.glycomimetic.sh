#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 glycomimeticInputFileName systemInfoFile"
    echo "Exmpl: $0 input.txt systemInfo.txt"
    echo "Exiting"
    exit 1
fi

glycomimeticInputFileName=$1
systemInfo=$2
source $systemInfo # installPath and GEMSHOME
glycomimeticProgram=$installPath/internal/glycomimeticTool/glycomimetic.exe

cd glycomimetics/

#Glycomimetics
echo "#!/bin/bash
#SBATCH --partition=gm
#SBATCH -J glycomimetics
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=2
source /etc/profile.d/modules.sh
${glycomimeticProgram} -f ${glycomimeticInputFileName}
" > slurm_submit_glycomimetics.sh
echo "Submitting glycomimetic job."
sbatch --wait slurm_submit_glycomimetics.sh

cd ../
echo "Finished $0. Ran from $PWD"
