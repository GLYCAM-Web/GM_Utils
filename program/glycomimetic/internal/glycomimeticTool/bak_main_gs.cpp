#include "gridsearch_pthread.hpp"
#include "open_valence_derivative_moiety.hpp"
#include "utility.hpp"

#include "amber_handling.hpp"

typedef std::vector<std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*> > > open_valence_atoms_and_derivatize_location;
typedef std::vector<MolecularModeling::Atom*> AtomVector;

std::vector<OpenValence*> GetOpenValenceSideGroupSp3Oxygens (CoComplex* cocomplex, std::vector<Glycan::Monosaccharide*>& monos, std::vector<open_valence_option>& open_valence_options, int num_threads);

std::pair<double, std::vector<double> > GridSearching(AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, std::vector<AtomVector>& all_torsions, int rotation_interval, int num_threads, std::vector<double>& crystal_torsion_values, double chpi_weight);

void GridSearchingByMultipleThreads(int coord_index, std::vector<AtomVector>& all_torsions, std::vector<int>& thread_start_torsion_values, int interval, int num_rotamers_to_sample, double* highest_affinity_ptr, pthread_mutex_t* mutex_ptr, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, std::vector<double>* highest_affinity_torsions_ptr, std::vector<double>& crystal_torsion_values, double chpi_weight);

namespace fs = ::boost::filesystem;
std::vector<std::string> glob_for_pattern(const fs::path& root, const std::string& ext);

void GridSearchingForOpenValenceAtoms(CoComplex* cocomplex, std::vector<OpenValence*>& open_valences, std::vector<DerivativeMoiety*>& all_moieties, int interval, int num_threads, std::string output_pdb_path, std::string& logfile_path);

void ProcessOptions(int argc, char* argv[], int& interval, int& max_num_threads, int& num_threads, std::string& ext, std::string& cocrystal_pdb_path, std::string& moiety_path, std::string& output_pdb_path, std::string& logfile_path, std::vector<open_valence_option> & open_valence_options);

std::vector<std::pair<MolecularModeling::Atom*, std::string> > GetRequestedOpenValenceAtoms(std::vector<Glycan::Monosaccharide*> monos, std::map<int, std::vector<std::pair<std::string, std::string> > >& open_valence_index_atom_names_derivatize_types);

double RMSD(AtomVector& target_atoms, AtomVector& reference_atoms, int coord_index);

int main(int argc, char* argv[])
{
    //Read torsion token
    std::map<std::string, std::vector<std::string> > torsion_strs;
    std::map<std::string, std::string> pdbid_resnum;
    std::ifstream torsion_file ("/home/yao/GLYCAM_Dev_Env/V_2/Web_Programs/gems/glycomimetics/good_chpi_gs/torsion_tokens.txt");
    //std::ifstream torsion_file ("./torsion_tokens.txt");
    std::string line;
    while (std::getline(torsion_file, line)){
        std::vector<std::string> tab_split = gmml::Split(line, "@");
	pdbid_resnum[tab_split[0]] = tab_split[1];
	std::stringstream stream;
	stream << tab_split[2];
	std::string tor_str;
	std::vector<std::string> tor_str_vec;
	while(std::getline(stream, tor_str, ',')){
	    tor_str_vec.push_back(tor_str);
	}
	torsion_strs[tab_split[0]] = tor_str_vec;
    }
    //std::exit(1);

    //requested_residue_index_str
    //glycomimetics
    typedef std::vector<Glycan::Oligosaccharide*> OligosaccharideVector;
    typedef std::vector<MolecularModeling::Atom*> AtomVector;
    typedef std::vector<std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*> > > open_valence_atoms_and_derivatize_location;

    int interval = 10;
    int max_num_threads = 4;
    int num_threads = 4; 	//When receptor is being rotated, can only use 1 thread. 
    std::string receptor_pdbqt_path;
    std::string ligand_pdbqt_path;
    std::string output_pdb_path;
    std::vector<AtomVector> torsions;
    std::string pdb_id;
    double chpi_weight = wt_ch_pi; 
    std::string logfile_path;
    //std::vector<std::string> torsion_strs;

    std::vector<open_valence_option> open_valence_options;
    int option = 0;
    //std::string requested_residue_index_str;
    while ((option = getopt(argc, argv, "r:l:i:o:p:n:w:f:")) != -1){  //Later restore -t option?
        switch (option) {
            case 114: { //-r receptor pdbqt path
                receptor_pdbqt_path = std::string(optarg);
                break;
            }
            case 108:{//-l for ligand pdbqt file
                ligand_pdbqt_path = std::string(optarg);
		break;
            }
            case 105: { //-i
                interval = std::stoi(std::string(optarg));
                break;
            }
            case 111:{ //-o
                output_pdb_path = std::string(optarg);
                break;
            }
            /*case 116:{ //-t for torsions
	        std::string torsion_arg_str = std::string(optarg);
		torsion_strs.push_back(torsion_arg_str);
                break;
            }*/
            case 112:{ //-p for pdb_id
	        pdb_id = std::string(optarg);
	        break;	     
            }
            case 119:{ //-w for external chpi weight
		chpi_weight = std::stod(optarg);
		break;
	    }
            case 102:{ //-f for logfile
                logfile_path = std::string(optarg);
		break;
	    }
            /*case 110:{ //-n for requested residue number
	        requested_residue_index_str = std::string(optarg);
		std::cout << "Requested res str: " << requested_residue_index_str << std::endl;
		break;
	    }*/
        }
    }

    std::vector<std::string> amino_libs;
    amino_libs.push_back("../../gems/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/amino12.lib");
    amino_libs.push_back("../../gems/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminoct12.lib");
    amino_libs.push_back("../../gems/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminont12.lib");
    std::string prep = "/programs/gems/gmml/dat/prep/GLYCAM_06j-1.prep";

    std::ofstream log(logfile_path, std::ios::app);
    if (log.fail()){
        std::cout << "Failed to open " << logfile_path << std::endl;
	std::exit(1);
    }

    MolecularModeling::Assembly receptor_assembly = MolecularModeling::Assembly(receptor_pdbqt_path, gmml::InputFileType::PDBQT);
    MolecularModeling::Assembly ligand_assembly = MolecularModeling::Assembly(ligand_pdbqt_path, gmml::InputFileType::PDBQT);
    VinaBondByDistance(receptor_assembly, vina_atom_data);
    VinaBondByDistance(ligand_assembly, vina_atom_data);

    //Build receptor and ligand assembly to get rec/lig atoms
    std::vector<MolecularModeling::Residue*> ligand_residues = ligand_assembly.GetResidues();
    std::vector<MolecularModeling::Residue*> receptor_residues = receptor_assembly.GetResidues();

    AtomVector ligand_atoms = ligand_assembly.GetAllAtomsOfAssembly();
    AtomVector receptor_atoms = receptor_assembly.GetAllAtomsOfAssembly();

    DuplicateAtomNodesAndCoordinates(ligand_atoms, num_threads);
    DuplicateAtomNodesAndCoordinates(receptor_atoms, num_threads);

    AtomVector requested_residue_atoms;
    
    std::string requested_residue_index_str = pdbid_resnum[pdb_id];
    //std::cout << "Requested residue index: " << requested_residue_index_str << std::endl;

    // -11 indicates gridsearching ligand instead of protein.
    std::vector<MolecularModeling::Residue*> residues_for_gridsearching = (requested_residue_index_str == "-11") ? ligand_residues : receptor_residues;

    MolecularModeling::Assembly ligand_assembly_ref = MolecularModeling::Assembly(ligand_pdbqt_path, gmml::InputFileType::PDBQT);
    MolecularModeling::Assembly receptor_assembly_ref = MolecularModeling::Assembly(receptor_pdbqt_path, gmml::InputFileType::PDBQT);

    AtomVector requested_residue_atoms_ref;

    for (unsigned int i = 0; i < residues_for_gridsearching.size(); i++){
        MolecularModeling::Residue* this_receptor_residue = residues_for_gridsearching[i];
	std::string this_residue_id = this_receptor_residue->GetId();
	//std::cout << "This res id: " << this_residue_id << std::endl;
	std::vector<std::string> id_underscore_split_token = gmml::Split(this_residue_id, "_");

	std::string residue_index_str;
	if (id_underscore_split_token.size() == 6){ //Residue id
	    residue_index_str = id_underscore_split_token[2];
	}
	else if (id_underscore_split_token.size() == 8){ //Atom id
	    residue_index_str = id_underscore_split_token[4];
	}
	else{
	    std::cout << "Failed to find residue index in ID" << std::endl;
	    std::exit(1);
	}

	if (requested_residue_index_str == "-11"){
	    //AtomVector this_residue_atoms = this_receptor_residue->GetAtoms();
	    AtomVector this_residue_atoms = ligand_assembly.GetAllAtomsOfAssembly();
	    requested_residue_atoms = this_residue_atoms;
	    //requested_residue_atoms_ref = ligand_assembly_ref.GetResidues()[i]->GetAtoms(); 
	    requested_residue_atoms_ref = ligand_assembly_ref.GetAllAtomsOfAssembly(); 
	    //std::cout << "Found residue: " << this_residue_id << std::endl;
	}
	else if (requested_residue_index_str == residue_index_str){
	    AtomVector this_residue_atoms = this_receptor_residue->GetAtoms();
	    requested_residue_atoms = this_residue_atoms;
	    requested_residue_atoms_ref = receptor_assembly_ref.GetResidues()[i]->GetAtoms();
	    //std::cout << "Found residue: " << this_residue_id << std::endl;
	}
    }

    for (std::map<std::string, std::vector<std::string> >::iterator mapit = torsion_strs.begin(); mapit != torsion_strs.end(); mapit++){
	if (mapit->first == pdb_id){
	    std::vector<std::string>& tor_tokens = mapit->second;
	    for (unsigned int i = 0; i < tor_tokens.size(); i++){
                std::vector<std::string> torsion_atom_names = gmml::Split(tor_tokens[i], "-");
                AtomVector this_torsion;
                for (unsigned int j = 0; j < 4; j++){
                    this_torsion.push_back(GetAtomByName(torsion_atom_names[j], requested_residue_atoms));
                }
                torsions.push_back(this_torsion);
	    }
	    break;
	}
    }

    VinaScorePrerequisites requisites(ligand_atoms, receptor_atoms);
    std::vector<double> affinities = VinaScoreInPlaceGS(requisites, chpi_weight, 0);

    double total_affinity = affinities[0];
    std::cout << "reference affinity: " << total_affinity << std::endl;
    //std::exit(1);

    std::vector<double> crystal_torsion_values;
    for (unsigned int i = 0; i < torsions.size(); i++){
        crystal_torsion_values.push_back(GetDihedral(torsions[i][0], torsions[i][1], torsions[i][2], torsions[i][3], 0));
    }

    std::pair<double, std::vector<double> > top_affinity_torsion_values = (requested_residue_index_str == "-11") ? GridSearching(receptor_atoms, ligand_atoms, requested_residue_atoms, torsions, interval, num_threads, crystal_torsion_values, chpi_weight) : GridSearching(ligand_atoms, receptor_atoms, requested_residue_atoms, torsions, interval, num_threads, crystal_torsion_values, chpi_weight) ;

    //std::pair<double, std::vector<double> > top_affinity_torsion_values = GridSearching(receptor_atoms, ligand_atoms, ligand_atoms, torsions, interval, num_threads, crystal_torsion_values);
    std::vector<double>& top_torsion_values = top_affinity_torsion_values.second;

    //std::cout << "Highest affinity: " << top_affinity_torsion_values.first << std::endl;
    for (unsigned int i = 0; i < top_torsion_values.size(); i++){
	//std::cout << "Top torsion: " << top_torsion_values[i] << std::endl;
        SetDihedral(torsions[i][0], torsions[i][1], torsions[i][2], torsions[i][3], top_torsion_values[i] + crystal_torsion_values[i], 0);
    }
    //std::cout << "Highest affinity again: " << VinaScoreInPlaceGS(ligand_atoms, receptor_atoms, atom_xs_type_map, ligand_aromatic_cycles, receptor_aromatic_cycles)[0] << std::endl;

    MolecularModeling::Assembly best_cocomplex;
    for (unsigned int i = 0; i < receptor_residues.size(); i++){
        best_cocomplex.AddResidue(receptor_residues[i]);
    }
    for (unsigned int i = 0; i < ligand_residues.size(); i++){
        best_cocomplex.AddResidue(ligand_residues[i]);
    }

    std::string best_complex_name = "/home/yao/GLYCAM_Dev_Env/V_2/Web_Programs/gems/glycomimetics/good_chpi_gs/top_pose_pdbs/";
    best_complex_name += pdb_id;
    best_complex_name += "_best_pose.pdb";
    best_cocomplex.BuildPdbFileStructureFromAssembly()->Write(best_complex_name);

    /*for (unsigned int i = 0; i < torsions.size(); i++){
	AtomVector torsion_rotated_atoms;
	torsion_rotated_atoms.push_back(torsions[i][1]);
        torsions[i][2]->FindConnectedAtoms(torsion_rotated_atoms);

	torsion_rotated_atoms.erase(torsion_rotated_atoms.begin());
	torsion_rotated_atoms.erase(torsion_rotated_atoms.begin());

	double top_pose_rmsd_this_torsion = RMSD(torsion_rotated_atoms, requested_residue_atoms_ref, 0);
	std::cout << "This torsion atom size: " << torsion_rotated_atoms.size() << " Actual value: " << top_torsion_values[i] + crystal_torsion_values[i] 
		  << " Rotation value: " << top_torsion_values[i] << " Top pose rmsd: " << top_pose_rmsd_this_torsion << std::endl;
	//std::cout << "Actual value: " << GetDihedral(torsions[i][0], torsions[i][1], torsions[i][2], torsions[i][3], 0) << std::endl;
    }*/

    double total_distance_squared = 0.000;
    for (unsigned int i = 0; i < torsions.size(); i++){
	double converted_angle_in_rad = CHpiConvertAngle2FirstQuadrant(top_torsion_values[i] / 180.00 * 3.1415);
	double converted_angle_in_deg = converted_angle_in_rad / 3.1415 * 180;

	std::cout << std::fixed << std::setprecision(0) << converted_angle_in_deg << " ";
	log << std::fixed << std::setprecision(0) << converted_angle_in_deg << " ";

        total_distance_squared += std::pow(converted_angle_in_deg /interval, 2);
    }

    if (torsions.size() == 1){
        std::cout << "0 ";
	log << "0 ";
    }

    log << std::fixed << std::setprecision(2) << std::sqrt(total_distance_squared) << std::endl;
    std::cout << std::fixed << std::setprecision(0) << std::sqrt(total_distance_squared) << std::endl;
    log.close();

    //double top_pose_rmsd = RMSD(ligand_atoms, ligand_ref_atoms, 0);
    //std::cout << "Top pose rmsd: " << top_pose_rmsd << std::endl;

    /*PdbFileSpace::PdbFile* top_ligand_pose = ligand_assembly.BuildPdbFileStructureFromAssembly();
    std::string best_pose_path = "/home/yao/GLYCAM_Dev_Env/V_2/Web_Programs/gems/glycomimetics/test_pdbs/";
    best_pose_path += pdb_id;
    best_pose_path += "_top_ligand_pose.pdb";
    top_ligand_pose->Write(best_pose_path);*/
    //std::exit(1);
} 

std::pair<double, std::vector<double> > GridSearching(AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, std::vector<AtomVector>& all_torsions, int interval, int num_threads, std::vector<double> & crystal_torsion_values, double chpi_weight){

    //std::cout << "Start gridsearching" << std::endl;
    double floatpart,angles_per_torsion;
    floatpart = std::modf(360/interval, &angles_per_torsion);

    int rotamer_count = std::pow(angles_per_torsion, all_torsions.size());
    //std::cout << "Rotamer count is: " << rotamer_count << std::endl;
    pthread_t tid[num_threads];


    pthread_mutex_t lock;
    PtheadGridSearching::thread_args argstruct[num_threads];//(all_torsions, &lock);

    if (pthread_mutex_init(&lock, NULL) != 0) {
	std::cout << "Pthread mutex init failed" << std::endl;
	std::exit(1);
    }

    std::vector<int> thread_start_torsion_values(all_torsions.size(), 0);

    int unassigned_rotamer_count = rotamer_count;
    for (unsigned int i = 0; i < num_threads; i++){
	
        int unassigned_rotamer_count_this_thread = int (rotamer_count / num_threads); //If not the last thread, every other thread gets this many rotamers
	if (i == num_threads -1){ //If this is the very last thread, get all remaining threads.
	    unassigned_rotamer_count_this_thread = unassigned_rotamer_count;
	}

	unassigned_rotamer_count -= unassigned_rotamer_count_this_thread;

	int thread_rotamers_count = unassigned_rotamer_count_this_thread;
	argstruct[i] = PtheadGridSearching::thread_args(i, all_torsions, &lock, thread_rotamers_count, interval, receptor_atoms, moiety_atoms, ligand_atoms, crystal_torsion_values, chpi_weight);
        argstruct[i].this_thread_start_torsion_values = thread_start_torsion_values;

	int thread_end_torsion_values[all_torsions.size()];
        for (unsigned int j = 0; j < all_torsions.size(); j++){
	    int power = all_torsions.size() - 1 - j;
	    int num_rotamers_per_increment = std::pow(angles_per_torsion, power);
	    int num_increments = int (unassigned_rotamer_count_this_thread / num_rotamers_per_increment);
	    thread_end_torsion_values[j] = interval * num_increments;
	    unassigned_rotamer_count_this_thread -= (num_rotamers_per_increment * num_increments);
	}   

	//Assign rotamers for next thread
	if (i != num_threads -1){
	    for (unsigned int j = 0; j < all_torsions.size(); j++){
                thread_start_torsion_values[j] += thread_end_torsion_values[j];
	    }

            for (unsigned int j = all_torsions.size() -1; j >0; j--){
                if (thread_start_torsion_values[j] >= 360){
                    thread_start_torsion_values[j] = 0;
                    thread_start_torsion_values[j-1] += interval;
                }
            }
	}
    }
	
    for (unsigned int i = 0; i < num_threads; i++){
	//Create a child thread
	int success_status = pthread_create(&tid[i], NULL, &GridSearchingByMultipleThreadsStartRoutine, &argstruct[i]);
    }

    for (unsigned int i = 0; i < num_threads; i++){
        pthread_join(tid[i], NULL);
    }
    pthread_mutex_destroy(&lock);

    std::map<double, std::vector<double> > thread_highest_affinity_torsion_value_map;
    for (unsigned int i = 0; i < num_threads; i++){
        thread_highest_affinity_torsion_value_map[argstruct[i].highest_affinity] = argstruct[i].hightest_affinity_torsion_values;
	/*std::cout << "Thread: " << i << " after gridsearching highest aff val and tors val: " << argstruct[i].highest_affinity << std::endl; 
	for (unsigned int j = 0; j < argstruct[i].hightest_affinity_torsion_values.size(); j++){
	    std::cout << "Highest affinity torsion: " << argstruct[i].hightest_affinity_torsion_values[j] << std::endl;
	}*/
    }
    
    //Return the highest affinity and the associated torsion values.
    return std::pair<double, std::vector<double> >(thread_highest_affinity_torsion_value_map.begin()->first, thread_highest_affinity_torsion_value_map.begin()->second);
}

void GridSearchingByMultipleThreads(int coord_index, std::vector<AtomVector>& all_torsions, std::vector<int>& thread_start_torsion_values, int interval, int num_rotamers_to_sample, double* highest_affinity_ptr, pthread_mutex_t* mutex_ptr, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, std::vector<double>* highest_affinity_torsions_ptr, std::vector<double>& crystal_torsion_values, double chpi_weight){

    int start_value = 0;
    int end_value = 359;
    std::cout << "start here" << std::endl;
  
    int rotation_values[all_torsions.size()];
    for (unsigned int a = 0; a < thread_start_torsion_values.size(); a++){
        rotation_values[a] = thread_start_torsion_values[a];
    }

    for (std::vector<AtomVector>::iterator it = all_torsions.begin(); it != all_torsions.end(); it++){
	int index = std::distance(all_torsions.begin(), it);
        SetDihedral((*it)[0], (*it)[1], (*it)[2], (*it)[3], rotation_values[index] + crystal_torsion_values[index], coord_index);
    }

    AtomVector moiety_atoms_no_h;
    for (unsigned int i = 0; i < moiety_atoms.size(); i++){
        if (moiety_atoms[i]->GetElementSymbol() != "H"){
	    moiety_atoms_no_h.push_back(moiety_atoms[i]);  
	}
    }
    AtomVector ligand_plus_moiety_atoms_no_h = moiety_atoms_no_h;
    for (unsigned int i = 0; i < ligand_atoms.size(); i++){
        if (ligand_atoms[i]->GetElementSymbol() != "H"){
	    ligand_plus_moiety_atoms_no_h.push_back(ligand_atoms[i]);
	}
    }

    /*std::map<MolecularModeling::Atom*, std::string> atom_xs_type_map;
    ObtainAtomXsType(moiety_atoms, atom_xs_type_map);
    ObtainAtomXsType(ligand_atoms, atom_xs_type_map);
    ObtainAtomXsType(receptor_atoms, atom_xs_type_map);

    std::vector<MolecularModeling::Residue*> receptor_residues;
    for (unsigned int i = 0; i < receptor_atoms.size(); i++){
        MolecularModeling::Residue* this_atom_residue = receptor_atoms[i]->GetResidue(); 
	if (std::find(receptor_residues.begin(), receptor_residues.end(), this_atom_residue) == receptor_residues.end()){
	    receptor_residues.push_back(this_atom_residue);
	}
    }

    std::vector<AtomVector> receptor_aromatic_rings = DetectAromaticCycles(receptor_residues);
    std::vector<AtomVector> ligand_aromatic_rings = DetectAromaticCycles(ligand_atoms);
    
    std::vector<GeometryTopology::Coordinate> receptor_ring_centroids = GetGeometricCenter(receptor_aromatic_rings, coord_index);
    std::vector<GeometryTopology::Coordinate> receptor_ring_normals = GetPlaneNormal(receptor_aromatic_rings, coord_index);*/

    VinaScorePrerequisites prerequisites(ligand_atoms, receptor_atoms);

    for (unsigned int rotamer_sampled = 0; rotamer_sampled < num_rotamers_to_sample;){
	unsigned int i = (rotamer_sampled == 0) ? rotation_values[all_torsions.size() -1] : start_value;
        for (; i <= end_value; i += interval){
            rotation_values[all_torsions.size() -1] = i;
            SetDihedral(all_torsions.back()[0], all_torsions.back()[1], all_torsions.back()[2], all_torsions.back()[3], i + crystal_torsion_values.back(), coord_index);

            if (!InternalClashesExist(moiety_atoms, ligand_atoms, coord_index)){
		/*std::vector<double> affinities = VinaScoreInPlaceGS(ligand_atoms, receptor_atoms, atom_xs_type_map, ligand_aromatic_rings, receptor_aromatic_rings, 
				                                    receptor_ring_centroids, receptor_ring_normals, chpi_weight, coord_index);*/
		std::vector<double> affinities = VinaScoreInPlaceGS(prerequisites, chpi_weight, coord_index);
                double moiety_affinity = affinities[0];
		/*for (int k = 0; k < all_torsions.size(); k++){
		    int value_for_printing = ((rotation_values[k] < 180) ? rotation_values[k]: rotation_values[k]-360);
                    std::cout << value_for_printing << "\t";
		}
		std::cout << moiety_affinity << std::endl;*/

                if (moiety_affinity < *(highest_affinity_ptr)){
                    *(highest_affinity_ptr) = moiety_affinity;
		    //std::cout << "Update affinity upon no clash to " << *(highest_affinity_ptr) << std::endl;
                    for (int k = 0; k < all_torsions.size(); k++){
                        (*highest_affinity_torsions_ptr)[k] = rotation_values[k];
                    }
                }
            }

	    //Printing statements
	    /*std::cout << "Presumably sampled: ";
	    for (unsigned int i = 0; i < all_torsions.size(); i++){
                std::cout << rotation_values[i] << "-";
	    }
            std::cout << std::endl;
	    std::cout << "But actual torsion value is: ";
	    for (unsigned int i = 0; i < all_torsions.size(); i++){
                std::cout << GetDihedral(all_torsions[i][0], all_torsions[i][1], all_torsions[i][2], all_torsions[i][3], coord_index) << "-";
	    }
	    std::cout << std::endl;*/

            rotamer_sampled++;
        }

        for (int j = all_torsions.size()-1; j>=0; j--){
            if (rotation_values[j] + interval <= end_value){
                rotation_values[j]+= interval;
                SetDihedral(all_torsions[j][0], all_torsions[j][1], all_torsions[j][2], all_torsions[j][3], rotation_values[j] + crystal_torsion_values[j], coord_index);

                for (unsigned int k = j+1; k < all_torsions.size(); k++){
                    rotation_values[k] = start_value;
                    SetDihedral(all_torsions[k][0], all_torsions[k][1], all_torsions[k][2], all_torsions[k][3], rotation_values[k] + crystal_torsion_values[k], coord_index);
                }
                break;
            }
        }
    }

}

/*std::vector<OpenValence*> GetOpenValenceSideGroupSp3Oxygens (CoComplex* cocomplex, std::vector<Glycan::Monosaccharide*>& monos, std::vector<open_valence_option>& open_valence_options, int num_threads){
    std::vector<OpenValence*> open_valences;
    for (std::vector<Glycan::Monosaccharide*>::iterator it = monos.begin(); it != monos.end(); it++){
	Glycan::Monosaccharide* mono = *it;
	std::vector<AtomVector> side_atoms = mono->side_atoms_;
	AtomVector potential_open_valence_this_residue;
	for (std::vector<AtomVector>::iterator sideit = side_atoms.begin(); sideit != side_atoms.end(); sideit++){
	    AtomVector each_side_position = *sideit;
	    for (AtomVector::iterator atomit = each_side_position.begin(); atomit != each_side_position.end(); atomit++){
		MolecularModeling::Atom* atom = *atomit;
		if (atom != NULL && (atom->GetName().substr(0,1) == "O" || atom->GetName().substr(0,1) == "N")){ //Right now only derivative sidechain oxygens or nitrogens
		    //MolecularModeling::Atom* carbon_neighbor = NULL;
		    MolecularModeling::Atom* hydrogen_to_derivatize = NULL;
		    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();

		    AtomVector carbon_neighbors;
		    for (AtomVector::iterator neighbor_it = neighbors.begin(); neighbor_it != neighbors.end(); neighbor_it++){
		        MolecularModeling::Atom* neighbor = *neighbor_it;
		        if (neighbor->GetName().substr(0,1) != "H"){
		            carbon_neighbors.push_back(neighbor);
			}
			else{
			    hydrogen_to_derivatize = neighbor;
			}
		    }
            
		    if (carbon_neighbors.size() > 0){
			int sp3_neighbor_count = 0;
			for (unsigned int i = 0; i < carbon_neighbors.size(); i++){
			    MolecularModeling::Atom* carbon_neighbor = carbon_neighbors[i];
		            AtomVector carbon_neighbor_neighbors = carbon_neighbor->GetNode()->GetNodeNeighbors();
		            bool carbon_neighbor_is_sp3 = true;
		            if (carbon_neighbor_neighbors.size() == 2 && sideit != side_atoms.end()-1){ //sideit!= side_atoms.end()-1 is the +1 branch, allowing the CH2OH without H situation
			        carbon_neighbor_is_sp3 = false;  //Assuming the absence of sp hybridization in natural sugars, two neighbors means sp2 with hydrogen absent.
			    }
			    else if (carbon_neighbor_neighbors.size() == 3){
			        AtomVector improper_torsion;
			        improper_torsion.push_back(atom);
			        improper_torsion.push_back(carbon_neighbor);
			        for (AtomVector::iterator carbon_neighbor_it = carbon_neighbor_neighbors.begin(); carbon_neighbor_it != carbon_neighbor_neighbors.end(); carbon_neighbor_it++){
			            if (*carbon_neighbor_it != atom){ 
				        improper_torsion.push_back(*carbon_neighbor_it);
				    }
			        }
			 	if (std::abs(std::cos(GetDihedral(improper_torsion[0], improper_torsion[1], improper_torsion[2], improper_torsion[3],0))) > 0.996){ //< 5 deg away from parallel
				    carbon_neighbor_is_sp3 = false; //if improper torsion is close to 0 or 180 deg, then carbon neighbor is planar, hence sp2 carbon.
				}
			    }
			    if (carbon_neighbor_is_sp3){
			        sp3_neighbor_count++;
			    }
		        }

			if (sp3_neighbor_count >0){
			    for(std::vector<open_valence_option>::iterator vec_it = open_valence_options.begin(); vec_it != open_valence_options.end(); vec_it++){
				std::string atom_residue_id = atom->GetResidue()->GetId();
                                std::vector<std::string> underscore_split_token = gmml::Split(atom_residue_id, "_");

				int atom_residue_number = 999999;
				if (underscore_split_token.size() == 6){ //Residue Id
                                    atom_residue_number = std::stoi(underscore_split_token[2]);
				}
				else if (underscore_split_token.size() == 8){ //Atom Id
				    atom_residue_number = std::stoi(underscore_split_token[4]);
				}

				if (atom_residue_number != 999999){
                                    if (vec_it->residue_number == atom_residue_number && vec_it->atom_name == atom->GetName()){ //If same residue and same atom
                                        OpenValence* new_open_valence = new OpenValence(cocomplex, atom, num_threads, vec_it->derivatization_type, vec_it->mutation_element, vec_it->primary_moiety_name, vec_it->explicit_torsion_str, vec_it->explicit_torsion_str_preset);
					std::cout << "Open valence is found with name " << atom->GetName() << std::endl;
                                        open_valences.push_back(new_open_valence);
                                        break;
                                    }
				}
                            }
			}
		    }  
		}

            }
	}
    }
    return open_valences;
}*/

std::vector<std::string> glob_for_pattern(const fs::path& root, const std::string& ext){
    // return the filenames of all files that have the specified extension
    // in the specified directory and all subdirectories
    std::vector<fs::path> ret;
    std::vector<std::string> all_matched_paths;

    if(!fs::exists(root) || !fs::is_directory(root)) return std::vector<std::string>();

    fs::recursive_directory_iterator it(root);
    fs::recursive_directory_iterator endit;

    while(it != endit)
    {
        if(fs::is_regular_file(*it) && it->path().string().find(ext) != std::string::npos) ret.push_back(it->path().filename());
        ++it;

    }

    for (unsigned int i = 0; i < ret.size(); i++){
        all_matched_paths.push_back(ret[i].string());
    }

    return all_matched_paths;

}
 
/*void ProcessOptions(int argc, char* argv[], int& interval, int& max_num_threads, int& num_threads, std::string& ext, std::string& cocrystal_pdb_path, std::string& moiety_path, std::string& output_pdb_path, std::string& logfile_path, std::vector<open_valence_option>& open_valence_options){

    int option = 0; 
    while ((option = getopt(argc, argv, "c:a:i:m:o:t:e:l:")) != -1){
        switch (option) {
            case 99: { //-c complex pdb path
                cocrystal_pdb_path = std::string(optarg);
                break;
            }
	    case 97: { //-a open valence residue index and atom names, e.g 3-O2-heavy-N-carbonyl
                std::string optarg_str = std::string(optarg);
                std::vector<std::string> dash_split_token = gmml::Split(optarg_str, "-"); //resnum-atomname-hydrogen/heavy-mutate-primarymoiety
		std::vector<std::string> explicit_torsion_tokens;
		if (dash_split_token.size() > 5){
		    for (unsigned int i = 5; i < dash_split_token.size(); i++){
		        explicit_torsion_tokens.push_back(dash_split_token[i]);
		    }
		}
                open_valence_options.emplace_back(open_valence_option(std::stoi(dash_split_token[0]), dash_split_token[1], dash_split_token[2], dash_split_token[3], dash_split_token[4], explicit_torsion_tokens));
                break;
            }
            case 105: { //-i
                interval = std::stoi(std::string(optarg));
                break;
            }
            case 109: { //-m
                moiety_path = std::string(optarg);
                break;
            }
            case 111:{ //-o
                output_pdb_path = std::string(optarg);
                break;
            }
            case 116:{ //-t
                num_threads = std::stoi(std::string(optarg));
                break;
            }
            case 101:{ //-e
                ext = std::string(optarg);
            }
            case 108:{//-l for log file
		logfile_path = std::string(optarg);
	    }
        }
    }
}*/


std::vector<std::pair<MolecularModeling::Atom*, std::string> > GetRequestedOpenValenceAtoms(std::vector<Glycan::Monosaccharide*> monos, std::map<int, std::vector<std::pair<std::string, std::string> > >& open_valence_index_atom_names){
    std::vector<std::pair<MolecularModeling::Atom*, std::string> > open_valence_atom_and_derivatize_type;
    for (std::map<int, std::vector<std::pair<std::string, std::string> > >::iterator mapit = open_valence_index_atom_names.begin(); mapit != open_valence_index_atom_names.end(); mapit++){ //for each open valence atoms
        //int requested_residue_index = mapit->first -1;
        int requested_residue_index = mapit->first;
	std::vector<std::pair<std::string, std::string> >& open_valence_atom_names_derivatize_type = mapit->second;
        MolecularModeling::Residue* requested_ligand_residue = NULL;
	for (unsigned int i = 0; i < monos.size(); i++){
            MolecularModeling::Residue* ligand_residue = monos[i]->cycle_atoms_[0]->GetResidue();
	    if (ligand_residue->GetId().find(std::to_string(requested_residue_index)) != std::string::npos){
	        requested_ligand_residue = ligand_residue;
		break;
	    }
	}
	if (requested_ligand_residue == NULL){
	    std::cout << "Cannot find residue with index " << requested_residue_index << std::endl;
	    std::exit(1);
	}
        AtomVector all_atoms_in_ligand_residue = requested_ligand_residue->GetAtoms(); 

        for (unsigned int i = 0; i < open_valence_atom_names_derivatize_type.size(); i ++){
	    std::pair<std::string, std::string>& atom_name_derivatize_type = open_valence_atom_names_derivatize_type[i];
            MolecularModeling::Atom* open_atom = GetAtomByName(atom_name_derivatize_type.first, all_atoms_in_ligand_residue);
	    open_valence_atom_and_derivatize_type.push_back(std::make_pair(open_atom, atom_name_derivatize_type.second));
            //requested_open_valence_atoms.push_back(open_atom);
        }
    }
    return open_valence_atom_and_derivatize_type;
}

double RMSD(AtomVector& target_atoms, AtomVector& reference_atoms, int coord_index){
    //if (target_atoms.empty()) return 9999.99;

    double total_distance_squared = 0;
    int target_heavy_atom_count = 0;
    //int moved_heavy_atom_count = 0;

    for (unsigned int i = 0; i < target_atoms.size(); i++){
        //if (target_atoms[i]->GetElementSymbol() != "H" && target_atoms[i]->MolecularDynamicAtom::GetAtomType() == "A"){
        if (target_atoms[i]->GetElementSymbol() != "H"){
            target_heavy_atom_count++;
            std::string target_atom_name = target_atoms[i]->GetName();
            bool match_exists = false;
            //std::cout << "Target name: " << target_atom_name << std::endl;

            for (unsigned int j = 0; j < reference_atoms.size(); j++){
                if (reference_atoms[j]->GetElementSymbol() != "H"){
                    //std::cout << "Reference name: " << reference_atoms[j]->GetName() << std::endl;
                    if (reference_atoms[j]->GetName() == target_atom_name){
			double distance = target_atoms[i]->GetCoordinates()[coord_index]->Distance(reference_atoms[j]->GetCoordinate());
                        total_distance_squared += std::pow(distance, 2);
			/*if (distance > 0.02){
			    //std::cout << "Target atom " << target_atom_name << " moves by " << distance << std::endl;
			    moved_heavy_atom_count++;
			}*/
                        match_exists = true;
                        break;
                    }
                }
            }
            if (!match_exists){
                std::cout << "RMSD: no match for atom " << target_atom_name << std::endl;
                std::exit(1);
            }
        }
    }

    total_distance_squared /= target_heavy_atom_count;
    //std::cout << "Total heavy atom count: " << target_heavy_atom_count << std::endl;
    //std::cout << "Moved heavy atom count: " << moved_heavy_atom_count << std::endl;
    //total_distance_squared /= moved_heavy_atom_count;
    //if (target_heavy_atom_count == 0) std::cout << "This model has no aromatic C" << std::endl;
    return std::pow(total_distance_squared, 0.5);
}
