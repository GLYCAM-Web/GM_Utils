glycomimetic_program_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/"
glycomimetic_scripts_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/"
job_workdir=$1
cd ${job_workdir}
job_workdir_absolute=$(pwd)

glycomimetic_reldir="glycomimetics"
glycomimetic_dir="${job_workdir_absolute}/${glycomimetic_reldir}"
input_filename="sample_input_file.txt"
glycomimetic_input_file="${glycomimetic_dir}/${input_filename}"
glycomimetic_output_dir=$(grep "OutputPath:" ${glycomimetic_input_file} | sed 's/OutputPath://')
num_cpus_glycomimetics=$(grep "NumThreads:" ${glycomimetic_input_file} | sed 's/NumThreads://')

simulation_reldir="simulation"
simulation_dir="${job_workdir_absolute}/${simulation_reldir}"

#SBATCH --partition=CPU
#SBATCH -D ${job_workdir_absolute}

#Glycomimetics
echo "#!/bin/bash
#SBATCH -D ${job_workdir_absolute}
#SBATCH -J glycomimetics
#SBATCH --get-user-env
#SBATCH --nodes=1
#SBATCH --tasks-per-node=${num_cpus_glycomimetics}

source /etc/profile.d/modules.sh

cd ${glycomimetic_dir}
#${glycomimetic_program_dir}/main.exe -f ${glycomimetic_input_file}
#exit 1

#Now make simulation directories, one for each analog
cd ${job_workdir_absolute}
glycomimetic_output_dir_with_slash=\"${glycomimetic_dir}/${glycomimetic_output_dir}\"

${glycomimetic_scripts_dir}/makedir.sh \${glycomimetic_output_dir_with_slash} ${simulation_dir}
#exit 1

cd ${simulation_dir}

for i in analog_* natural; do
    #Use this to run md of glycomimetic analogs
    ${glycomimetic_scripts_dir}/make_simulation_scripts.sh \${i}

    #Use this to only run QM and RESP on R groups
    #${glycomimetic_scripts_dir}/run_qm_only.sh \${i}

    sbatch --exclude=node[001-005] --no-requeue slurm_submit_\${i}.sh
    sleep 1
done
echo 'Slurm glycomimetic script reaches end'
" > slurm_submit_glycomimetics.sh

sbatch --exclude=node[001-005] --no-requeue slurm_submit_glycomimetics.sh
