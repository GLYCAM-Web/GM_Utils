glycomimetic_scripts_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
vina_score_traj_program_dir="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../yao_glycomimetics/rescoring"
num_frames=10000
interval=5
scoring_interval=1

simulation_workdir=$1
cd ${simulation_workdir}/simulation

echo "Begin writeframe"
${glycomimetic_scripts_dir}/Analysis/writeframes.sh ${num_frames} ${interval}
echo "Begin scoretraj"
${glycomimetic_scripts_dir}/Analysis/scoretraj.sh ${scoring_interval}
echo "Begin RMSD"
${glycomimetic_scripts_dir}/Analysis/writeRMSD.sh 
echo "Begin HBond"
${glycomimetic_scripts_dir}/Analysis/writeHBond.sh
echo "Begin Copy Traj Movie"
${glycomimetic_scripts_dir}/Analysis/copytrajmovie.sh
echo "Begin copyPDBmovie"
${glycomimetic_scripts_dir}/Analysis/writePDBmovies.sh
# echo "Making Short Step 50 movie"
# ${glycomimetic_scripts_dir}/Analysis/WriteShortMoviesStep50.sh
echo "Begin RMSF"
${glycomimetic_scripts_dir}/Analysis/writeRMSF.sh

gbsa_csv="frames/summary/gbsa.csv"
echo "Moiety, MMGBSA_Enthalpy, Stdev, Rec_IE, Lig_IE, Cocomplex_IE, dG_IE, Rec_C2, Lig_C2, Cocomplex_C2, dG_C2" > ${gbsa_csv}

curdir=$(pwd)
#<<"comment"
echo "Finally, GBSA dG including interaction entropy:"
interaction_entropy_path="${glycomimetic_scripts_dir}/../../yao_glycomimetics/interaction_entropy"
#echo "$interaction_entropy_path"
for i in analog_* natural; do
    if [ ! -f "${i}/4_gbsa/per_frame_breakdown.dat" ];then
        echo "${i} Failed" >> ${gbsa_csv}
        continue
    fi
    # ${interaction_entropy_path}/interaction_entropy.exe ${i} ${curdir}/${i}/4_gbsa/per_frame_breakdown.dat >> ${gbsa_csv}
    data=$(${interaction_entropy_path}/interaction_entropy.exe "${i}" "${curdir}/${i}/4_gbsa/per_frame_breakdown.dat")
    # Use awk to format the data into CSV format with proper field separation (add commas in data)
    echo "$data" | awk '{ printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n", $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11 }' >> "${gbsa_csv}"

done
#comment

<<"comment"
echo "Finally, GBSA dG:"
mkdir -p frames/summary
rm -f frames/summary/gbsa_summary.txt

for i in analog_* natural; do
    gbsa_info=""
    if grep -q "DELTA TOTAL" ${i}/4_gbsa/mmgbsa.out; then
        gbsa_info=$(grep "DELTA TOTAL" ${i}/4_gbsa/mmgbsa.out | awk '{print $3" "$4}')
    else
        gbsa_info="Failed"
    fi

    echo "${i} ${gbsa_info}"
    echo "${i} ${gbsa_info}" >> frames/summary/gbsa_summary.txt
done

 sort -nk1 frames/summary/gbsa_summary.txt > frames/summary/gbsa_summary_sorted.txt
comment
