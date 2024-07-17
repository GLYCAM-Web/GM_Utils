#!/bin/bash

if [ ! -d simulation ]; then
    echo "$0 must be run from a folder that contains the foler simulation/"
    echo "Exiting"
    exit 1
fi

simulationDirectory=$1
cd ${simulationDirectory}

echo "#!/bin/bash
#SBATCH -J JOBNAME
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=10

source /etc/profile.d/modules.sh
source ${AMBERHOME}/amber.sh
srun hostname -s | sort -u >slurm.hosts

mmpbsa=\"mpirun -np 10 ${AMBERHOME}/bin/MMPBSA.py.MPI\"

\${mmpbsa} -O \\
 -i mmgbsa.in \\
 -cp ../1_leap/cocomplex_nowat_noion.prmtop \\
 -rp ../1_leap/receptor_nowat_noion.prmtop \\
 -lp ../1_leap/ligand_nowat_noion.prmtop \\
 -y  ../3_md/10.md.nc \\
 -o  mmgbsa.out \\
 -do decom_gbsa.dat \\
 -eo per_frame_breakdown.dat \\
 -use-mdins
" > mmgbsa.sh

wallclock="Total wall time"

for folder in analog_* natural; do
    #Use this to run md of glycomimetic analogs
    mkdir -p $folder/4_mmgbsa
    sed "s/JOBNAME/gm-$folder/g" mmgbsa.sh > $folder/4_mmgbsa/mmgbsa.sh
    cd $folder/4_mmgbsa/
    if [ ! grep -q ${wallclock} ../3_md/10.md.out ]; then
        echo "Step 10 md failed for $folder. Not running MM-GBSA."
        continue
    fi
    sbatch --no-requeue mmgbsa.sh
    cd ../../
    echo "$0 submitted mmgbsa for $folder."
done
cd ../
echo "Finished $0. Ran from $PWD"
