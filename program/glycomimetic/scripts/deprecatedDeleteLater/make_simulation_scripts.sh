dirname=$1
autogen_input_path="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files"
interface_glycam_gaff_path="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/glycam_gaff_interfacing"
glycomimetic_program_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/"
glycomimetics_scripts_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
num_cpus_emin=14
num_cpus_gbsa=14
num_mem_gaussian="1024MB"
g16root="/programs/gaussian/16"

if [[ ${dirname} == "natural_ligand" ]]; then
    analog_name="natural"
else
    analog_name=$(echo ${dirname} | sed "s/analog_//")
fi
echo "Processing ${analog_name}"
ligand_pdb="${analog_name}_ligand.pdb"

#SBATCH --partition=glycomimetics

echo "#!/bin/bash
#SBATCH -D ${dirname}/1_leap
#SBATCH -J E-${analog_name}
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=${num_cpus_emin}


source /etc/profile.d/modules.sh
source ${AMBERHOME}/amber.sh


#srun hostname -s | sort -u >slurm.hosts
bash ../../simulation_${analog_name}_Emin.sh

echo \"Slurm script ends\"
" > slurm_submit_${dirname}.sh

echo "#Antechamber
nc=\$(grep \"\b${analog_name}:\" ../../charges.txt | sed \"s/${analog_name}://\")
echo \"Net charge: \${nc}\"

#Only run this part if you want to calculate RESP charges for R groups
<<\"comment\"
#Make Gaussian input file for optimization
${glycomimetics_scripts_dir}/make_gaussian_input_file.sh ${analog_name}_ligand.pdb ${analog_name}.chk ${analog_name}_ligand.com \${nc} ${num_cpus_emin} ${num_mem_gaussian} 0

#Gaussian 16
export g16root=${g16root}
source ${g16root}/g16/bsd/g16.profile
mkdir -p /local/oliver/${analog_name}
export PBS_O_WORKDIR=\".\"
cd \${PBS_O_WORKDIR}
export GAUSS_SCRDIR=/local/oliver/${analog_name}
export GAUSS_RUNDIR=\${PBS_O_WORKDIR}

#Run optimization
/programs/gaussian/16/g16/g16 \${GAUSS_RUNDIR}/${analog_name}_ligand.com \${GAUSS_RUNDIR}/${analog_name}_ligand_g16.log

#Make Gaussian input file for ESP calculation
${glycomimetics_scripts_dir}/make_gaussian_input_file.sh ${analog_name}_ligand.pdb ${analog_name}_esp.chk ${analog_name}_ligand_esp.com \${nc} ${num_cpus_emin} ${num_mem_gaussian} 1

#Run ESP calculation
/programs/gaussian/16/g16/g16 \${GAUSS_RUNDIR}/${analog_name}_ligand_esp.com \${GAUSS_RUNDIR}/${analog_name}_ligand_esp_g16.log
rm -rf /local/oliver/${analog_name}

#exit 1

#Make RESP input file
${glycomimetic_program_dir}/autogen_resp_input/main.exe ${analog_name}_ligand_noconect.pdb \${nc} ${analog_name}_resp.in
#Do RESP calculation
num_atoms=\$(grep -c \"ATOM\" ${analog_name}_ligand.pdb)
num_het_atoms=\$(grep -c \"HETATM\" ${analog_name}_ligand.pdb)
let "num_atoms+=\${num_het_atoms}"
echo \"Num atoms : \${num_atoms}\"
#${glycomimetics_scripts_dir}/run_resp.sh ${analog_name}_ligand_esp_g16.log \${num_atoms} ${analog_name}_resp.in ${analog_name}_resp.out ${analog_name}_resp.pch ${analog_name}_resp_charges.out 
${glycomimetics_scripts_dir}/Run.resp ${analog_name}_ligand_esp_g16.log \${num_atoms} ${analog_name}_resp.in ${analog_name}_resp.out ${analog_name}_resp.pch ${analog_name}_resp_charges.out 

#exit 1
comment
#To only calculate RESP Charges for R groups, uncomment 'exit 1'


# echo \"antechamber -i ${analog_name}_ligand.pdb -fi pdb -o corona.mol2 -fo mol2 -c bcc -s 2 -nc \${nc}\"
echo \"antechamber -i ${analog_name}_ligand.pdb -fi pdb -o corona.mol2 -fo mol2 \"
antechamber -i ${analog_name}_ligand.pdb -fi pdb -o corona.mol2 -fo mol2
#antechamber -i ${analog_name}_ligand.pdb -fi pdb -o corona.mol2 -fo mol2 -at gaff

#Frcmod
parmchk2 -i corona.mol2 -f mol2 -o corona.frcmod

#Interfacing
mol2=corona.mol2
ligand_pdb=${ligand_pdb}
pdb2glycam_log=${analog_name}_pdb2glycam.log
amber_gaff_dat=\"${interface_glycam_gaff_path}/gaff.dat\"
antechamber_frcmod=corona.frcmod
output_glycam_gaff_frcmod=${analog_name}_glycam_gaff.frcmod
output_glycam_gaff_off=${analog_name}_glycam_gaff.off

#Use this when calculating RESP charges of R groups. 
#${interface_glycam_gaff_path}/main.exe \${mol2} ${analog_name}_ligand_noconect.pdb \${pdb2glycam_log} \${amber_gaff_dat} \${antechamber_frcmod} ${analog_name}_resp_charges.out \${output_glycam_gaff_frcmod} \${output_glycam_gaff_off} \${nc}

#Use this for virtual screening.
${interface_glycam_gaff_path}/main.exe \${mol2} ${analog_name}_ligand_noconect.pdb \${pdb2glycam_log} \${amber_gaff_dat} \${antechamber_frcmod} none \${output_glycam_gaff_frcmod} \${output_glycam_gaff_off} \${nc}
#exit 1

#tleap
${glycomimetics_scripts_dir}/tleap.sh ${analog_name}


#Make input files
${autogen_input_path}/main.exe receptor_nowat_noion.pdb cocomplex_nowat_noion.pdb ../2_min/01.min.in ../2_min/02.relax.in ../2_min/03.min.in ../2_min/04.min.in ../2_min/05.min.in ../3_md/06.relax.in ../3_md/07.relax.in ../3_md/08.relax.in ../3_md/09.relax.in ../3_md/10.md.in ../4_gbsa/mmgbsa.in ../4_gbsa/_MMPBSA_gb_decomp_com.mdin  ../4_gbsa/_MMPBSA_gb_decomp_lig.mdin  ../4_gbsa/_MMPBSA_gb_decomp_rec.mdin

#01.min.in  02.relax.in  03.min.in  04.min.in  05.min.in  06.relax.in  07.relax.in  08.relax.in  09.relax.in  10.produ.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/01.min.in ../2_min/ligand_01.min.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/02.relax.in ../2_min/ligand_02.relax.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/03.min.in ../2_min/ligand_03.min.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/04.min.in ../2_min/ligand_04.min.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/05.min.in ../2_min/ligand_05.min.in

cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/06.relax.in ../3_md/ligand_06.relax.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/07.relax.in ../3_md/ligand_07.relax.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/08.relax.in ../3_md/ligand_08.relax.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/09.relax.in ../3_md/ligand_09.relax.in
cp $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/autogen_md_input_files/roe_protocol_input_files/10.produ.in ../3_md/ligand_10.md.in

ligand_ntwprt=\$(grep ATOM ./ligand_nowat_noion.pdb | tail -n1 | awk '{print \$2}')
sed -i \"s/ligand_ntwprt/\${ligand_ntwprt}/\" ../3_md/ligand_10.md.in
#exit 1

#Energy minimization
cd ../2_min
export pmemd=\"mpirun -np ${num_cpus_emin} \${AMBERHOME}/bin/pmemd.MPI\"
wallclock=\"Total wall time\"

#Step one
\${pmemd} -O \\
 -p ../1_leap/cocomplex.prmtop \\
 -c ../1_leap/cocomplex.rst7 \\
 -i 01.min.in \\
 -o 01.min.out \\
 -r 01.min.rst7 \\
 -ref ../1_leap/cocomplex.rst7

\${pmemd} -O \\
 -p ../1_leap/ligand.prmtop \\
 -c ../1_leap/ligand.rst7 \\
 -i ligand_01.min.in \\
 -o ligand_01.min.out \\
 -r ligand_01.min.rst7 \\
 -ref ../1_leap/ligand.rst7

if grep -q \"\${wallclock}\" 01.min.out ; then
#Step two
    \${pmemd} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 01.min.rst7 \\
     -i 02.relax.in \\
     -o 02.relax.out \\
     -r 02.relax.rst7 \\
     -ref 01.min.rst7

    \${pmemd} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_01.min.rst7 \\
     -i ligand_02.relax.in \\
     -o ligand_02.relax.out \\
     -r ligand_02.relax.rst7 \\
     -ref ligand_01.min.rst7

else
    echo "Step one min failed"
    exit 1
fi

if grep -q \"\${wallclock}\" 02.relax.out ; then
#Step three
    \${pmemd} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 02.relax.rst7 \\
     -i 03.min.in \\
     -o 03.min.out \\
     -r 03.min.rst7 \\
     -ref 02.relax.rst7

    \${pmemd} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_02.relax.rst7 \\
     -i ligand_03.min.in \\
     -o ligand_03.min.out \\
     -r ligand_03.min.rst7 \\
     -ref ligand_02.relax.rst7
else
    echo "Step two relax failed"
    exit 1
fi


if grep -q \"\${wallclock}\" 03.min.out ; then
#Step four
    \${pmemd} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 03.min.rst7 \\
     -i 04.min.in \\
     -o 04.min.out \\
     -r 04.min.rst7 \\
     -ref 03.min.rst7

    \${pmemd} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_03.min.rst7 \\
     -i ligand_04.min.in \\
     -o ligand_04.min.out \\
     -r ligand_04.min.rst7 \\
     -ref ligand_03.min.rst7
else
    echo "Step three min failed"
    exit 1
fi

if grep -q \"\${wallclock}\" 04.min.out ; then
#Step five
    \${pmemd} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 04.min.rst7 \\
     -i 05.min.in \\
     -o 05.min.out \\
     -r 05.min.rst7 \\
     -ref 04.min.rst7

    \${pmemd} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_04.min.rst7 \\
     -i ligand_05.min.in \\
     -o ligand_05.min.out \\
     -r ligand_05.min.rst7 \\
     -ref ligand_04.min.rst7
else
    echo "Step four min failed"
    exit 1
fi


if grep -q \"\${wallclock}\" 05.min.out ; then
    cd ../3_md
    sbatch --exclude=node[001-005] --no-requeue ../../simulation_${analog_name}_md.sh
else
    echo "Step 5 min failed. Abort MD"
fi
" > simulation_${analog_name}_Emin.sh

echo "#!/bin/bash
#SBATCH -D .
#SBATCH -J M-${analog_name}
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --gres=gpu:1

source /etc/profile.d/modules.sh
source ${AMBERHOME}/amber.sh
srun hostname -s | sort -u >slurm.hosts

#MD
pmemd_cuda=\"${AMBERHOME}/bin/pmemd.cuda\"

#Step 6
\${pmemd_cuda} -O \\
 -p ../1_leap/cocomplex.prmtop \\
 -c ../2_min/05.min.rst7 \\
 -i 06.relax.in \\
 -o 06.relax.out \\
 -r 06.relax.rst7 \\
 -ref ../2_min/05.min.rst7

\${pmemd_cuda} -O \\
 -p ../1_leap/ligand.prmtop \\
 -c ../2_min/ligand_05.min.rst7 \\
 -i ligand_06.relax.in \\
 -o ligand_06.relax.out \\
 -r ligand_06.relax.rst7 \\
 -ref ../2_min/ligand_05.min.rst7

if grep -q \"\${wallclock}\" 06.relax.out ; then
#Step 7 
    \${pmemd_cuda} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 06.relax.rst7 \\
     -i 07.relax.in \\
     -o 07.relax.out \\
     -r 07.relax.rst7 \\
     -ref 06.relax.rst7

     \${pmemd_cuda} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_06.relax.rst7 \\
     -i ligand_07.relax.in \\
     -o ligand_07.relax.out \\
     -r ligand_07.relax.rst7 \\
     -ref ligand_06.relax.rst7
else
    echo "Step 6 relax failed"
    exit 1
fi

if grep -q \"\${wallclock}\" 07.relax.out; then
#Step 8
    \${pmemd_cuda} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 07.relax.rst7 \\
     -i 08.relax.in \\
     -o 08.relax.out \\
     -r 08.relax.rst7 \\
     -ref 07.relax.rst7

    \${pmemd_cuda} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_07.relax.rst7 \\
     -i ligand_08.relax.in \\
     -o ligand_08.relax.out \\
     -r ligand_08.relax.rst7 \\
     -ref ligand_07.relax.rst7
else
    echo "Step 7 relax failed"
    exit 1
fi

if grep -q \"\${wallclock}\" 08.relax.out; then
#Step 9
    \${pmemd_cuda} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 08.relax.rst7 \\
     -i 09.relax.in \\
     -o 09.relax.out \\
     -r 09.relax.rst7 \\
     -ref 08.relax.rst7

    \${pmemd_cuda} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_08.relax.rst7 \\
     -i ligand_09.relax.in \\
     -o ligand_09.relax.out \\
     -r ligand_09.relax.rst7 \\
     -ref ligand_08.relax.rst7
else
    echo "Step 8 relax failed"
    exit 1
fi

if grep -q \"\${wallclock}\" 09.relax.out; then
#Step 10
    \${pmemd_cuda} -O \\
     -p ../1_leap/cocomplex.prmtop \\
     -c 09.relax.rst7 \\
     -i 10.md.in \\
     -o 10.md.out \\
     -r 10.md.rst7 \\
     -x 10.md.nc \\
     -ref 09.relax.rst7

     \${pmemd_cuda} -O \\
     -p ../1_leap/ligand.prmtop \\
     -c ligand_09.relax.rst7 \\
     -i ligand_10.md.in \\
     -o ligand_10.md.out \\
     -r ligand_10.md.rst7 \\
     -x ligand_10.md.nc \\
     -ref ligand_09.relax.rst7
else
    echo "Step 9 relax failed"
    exit 1
fi

#check if MD is complete
if grep -q \"\${wallclock}\" 10.md.out ; then
    cd ../4_gbsa

    sbatch --exclude=node[001-005] --no-requeue ../../simulation_${analog_name}_gbsa.sh
else
    echo "Step 10 md failed. Abort MM-GBSA"
fi
" > simulation_${analog_name}_md.sh

echo "#!/bin/bash
#SBATCH -D .
#SBATCH -J G-${analog_name}
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=${num_cpus_gbsa}

source /etc/profile.d/modules.sh
source ${AMBERHOME}/amber.sh
srun hostname -s | sort -u >slurm.hosts

mmpbsa=\"mpirun -np ${num_cpus_gbsa} ${AMBERHOME}/bin/MMPBSA.py.MPI\"

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
" > simulation_${analog_name}_gbsa.sh

