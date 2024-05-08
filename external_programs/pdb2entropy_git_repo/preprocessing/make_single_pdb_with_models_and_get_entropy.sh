num_ns=$1
num_frames=$2
ndiv=$3
let "frames_per_div=${num_frames}/${ndiv}"

if [[ ! -d all_model_pdbs ]];then
    mkdir all_model_pdbs
fi

if [[ ! -d all_ligand_model_pdbs ]];then
    mkdir all_ligand_model_pdbs
fi

<<"comment"
rm -f all_model_pdbs/*.pdb

for i in $(ls -d frames/*);do
    echo $i
    moiety_name=$(echo ${i} | sed 's/frames\///')
    for div in $(seq 1 1 ${ndiv});do
        pdb_filename="${moiety_name}_${div}.pdb"
	echo "Cocomplex pdb filename: ${pdb_filename}"

	#If not the last div, #models in pdb = frame_per_div*ndiv. This is a rounded down number. If last div, equals the total # of pdbs
	if [[ ${div} -ne  ${ndiv} ]];then 
	    let "num_frames_this_pdb=${frames_per_div}*${div}"
	else
	    num_frames_this_pdb=${num_frames}
	fi

        for j in $(seq 1 1 ${num_frames_this_pdb});do
	    echo "MODEL       ${j}" >> all_model_pdbs/${pdb_filename}
	    cat ${i}/${j}_renamed.pdb >> all_model_pdbs/${pdb_filename}
	    echo "ENDMDL">> all_model_pdbs/${pdb_filename}
        done

        #PDB written by cpptraj does not contain chain ID, but pdb2trent requires one. So assign chain A to all ATOM entries. 
        sed -i 's/^\(ATOM.\{17\}\) /\1A/'  all_model_pdbs/${pdb_filename} ${i}/1_renamed.pdb

        #Calculate protein conformational entropy 
        entropy_filename="entropy_${moiety_name}_${div}.txt"
	#echo "/home/yao/programs_src/pdb2entropy/pdb2entropy all_model_pdbs/${pdb_filename} /home/yao/programs_src/pdb2entropy/tors_next_def.dat all_model_pdbs/${entropy_filename} -mi -kmi 1 -nt 8"
        /home/yao/programs_src/pdb2entropy/pdb2entropy all_model_pdbs/${pdb_filename} /home/yao/programs_src/pdb2entropy/tors_next_def.dat all_model_pdbs/${entropy_filename} -mi -kmi 1 -nt 8


        #Calculate protein translational-rotational entropy relative to ligand
        tr_entropy_filename="tr_entropy_${moiety_name}_${div}.txt"
        resnum=$(grep "ATOM" all_model_pdbs/${pdb_filename} | tail -n 1 | awk '{print $6}')
        let "protein_resnum=${resnum} - 1"

        protein_backbone_str="\"A:1-${protein_resnum}:N,CA,C\""
        echo "Protein str: ${protein_backbone_str}"

        #Filter for ligand heavy atom name
        ligand_atomname_str_temp="\"A:${resnum}:"
        ligand_atomname_str_temp+=$(awk '{if($1 == "ATOM" && $6 == x && $10 != "H") printf $3","}' x=${resnum} ${i}/1_renamed.pdb)

        ligand_atomname_str=${ligand_atomname_str_temp::-1}
        ligand_atomname_str+="\""
        #echo "Ligand atom name str  ${ligand_atomname_str}"

	echo "/home/yao/programs_src/pdb2trent/pdb2trent  all_model_pdbs/${pdb_filename} all_model_pdbs/${tr_entropy_filename} ${protein_backbone_str} ${ligand_atomname_str} -nt 8"
        /home/yao/programs_src/pdb2trent/pdb2trent  all_model_pdbs/${pdb_filename} all_model_pdbs/${tr_entropy_filename} ${protein_backbone_str} ${ligand_atomname_str} -nt 8

	#Calculate ligand translational-rotational entropy relative to protein
	ligand_tr_entropy_filename="tr_entropy_ligand_${moiety_name}_${div}.txt"
	/home/yao/programs_src/pdb2trent/pdb2trent all_model_pdbs/${pdb_filename} all_ligand_model_pdbs/${ligand_tr_entropy_filename} ${ligand_atomname_str} ${protein_backbone_str}
    done

done

rm -f all_ligand_model_pdbs/*.pdb
for i in $(ls -d frames_ligand/*);do
    moiety_name=$(echo ${i} | sed 's/frames_ligand\///')

    for div in $(seq 1 1 ${ndiv});do
        pdb_filename="${moiety_name}_${div}.pdb"
	#If not the last div, #models in pdb = frame_per_div*ndiv. This is a rounded down number. If last div, equals the total # of pdbs
        if [[ ${div} -ne  ${ndiv} ]];then
            let "num_frames_this_pdb=${frames_per_div}*${div}"
        else
            num_frames_this_pdb=${num_frames}
        fi

	for j in $(seq 1 1 ${num_frames_this_pdb});do
            echo "MODEL       ${j}" >> all_ligand_model_pdbs/${pdb_filename}
            cat ${i}/${j}_renamed.pdb >> all_ligand_model_pdbs/${pdb_filename}
            echo "ENDMDL">> all_ligand_model_pdbs/${pdb_filename}
        done

        #PDB written by cpptraj does not contain chain ID, but pdb2trent requires one. So assign chain A to all ATOM entries. 
        sed -i 's/^\(ATOM.\{17\}\) /\1A/'  all_ligand_model_pdbs/${pdb_filename} ${i}/1_renamed.pdb    


        #Calculate ligand conformational entropy from free ligand MD
        entropy_filename="entropy_${moiety_name}_${div}.txt"
        echo "/home/yao/programs_src/pdb2entropy/pdb2entropy all_ligand_model_pdbs/${pdb_filename} ligand_pdb2entropy_metadata/${moiety_name}.dat all_ligand_model_pdbs/${entropy_filename} -mk -kmi 1 -nt 8"
        /home/yao/programs_src/pdb2entropy/pdb2entropy all_ligand_model_pdbs/${pdb_filename} ligand_pdb2entropy_metadata/${moiety_name}.dat all_ligand_model_pdbs/${entropy_filename} -mi -kmi 1 -nt 8


        #Calculate ligand conformational entropy from complex MD, use ligand-specific meetadata file.
        ligand_in_complex_entropy_filename="in_complex_entropy_${moiety_name}_${div}.txt"
	echo "/home/yao/programs_src/pdb2entropy/pdb2entropy all_model_pdbs/${pdb_filename} ligand_pdb2entropy_metadata/${moiety_name}.dat all_ligand_model_pdbs/${ligand_in_complex_entropy_filename} -mi -kmi 1 -nt 8"
        /home/yao/programs_src/pdb2entropy/pdb2entropy all_model_pdbs/${pdb_filename} ligand_pdb2entropy_metadata/${moiety_name}.dat all_ligand_model_pdbs/${ligand_in_complex_entropy_filename} -mi -kmi 1 -nt 8
    done
done


echo -e "\n\n\n"

echo -e "Protein_conf\tTR_p_rel_l\tLigand_conf"
comment

for i in $(ls -d frames/*);do
    moiety_name=$(echo ${i} | sed 's/frames\///')
    echo ${moiety_name}

    #Do linear regression for protein conf, protein TR, ligand TR, ligand conf free, ligand conf cocomplex. Y=entropy, X=1/simulation_time
    #sx=sum x, sy=sum y, sxx=sum x*x, sxy=sum x*y
    let "sx=0"
    let "sy1=sy2=sy3=sy4=sy5=0"
    let "sxx=0"
    let "sxy1=sxy2=sxy3=sxy4=sxy5=0"
    let "syy1=syy2=syy3=syy4=syy5=0"

    x_array=()
    y1_array=()
    y2_array=()
    y3_array=()
    y4_array=()
    y5_array=()

    for div in $(seq 1 1 ${ndiv});do
        entropy_in_R_unit=$(awk 'FNR==3 {print $1}' all_model_pdbs/entropy_${moiety_name}_${div}.txt)
        entropy_in_kcal_mol=$(bc <<< "scale=6; ${entropy_in_R_unit} * 0.001987" | awk '{printf "%f", $0}')

        tr_entropy_in_R_unit=$(tail -n 3 all_model_pdbs/tr_entropy_${moiety_name}_${div}.txt | head -n 1 | awk '{print $1}')
        tr_entropy_in_kcal_mol=$(bc <<< "scale=6; ${tr_entropy_in_R_unit} * 0.001987" | awk '{printf "%f", $0}')
        #echo -e "${i}\t${tr_entropy_in_kcal_mol}"
        tr_entropy_in_ligand_R_unit=$(tail -n 3 all_ligand_model_pdbs/tr_entropy_ligand_${moiety_name}_${div}.txt | head -n 1 | awk '{print $1}')

        entropy_ligand_free_in_R_unit=$(awk 'FNR==3 {print $1}' all_ligand_model_pdbs/entropy_${moiety_name}_${div}.txt)
        entropy_ligand_complex_in_R_unit=$(awk 'FNR==3 {print $1}' all_ligand_model_pdbs/in_complex_entropy_${moiety_name}_${div}.txt)
        ligand_entropy_diff_in_kcal_mol=$(bc <<< "scale=6; (${entropy_ligand_complex_in_R_unit} - ${entropy_ligand_free_in_R_unit})*0.001987" | awk '{printf "%f", $0}')

        echo -e "${entropy_in_R_unit}\t${tr_entropy_in_R_unit}\t${tr_entropy_in_ligand_R_unit}\t${entropy_ligand_free_in_R_unit}\t${entropy_ligand_complex_in_R_unit}"

        #Begin linear regression
	inverse_sim_time=$(bc <<< "scale=6; ${ndiv} / (${div} * ${num_ns})" | awk '{printf "%f", $0}')

	sx=$(bc <<< "scale=6; ${sx} + ${inverse_sim_time}" | awk '{printf "%f", $0}')
        sxx=$(bc <<< "scale=6; ${sxx} + (${inverse_sim_time} * ${inverse_sim_time})" | awk '{printf "%f", $0}')

        sy1=$(bc <<< "scale=6; ${sy1} + ${entropy_in_R_unit}" | awk '{printf "%f", $0}')
        sy2=$(bc <<< "scale=6; ${sy2} + ${tr_entropy_in_R_unit}" | awk '{printf "%f", $0}')
        sy3=$(bc <<< "scale=6; ${sy3} + ${tr_entropy_in_ligand_R_unit}" | awk '{printf "%f", $0}')
        sy4=$(bc <<< "scale=6; ${sy4} + ${entropy_ligand_free_in_R_unit}" | awk '{printf "%f", $0}')
        sy5=$(bc <<< "scale=6; ${sy5} + ${entropy_ligand_complex_in_R_unit}" | awk '{printf "%f", $0}')

        sxy1=$(bc <<< "scale=6; ${sxy1} + ${inverse_sim_time} * ${entropy_in_R_unit}" | awk '{printf "%f", $0}')
        sxy2=$(bc <<< "scale=6; ${sxy2} + ${inverse_sim_time} * ${tr_entropy_in_R_unit}" | awk '{printf "%f", $0}')
        sxy3=$(bc <<< "scale=6; ${sxy3} + ${inverse_sim_time} * ${tr_entropy_in_ligand_R_unit}" | awk '{printf "%f", $0}')
        sxy4=$(bc <<< "scale=6; ${sxy4} + ${inverse_sim_time} * ${entropy_ligand_free_in_R_unit}" | awk '{printf "%f", $0}')
        sxy5=$(bc <<< "scale=6; ${sxy5} + ${inverse_sim_time} * ${entropy_ligand_complex_in_R_unit}" | awk '{printf "%f", $0}')

        syy1=$(bc <<< "scale=6; ${syy1} + ${entropy_in_R_unit} * ${entropy_in_R_unit}" | awk '{printf "%f", $0}')
        syy2=$(bc <<< "scale=6; ${syy2} + ${tr_entropy_in_R_unit} * ${tr_entropy_in_R_unit}" | awk '{printf "%f", $0}')
        syy3=$(bc <<< "scale=6; ${syy3} + ${tr_entropy_in_ligand_R_unit} * ${tr_entropy_in_ligand_R_unit}" | awk '{printf "%f", $0}')
        syy4=$(bc <<< "scale=6; ${syy4} + ${entropy_ligand_free_in_R_unit} * ${entropy_ligand_free_in_R_unit}" | awk '{printf "%f", $0}')
        syy5=$(bc <<< "scale=6; ${syy5} + ${entropy_ligand_complex_in_R_unit} * ${entropy_ligand_complex_in_R_unit}" | awk '{printf "%f", $0}')
       
        x_array[${#x_array[@]}]=${inverse_sim_time}
        y1_array[${#y1_array[@]}]=${entropy_in_R_unit}
        y2_array[${#y2_array[@]}]=${tr_entropy_in_R_unit}
        y3_array[${#y3_array[@]}]=${tr_entropy_in_ligand_R_unit}
        y4_array[${#y4_array[@]}]=${entropy_ligand_free_in_R_unit}
        y5_array[${#y5_array[@]}]=${entropy_ligand_complex_in_R_unit}
    done

    x_avg=$(bc <<< "scale=6; ${sx} / ${ndiv}" | awk '{printf "%f", $0}')
    y1_avg=$(bc <<< "scale=6; ${sy1} / ${ndiv}" | awk '{printf "%f", $0}')
    y2_avg=$(bc <<< "scale=6; ${sy2} / ${ndiv}" | awk '{printf "%f", $0}')
    y3_avg=$(bc <<< "scale=6; ${sy3} / ${ndiv}" | awk '{printf "%f", $0}')
    y4_avg=$(bc <<< "scale=6; ${sy4} / ${ndiv}" | awk '{printf "%f", $0}')
    y5_avg=$(bc <<< "scale=6; ${sy5} / ${ndiv}" | awk '{printf "%f", $0}')

    xy1_avg=$(bc <<< "scale=6; ${sxy1} / ${ndiv}")
    xy2_avg=$(bc <<< "scale=6; ${sxy2} / ${ndiv}")
    xy3_avg=$(bc <<< "scale=6; ${sxy3} / ${ndiv}")
    xy4_avg=$(bc <<< "scale=6; ${sxy4} / ${ndiv}")
    xy5_avg=$(bc <<< "scale=6; ${sxy5} / ${ndiv}")

    xx_avg=$(bc <<< "scale=6; ${sxx} / ${ndiv}" | awk '{printf "%f", $0}')
    yy1_avg=$(bc <<< "scale=6; ${syy1} / ${ndiv}" | awk '{printf "%f", $0}')
    yy2_avg=$(bc <<< "scale=6; ${syy2} / ${ndiv}" | awk '{printf "%f", $0}')
    yy3_avg=$(bc <<< "scale=6; ${syy3} / ${ndiv}" | awk '{printf "%f", $0}')
    yy4_avg=$(bc <<< "scale=6; ${syy4} / ${ndiv}" | awk '{printf "%f", $0}')
    yy5_avg=$(bc <<< "scale=6; ${syy5} / ${ndiv}" | awk '{printf "%f", $0}')

    let "up1=up2=up3=up4=up5=0"
    let "down=0"
    for div in $(seq 1 1 ${ndiv});do
        let "index=${div}-1"

        x_minus_avg=$(bc <<< "scale=6; ${x_array[index]} - ${x_avg}" | awk '{printf "%f", $0}')
	down=$(bc <<< "scale=6; ${down} + ${x_minus_avg} * ${x_minus_avg}" | awk '{printf "%f", $0}')

        y1_minus_avg=$(bc <<< "scale=6; ${y1_array[index]} - ${y1_avg}" | awk '{printf "%f", $0}')
	up1=$(bc <<< "scale=6; ${up1} + ${x_minus_avg} * ${y1_minus_avg}" | awk '{printf "%f", $0}')

        y2_minus_avg=$(bc <<< "scale=6; ${y2_array[index]} - ${y2_avg}" | awk '{printf "%f", $0}')
	up2=$(bc <<< "scale=6; ${up2} + ${x_minus_avg} * ${y2_minus_avg}" | awk '{printf "%f", $0}')

        y3_minus_avg=$(bc <<< "scale=6; ${y3_array[index]} - ${y3_avg}" | awk '{printf "%f", $0}')
	up3=$(bc <<< "scale=6; ${up3} + ${x_minus_avg} * ${y3_minus_avg}" | awk '{printf "%f", $0}')

        y4_minus_avg=$(bc <<< "scale=6; ${y4_array[index]} - ${y4_avg}" | awk '{printf "%f", $0}')
	up4=$(bc <<< "scale=6; ${up4} + ${x_minus_avg} * ${y4_minus_avg}" | awk '{printf "%f", $0}')

        y5_minus_avg=$(bc <<< "scale=6; ${y5_array[index]} - ${y5_avg}" | awk '{printf "%f", $0}')
	up5=$(bc <<< "scale=6; ${up5} + ${x_minus_avg} * ${y5_minus_avg}" | awk '{printf "%f", $0}')
    done

    slope1=$(bc <<< "scale=6; ${up1} / ${down}" | awk '{printf "%f", $0}')
    intercept1=$(bc <<< "scale=6; ${y1_avg} - (${slope1} * ${x_avg})" | awk '{printf "%f", $0}')
    slope1_kcal_mol=$(bc <<< "scale=6; ${slope1} * 0.001987" | awk '{printf "%f", $0}')
    intercept1_kcal_mol=$(bc <<< "scale=6; ${intercept1} * 0.001987" | awk '{printf "%f", $0}')

    slope2=$(bc <<< "scale=6; ${up2} / ${down}" | awk '{printf "%f", $0}')
    intercept2=$(bc <<< "scale=6;${y2_avg} - (${slope2} * ${x_avg})" | awk '{printf "%f", $0}')
    slope2_kcal_mol=$(bc <<< "scale=6; ${slope2} * 0.001987" | awk '{printf "%f", $0}')
    intercept2_kcal_mol=$(bc <<< "scale=6; ${intercept2} * 0.001987" | awk '{printf "%f", $0}')

    slope3=$(bc <<< "scale=6; ${up3} / ${down}" | awk '{printf "%f", $0}')
    intercept3=$(bc <<< "scale=6; ${y3_avg} - (${slope3} * ${x_avg})" | awk '{printf "%f", $0}')
    slope3_kcal_mol=$(bc <<< "scale=6; ${slope3} * 0.001987" | awk '{printf "%f", $0}')
    intercept3_kcal_mol=$(bc <<< "scale=6; ${intercept3} * 0.001987" | awk '{printf "%f", $0}')

    slope4=$(bc <<< "scale=6; ${up4} / ${down}" | awk '{printf "%f", $0}')
    intercept4=$(bc <<< "scale=6; ${y4_avg} - (${slope4} * ${x_avg})" | awk '{printf "%f", $0}')
    slope4_kcal_mol=$(bc <<< "scale=6; ${slope4} * 0.001987" | awk '{printf "%f", $0}')
    intercept4_kcal_mol=$(bc <<< "scale=6; ${intercept4} * 0.001987" | awk '{printf "%f", $0}')

    slope5=$(bc <<< "scale=6; ${up5} / ${down}" | awk '{printf "%f", $0}')
    intercept5=$(bc <<< "scale=6; ${y5_avg} - (${slope5} * ${x_avg})" | awk '{printf "%f", $0}')
    slope5_kcal_mol=$(bc <<< "scale=6; ${slope5} * 0.001987" | awk '{printf "%f", $0}')
    intercept5_kcal_mol=$(bc <<< "scale=6; ${intercept5} * 0.001987" | awk '{printf "%f", $0}')

    r1=$(bc <<< "scale=6; (${xy1_avg} - (${x_avg} * ${y1_avg})) / sqrt((${xx_avg} - ${x_avg} * ${x_avg}) * (${yy1_avg} - ${y1_avg} * ${y1_avg}))" | awk '{printf "%f", $0}')
    r2=$(bc <<< "scale=6; (${xy2_avg} - (${x_avg} * ${y2_avg})) / sqrt((${xx_avg} - ${x_avg} * ${x_avg}) * (${yy2_avg} - ${y2_avg} * ${y2_avg}))" | awk '{printf "%f", $0}')
    r3=$(bc <<< "scale=6; (${xy3_avg} - (${x_avg} * ${y3_avg})) / sqrt((${xx_avg} - ${x_avg} * ${x_avg}) * (${yy3_avg} - ${y3_avg} * ${y3_avg}))" | awk '{printf "%f", $0}')
    r4=$(bc <<< "scale=6; (${xy4_avg} - (${x_avg} * ${y4_avg})) / sqrt((${xx_avg} - ${x_avg} * ${x_avg}) * (${yy4_avg} - ${y4_avg} * ${y4_avg}))" | awk '{printf "%f", $0}')
    r5=$(bc <<< "scale=6; (${xy5_avg} - (${x_avg} * ${y5_avg})) / sqrt((${xx_avg} - ${x_avg} * ${x_avg}) * (${yy5_avg} - ${y5_avg} * ${y5_avg}))" | awk '{printf "%f", $0}')

    r1_sqr=$(bc <<< "scale=6; ${r1}*${r1}" | awk '{printf "%f", $0}')
    r2_sqr=$(bc <<< "scale=6; ${r2}*${r2}" | awk '{printf "%f", $0}')
    r3_sqr=$(bc <<< "scale=6; ${r3}*${r3}" | awk '{printf "%f", $0}')
    r4_sqr=$(bc <<< "scale=6; ${r4}*${r4}" | awk '{printf "%f", $0}')
    r5_sqr=$(bc <<< "scale=6; ${r5}*${r5}" | awk '{printf "%f", $0}')

    ligand_entropy_complex_minus_free=$(bc <<< "scale=6; ${intercept5_kcal_mol} - ${intercept4_kcal_mol}" | awk '{printf "%f", $0}')

    echo -e "1\t${intercept1_kcal_mol}\t${slope1_kcal_mol}\t${r1_sqr}"
    echo -e "2\t${intercept2_kcal_mol}\t${slope2_kcal_mol}\t${r2_sqr}"
    echo -e "3\t${intercept3_kcal_mol}\t${slope3_kcal_mol}\t${r3_sqr}"
    echo -e "4\t${intercept4_kcal_mol}\t${slope4_kcal_mol}\t${r4_sqr}"
    echo -e "5\t${intercept5_kcal_mol}\t${slope5_kcal_mol}\t${r5_sqr}"
    echo ""

    echo -e "${intercept1_kcal_mol}\t${intercept2_kcal_mol}\t${intercept3_kcal_mol}\t${ligand_entropy_complex_minus_free}"
    echo ""
    echo ""
done
