#ifndef GRIDSEARCH_PTHREAD_HPP
#define GRIDSEARCH_PTHREAD_HPP

#include "includes/gmml.hpp"
#include "includes/MolecularModeling/assembly.hpp"
#include "includes/ParameterSet/PrepFileSpace/prepfile.hpp"
#include "includes/ParameterSet/PrepFileSpace/prepfileresidue.hpp"
#include "includes/ParameterSet/PrepFileSpace/prepfileprocessingexception.hpp"
#include "includes/ParameterSet/OffFileSpace/offfile.hpp"
#include "includes/ParameterSet/OffFileSpace/offfileresidue.hpp"
#include "includes/ParameterSet/OffFileSpace/offfileprocessingexception.hpp"
#include "includes/InputSet/CondensedSequenceSpace/condensedsequence.hpp"
#include "includes/InputSet/PdbFileSpace/pdbfile.hpp"
#include "includes/InputSet/PdbFileSpace/pdbremarksection.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtfile.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtmodel.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtremarkcard.hpp"
#include "includes/utils.hpp"
#include "src/MolecularMetadata/guesses.cc"

#include "vina_atom_data.hpp"
#include "rotamer_library.hpp"
#include "utility.hpp"
#include "open_valence_derivative_moiety.hpp"
#include "monte_carlo.hpp"

#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdlib>
#include <pthread.h>
#include <iterator>
#include <chrono>
#include <sstream>
#include <functional> //std::greater

struct open_valence_option{
    int residue_number = 1;
    std::string atom_name;
    std::string derivatization_type;
    std::string linkage_torsion_rotatable;
    std::vector<std::string> explicit_torsion_str;
    std::vector<std::pair<std::string, std::string> > explicit_torsion_str_preset;
    bool linkage_preset = false;
    std::string linkage_preset_torsion_value_str;
    std::string linkage_torsion_atom1;
    std::string moiety_path;
    std::string moiety_name_pattern;
    
    //open_valence_option(int resnum, std::string atomname, std::string type, std::string if_linkage_rotatable, std::vector<std::string>& explicit_torsion)
    open_valence_option(std::vector<std::string>& dash_split_tokens){

	    for (unsigned int i = 0; i < dash_split_tokens.size(); i++){
	        std::string& this_token = dash_split_tokens[i];
	        std::vector<std::string> underscore_split_tokens = gmml::Split(this_token, "_");	

            //328_C5_N5_C10-moieties/pdbqt/sigma_aldehydes-pdbqt-328_C4_C5_N5_H5N

            //1st token
	        if (i == 0){
		        residue_number = std::stoi(underscore_split_tokens[0]);
		        linkage_torsion_atom1 = underscore_split_tokens[1];
		        atom_name = underscore_split_tokens[2];

	            if (underscore_split_tokens[3].find(":") == std::string::npos){
		            linkage_preset = false;
		            derivatization_type = underscore_split_tokens[3];
	            }
	 	        else{
		            linkage_preset = true;
		            std::vector<std::string> colon_split_tokens = gmml::Split(underscore_split_tokens[3], ":");
		            derivatization_type = colon_split_tokens[0];
		            linkage_preset_torsion_value_str =  colon_split_tokens[1];
		        }
	        }
            //2nd token, moiety path of this open valence position. 
            else if (i == 1){
                moiety_path =  this_token;
            }
            else if (i == 2){
                moiety_name_pattern = this_token;
            }

	        else{
                if (this_token.find(":") == std::string::npos){
                    std::cout << "Add user selected rotatable torsion: " << this_token << std::endl;
                    explicit_torsion_str.push_back(this_token);
                }
                else{
	                std::cout << "Add to preset torsion " << this_token << std::endl;
                    std::vector<std::string> colon_split_tokens = gmml::Split(this_token, ":");
                    explicit_torsion_str_preset.emplace_back(std::make_pair(colon_split_tokens[0], colon_split_tokens[1]));
                }
	        }
	    }

    }
    open_valence_option(){};
};

struct open_valence_gridsearching_results{

    std::multimap<double, std::string> top_affinity_moiety_name_map;
    std::map<std::string, std::vector<double> > moiety_name_top_pose_torsion_values_map;

    open_valence_gridsearching_results(){};
};

namespace PtheadGridSearching{
struct thread_args{
        std::vector<int> this_thread_start_torsion_values;
        std::vector<AtomVector> all_torsions;
        pthread_mutex_t* mutex_ptr = NULL;
	int this_thread_rotamer_count = 0;
	int thread_id = 0;
	int interval = 0;
	AtomVector receptor_atoms;
	AtomVector moiety_atoms;
	AtomVector ligand_atoms;
        double highest_affinity = 999999;
        std::vector<double> hightest_affinity_torsion_values;
	std::vector<double> crystal_torsion_values;
	bool at_least_one_rotamer_accepted = false;
	double chpi_weight = wt_ch_pi;

        thread_args(){
        }
        thread_args(int thread_id_value, std::vector<AtomVector>& all_torsions_vector, pthread_mutex_t* mutex_ptr_value, int rotamer_count_value, int interval_value, AtomVector& receptor_atoms_arg, AtomVector& moiety_atoms_arg, AtomVector& ligand_atoms_arg, std::vector<double>& crystal_torsion_val, double chpi_weight_value){
	    thread_id = thread_id_value;
            //this_thread_start_torsion_values = std::vector<int>(all_torsions_vector.size(), 0);
            all_torsions = all_torsions_vector;
            mutex_ptr = mutex_ptr_value;
	    this_thread_rotamer_count = rotamer_count_value;
	    interval = interval_value;
	    receptor_atoms = receptor_atoms_arg;
	    moiety_atoms = moiety_atoms_arg;
	    ligand_atoms = ligand_atoms_arg;
	    hightest_affinity_torsion_values = std::vector<double>(all_torsions_vector.size(), 999);
	    crystal_torsion_values = crystal_torsion_val;
            chpi_weight = chpi_weight_value;
        }

	thread_args(int thread_id_value, std::vector<AtomVector>& all_torsions_vector, pthread_mutex_t* mutex_ptr_value, int rotamer_count_value, int interval_value, AtomVector& receptor_atoms_arg, AtomVector& moiety_atoms_arg, AtomVector& ligand_atoms_arg){
            thread_id = thread_id_value;
            //this_thread_start_torsion_values = std::vector<int>(all_torsions_vector.size(), 0);
            all_torsions = all_torsions_vector;
            mutex_ptr = mutex_ptr_value;
            this_thread_rotamer_count = rotamer_count_value;
            interval = interval_value;
            receptor_atoms = receptor_atoms_arg;
            moiety_atoms = moiety_atoms_arg;
            ligand_atoms = ligand_atoms_arg;
            hightest_affinity_torsion_values = std::vector<double>(all_torsions_vector.size(), 999);
            //crystal_torsion_values = crystal_torsion_val;
        }

};
}

/*bool InternalClashesExist(AtomVector& atom_set_1, AtomVector& atom_set_2, int coord_index){
    //Exhaustively compare two different atoms in assembly, using two nested for loops
    for (gmml::AtomVector::iterator it = atom_set_1.begin(); it != atom_set_1.end(); it++){
        MolecularModeling::Atom* current_atom = *it;
        if (current_atom->GetElementSymbol() != "H"){
            unsigned int bond_by_distance_count = 0;  //How many bonds does a particular atom have, according to bond by distance
            for (gmml::AtomVector::iterator it1 = atom_set_2.begin(); it1 != atom_set_2.end(); it1++){
                if (*it1 != current_atom){ //If not the same atom in the two atom vectors
                    MolecularModeling::Atom* another_atom = *it1;
                    //First compare X,Y,Z distance of two atoms. If they are really far apart, one dimension comparison is sufficient to exclude. In this way don't have to calculate distance for
                    //each pair
                    if (another_atom->GetElementSymbol() != "H"){
                        if (std::abs(current_atom->GetCoordinates().at(coord_index)->GetX() - another_atom->GetCoordinates().at(coord_index)->GetX()) < 2.0){
                            if (std::abs(current_atom->GetCoordinates().at(coord_index)->GetY() - another_atom->GetCoordinates().at(coord_index)->GetY()) < 2.0){
                                if (std::abs(current_atom->GetCoordinates().at(coord_index)->GetZ() - another_atom->GetCoordinates().at(coord_index)->GetZ()) < 2.0){
                                    //If distance as each dimension is within cutoff, then calculate 3D distance
                                    if (current_atom->GetCoordinates().at(coord_index)->Distance(*(another_atom->GetCoordinates().at(coord_index)) ) < 2.0){
                                        bond_by_distance_count++;
                                    }
                                }
                            }
                        }
                    }
                }
            }

            AtomVector neighbors = current_atom->GetNodes().at(coord_index)->GetNodeNeighbors();
            int non_h_neighbors_count = 0;
            for (unsigned int i = 0; i < neighbors.size(); i++){
                if (neighbors[i]->GetElementSymbol() != "H"){
                    non_h_neighbors_count++;
                }
            }
            //If bond by distance gives more bonds than the number of bonds in atom node, then this atom is clashing with other atoms. This residue is a clashing residue
            if (bond_by_distance_count > non_h_neighbors_count){
		//std::cout << "Bond by dist count: " << bond_by_distance_count << " non H neighbors count: " << non_h_neighbors_count << std::endl;
                //std::cout << "Atom with clash: " << current_atom->GetResidue()->GetName() << "-" << current_atom->GetName() << " has clash " << std::endl;
                return true;
            }
        }
    }

    return false;
}*/

bool GridSearchingByMultipleThreads(int coord_index, std::vector<AtomVector>& all_torsions, std::vector<int>& thread_start_torsion_values, int interval, int num_rotamers_to_sample, double* highest_affinity_ptr, pthread_mutex_t* mutex_ptr, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, std::vector<double>* highest_affinity_torsions_ptr){

    int start_value = 0;
    int end_value = 359;

    int rotation_values[all_torsions.size()];
    for (unsigned int a = 0; a < thread_start_torsion_values.size(); a++){
        rotation_values[a] = thread_start_torsion_values[a];
    }

    for (std::vector<AtomVector>::iterator it = all_torsions.begin(); it != all_torsions.end(); it++){
        int index = std::distance(all_torsions.begin(), it);
        SetDihedral((*it)[0], (*it)[1], (*it)[2], (*it)[3], rotation_values[index], coord_index);
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

    //Part the moiety atoms into those rotate and those that don't. Score the unrotated only once, and only repetitively score the rotated ones
    AtomVector rotated_atoms_and_dummy_atoms;
    rotated_atoms_and_dummy_atoms.push_back(all_torsions.back()[1]); //2nd atom of the last torsion
    all_torsions.back()[2]->FindConnectedAtoms(rotated_atoms_and_dummy_atoms, coord_index);
    //Remove the 2nd atom from the rotated vector.For example, benzene_C1-benzene_C2-O3-C4. If benzene_C2 is excluded from unrotated atoms, unrotated atoms no longer contains the whole benzene ring.
    //This will break DetectAromaticCarbons and will affect pi-pi/ch-pi/catpi results.
    rotated_atoms_and_dummy_atoms.erase(rotated_atoms_and_dummy_atoms.begin());

    //Find Connected atoms may contain moiety dummy atoms. These aren't in the moiety atoms vector. So filter these out.
    AtomVector rotated_atoms;
    for (unsigned int i = 0; i < rotated_atoms_and_dummy_atoms.size(); i++){
        if (std::find(moiety_atoms.begin(), moiety_atoms.end(), rotated_atoms_and_dummy_atoms[i]) != moiety_atoms.end()){
            rotated_atoms.push_back(rotated_atoms_and_dummy_atoms[i]);
        }
    }

    AtomVector rotated_atoms_no_h;
    for (unsigned int i = 0; i < rotated_atoms.size(); i++){
        if (rotated_atoms[i]->GetElementSymbol() != "H"){
            rotated_atoms_no_h.push_back(rotated_atoms[i]);
        }
    }

    AtomVector unrotated_atoms;
    for (unsigned int j = 0; j < moiety_atoms.size(); j++){
        if (std::find(rotated_atoms.begin(), rotated_atoms.end(), moiety_atoms[j]) == rotated_atoms.end()){
            unrotated_atoms.push_back(moiety_atoms[j]);
        }
    }

    bool at_least_one_rotamer_accepted = false;

    VinaScorePrerequisites prerequisites_for_unrotated_atoms(unrotated_atoms, receptor_atoms);
    VinaScorePrerequisites prerequisites_for_rotated_atoms(rotated_atoms, receptor_atoms);

     for (unsigned int rotamer_sampled = 0; rotamer_sampled < num_rotamers_to_sample;){

        double unrotated_atom_affinity = VinaScoreInPlace(prerequisites_for_unrotated_atoms, coord_index)[0];

        unsigned int i = (rotamer_sampled == 0) ? rotation_values[all_torsions.size() -1] : start_value;
        for (; i <= end_value; i += interval){

            rotation_values[all_torsions.size() -1] = i;
            SetDihedral(all_torsions.back()[0], all_torsions.back()[1], all_torsions.back()[2], all_torsions.back()[3], i, coord_index);

            if (!InternalClashesExist(moiety_atoms_no_h, ligand_plus_moiety_atoms_no_h, coord_index)){
                double rotated_atom_affinity = VinaScoreInPlace(prerequisites_for_rotated_atoms, coord_index)[0];
                double moiety_affinity = unrotated_atom_affinity + rotated_atom_affinity;

                if (moiety_affinity < *(highest_affinity_ptr)){
                    *(highest_affinity_ptr) = moiety_affinity;
                    for (int k = 0; k < all_torsions.size(); k++){
                        (*highest_affinity_torsions_ptr)[k] = rotation_values[k];
                    }
                }

                at_least_one_rotamer_accepted = true;

                //ligand_atoms[0]->GetResidue()->GetAssembly()->BuildPdbFileStructureFromAssembly()->Write(temp.str());
                //pthread_mutex_lock(mutex_ptr);
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
                std::cout << std::endl << std::endl;
                pthread_mutex_unlock(mutex_ptr);*/
                //rotamer_sampled++;
            }

            //std::cout << "Thread " << coord_index << " num rot sampled " << rotamer_sampled << std::endl;
            rotamer_sampled++;
        }

	for (int j = all_torsions.size()-1; j>=0; j--){
            if (rotation_values[j] + interval <= end_value){
                rotation_values[j]+= interval;
                SetDihedral(all_torsions[j][0], all_torsions[j][1], all_torsions[j][2], all_torsions[j][3], rotation_values[j], coord_index);

                for (unsigned int k = j+1; k < all_torsions.size(); k++){
                    rotation_values[k] = start_value;
                    SetDihedral(all_torsions[k][0], all_torsions[k][1], all_torsions[k][2], all_torsions[k][3], rotation_values[k], coord_index);
                }
                break;
            }
        }
    }

    return at_least_one_rotamer_accepted;

}



void* GridSearchingByMultipleThreadsStartRoutine (void* arg_ptr){
    PtheadGridSearching::thread_args* argstruct = (PtheadGridSearching::thread_args* ) arg_ptr;
    std::vector<AtomVector> in_thread_torsions = argstruct->all_torsions;

    argstruct->at_least_one_rotamer_accepted = GridSearchingByMultipleThreads(argstruct->thread_id, argstruct->all_torsions, argstruct->this_thread_start_torsion_values, argstruct->interval, argstruct->this_thread_rotamer_count, &(argstruct->highest_affinity), argstruct->mutex_ptr, argstruct->receptor_atoms, argstruct->ligand_atoms, argstruct->moiety_atoms, &(argstruct->hightest_affinity_torsion_values));
    return NULL;
}

std::pair<double, std::vector<double> > GridSearching(CoComplex* cocomplex, OpenValence* open_valence, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, 
		                                      std::vector<AtomVector>& all_torsions, int interval, int num_threads){


    std::cout << "Start gridsearching" << std::endl;
    double floatpart,angles_per_torsion;
    floatpart = std::modf(360/interval, &angles_per_torsion);

    int rotamer_count = std::pow(angles_per_torsion, all_torsions.size());
    std::cout << "Rotamer count is: " << rotamer_count << std::endl;
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
        argstruct[i] = PtheadGridSearching::thread_args(i, all_torsions, &lock, thread_rotamers_count, interval, receptor_atoms, moiety_atoms, ligand_atoms);
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

    //Before each grid searching, reset the coordinates of the ligand and R group atoms to their initial state. Natural ligand go back to crystal structure, R group go back to when they just get grafted. 
    //This is necessary because grid searching is multi threaded at the rotamer level. Since each thread ends with different coordinates, the zero-degree position of each torsion may be inconsistent.
    //So a reset is necessary before a new gridsearching starts. 
    //cocomplex->RestoreLigandPositions();
    //open_valence->RestoreMoietyAtomPositions();

    for (unsigned int i = 0; i < num_threads; i++){
        //Create a child thread
        int success_status = pthread_create(&tid[i], NULL, &GridSearchingByMultipleThreadsStartRoutine, &argstruct[i]);
	if (success_status != 0){
	    std::cout << "Pthread create failed on thread " << i << " error code: " << success_status << " Aborting." << std::endl;
	    std::exit(1);
	}
    }

    for (unsigned int i = 0; i < num_threads; i++){
        pthread_join(tid[i], NULL);
    }
    pthread_mutex_destroy(&lock);

    bool at_least_one_rotamer_accepted = false;
    std::map<double, std::vector<double> > thread_highest_affinity_torsion_value_map;
    for (unsigned int i = 0; i < num_threads; i++){
        thread_highest_affinity_torsion_value_map[argstruct[i].highest_affinity] = argstruct[i].hightest_affinity_torsion_values;
        if (argstruct[i].at_least_one_rotamer_accepted){
            at_least_one_rotamer_accepted = true;
        }
    }

    if (!at_least_one_rotamer_accepted){
        std::cout << "Warning, no unclashing rotamer found for this moiety" << std::endl;
    }

    //Return the highest affinity and the associated torsion values.
    return std::pair<double, std::vector<double> >(thread_highest_affinity_torsion_value_map.begin()->first, thread_highest_affinity_torsion_value_map.begin()->second);
}

void AttemptClashResolutionUsingRotamerLibrary(CoComplex* cocomplex, OpenValence* open_valence, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, 
		                               std::vector<AtomVector>& free_tors, int interval_actual, int num_threads, double& highest_affinity, std::string& this_moiety_filename, 
					       std::vector<open_valence_gridsearching_results>& open_valence_gridsearch_info, std::ofstream& gridsearch_log){
    std::cout << "Attempt clash resolution using rotamer library." << std::endl;
    gridsearch_log << "Attempt clash resolution using rotamer library." << std::endl;

    std::map<double, MolecularModeling::Residue*, std::greater<double> > score_clashing_residue_map = SortClashingResiduesInDescendingOrder(moiety_atoms, receptor_atoms);
    for (std::map<double, MolecularModeling::Residue*>::iterator mapit = score_clashing_residue_map.begin(); mapit != score_clashing_residue_map.end(); mapit++){
        std::cout << "Clashing residue " << mapit->second->GetId() << " and score " << mapit->first << std::endl;
    }

    ResolveClashesUsingRotamerLibrary(score_clashing_residue_map, moiety_atoms, receptor_atoms);

    if (!free_tors.empty()){
        //std::pair<double, std::vector<double> > highest_affinity_torsion_value_pair2 = GridSearching(cocomplex, open_valence, receptor_atoms, ligand_atoms, moiety_atoms, free_tors, interval_actual, num_threads);
        std::pair<double, std::vector<double> > highest_affinity_torsion_value_pair2 = MonteCarlo(cocomplex, open_valence, receptor_atoms, ligand_atoms, moiety_atoms, free_tors, interval_actual, num_threads);
        highest_affinity = highest_affinity_torsion_value_pair2.first;
        std::vector<double>& highest_affinity_torsion_values2 = highest_affinity_torsion_value_pair2.second;

        open_valence_gridsearch_info.back().top_affinity_moiety_name_map.clear();
        open_valence_gridsearch_info.back().moiety_name_top_pose_torsion_values_map.clear();

        open_valence_gridsearch_info.back().top_affinity_moiety_name_map.insert(std::make_pair(highest_affinity, this_moiety_filename));
        open_valence_gridsearch_info.back().moiety_name_top_pose_torsion_values_map[this_moiety_filename] = highest_affinity_torsion_values2;

        std::cout << "After rotamer library affinity: " << highest_affinity << std::endl;
        gridsearch_log << "After rotamer library affinity: " << highest_affinity << std::endl;

        for (unsigned int x = 0; x < free_tors.size(); x++){
            SetDihedral(free_tors[x][0], free_tors[x][1], free_tors[x][2], free_tors[x][3], highest_affinity_torsion_values2[x], 0);
        }
    }

    VinaScorePrerequisites prerequisites(moiety_atoms, receptor_atoms);
    double post_gridsearch_affinity = VinaScoreInPlace(prerequisites, 0)[0];
    std::cout << "After rotamer library protocal computing affinity again: " << post_gridsearch_affinity << std::endl;
}

double determine_minimum_interval(int num_torsions){
 //Limit #rotamers per moiety to 250k. If greater, adjust interval to reduce calculation burden.
    int max_rotamers = 250000;
    int max_rot_per_torsion = std::pow(max_rotamers, (double) 1/num_torsions);
    std::cout << "Max rot per torsion " << max_rot_per_torsion << std::endl;
    int min_interval = 360/max_rot_per_torsion;

    if (min_interval < 1){
        min_interval = 1;
    }
    std::cout << "Min interval: " << min_interval << std::endl;
    return min_interval;
}

void GridsearchingForIndividualOpenValenceAtomAndMoiety(CoComplex* cocomplex, OpenValence* open_valence, int open_valence_index, std::string& moiety_path, std::string& this_moiety_filename,  
		                                        int interval, int num_threads,  std::string& output_pdb_path, std::ofstream& gridsearch_log, std::ofstream& entropy_penalty, 
							double& total_entropic_penalty, std::vector<open_valence_gridsearching_results>& open_valence_gridsearch_info){
    gridsearch_log << "Start moiety\n";
    DerivativeMoiety* derivative_moiety = new DerivativeMoiety(moiety_path, this_moiety_filename, num_threads);
    std::string moiety_name = derivative_moiety->GetMoietyName();
    std::cout << "Moiety name is: " << moiety_name << std::endl;
    gridsearch_log << "Moiety name is: " << moiety_name << std::endl;
    std::string open_atom_name = open_valence->GetOpenValenceAtom()->GetName();
    open_valence->Derivatize(derivative_moiety);

    AtomVector moiety_atoms = open_valence->GetAllMoietyAtoms();
    AtomVector receptor_atoms = cocomplex->GetReceptorAtoms();
    AtomVector ligand_atoms = cocomplex->GetLigandAtoms();

    std::vector<AtomVector> free_tors = open_valence->GetRotatableBonds();

    double interval_actual = interval;
    double min_interval = determine_minimum_interval(free_tors.size());
    if (interval_actual < min_interval){
        interval_actual = min_interval;
    }
    std::cout << "Actual interval this moiety: " << interval_actual << std::endl;

    for (unsigned int a = 0; a < free_tors.size(); a++){
        //std::cout << "Free tors " << free_tors[a][0]->GetName() << "-" << free_tors[a][1]->GetName() << "-" << free_tors[a][2]->GetName() << "-" << free_tors[a][3]->GetName() << std::endl;
        std::cout << "Free tors " << free_tors[a][0]->GetResidue()->GetName() << ":" << free_tors[a][0]->GetName() << "-" << free_tors[a][1]->GetResidue()->GetName() << ":" << free_tors[a][1]->GetName() << "-"<< free_tors[a][2]->GetResidue()->GetName() << ":" << free_tors[a][2]->GetName() << "-" << free_tors[a][3]->GetResidue()->GetName() << ":" << free_tors[a][3]->GetName() << std::endl;
    }

    //Unless there is at least one free torsion, or you shouldn't do grid searching. Will segfault
    if (!free_tors.empty()){
        entropy_penalty << moiety_name << "\t" << open_valence->GetEntropicPenalty() << std::endl;
        total_entropic_penalty += open_valence->GetEntropicPenalty();

        std::cout << "Ligand atoms size: " << ligand_atoms.size() << std::endl;

        //Before each grid searching call, restore natural ligand atoms to initial position.
        std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
        //std::pair<double, std::vector<double> > highest_affinity_torsion_value_pair = GridSearching(cocomplex, open_valence, receptor_atoms, ligand_atoms, moiety_atoms, free_tors, interval_actual, num_threads);
        std::pair<double, std::vector<double> > highest_affinity_torsion_value_pair = MonteCarlo(cocomplex, open_valence, receptor_atoms, ligand_atoms, moiety_atoms, free_tors, interval_actual, num_threads);

        std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();

        double highest_affinity = highest_affinity_torsion_value_pair.first;
        std::vector<double>& highest_affinity_torsion_values = highest_affinity_torsion_value_pair.second;

        open_valence_gridsearch_info.back().top_affinity_moiety_name_map.insert(std::make_pair(highest_affinity, this_moiety_filename));
        open_valence_gridsearch_info.back().moiety_name_top_pose_torsion_values_map[this_moiety_filename] = highest_affinity_torsion_values;

        std::cout << "Grid searching time elapsed = " << std::chrono::duration_cast<std::chrono::milliseconds>(end - begin).count() << "[ms]" << std::endl;
        std::cout << "After grid searching, highest affinity is: " << highest_affinity << std::endl;
        gridsearch_log << "After grid searching, highest affinity is: " << highest_affinity << std::endl;

        for (unsigned int x = 0; x < free_tors.size(); x++){
            std::cout << "After GS highest torisons " << highest_affinity_torsion_values[x] << std::endl;
            SetDihedral(free_tors[x][0], free_tors[x][1], free_tors[x][2], free_tors[x][3], highest_affinity_torsion_values[x], 0);
            std::cout << "But actually this torsions is: " << GetDihedral(free_tors[x][0], free_tors[x][1], free_tors[x][2], free_tors[x][3], 0) << std::endl;
        }

    }//If at least one torsion

    else{
        std::cout << "No free torsions at this position." << std::endl;
    }

    VinaScorePrerequisites prerequisites(moiety_atoms, receptor_atoms);
    double post_gridsearch_affinity = VinaScoreInPlace(prerequisites, 0)[0];

    std::cout << "After gridsearching affinity: " << post_gridsearch_affinity << std::endl;
    gridsearch_log << "After gridsearching affinity: " << post_gridsearch_affinity << std::endl;

    if (post_gridsearch_affinity > 0){
	    AttemptClashResolutionUsingRotamerLibrary(cocomplex, open_valence, receptor_atoms, ligand_atoms, moiety_atoms, free_tors, interval_actual, num_threads, post_gridsearch_affinity, 
			                          this_moiety_filename, open_valence_gridsearch_info, gridsearch_log);
    }

    std::stringstream output_pdb_name;
    output_pdb_name << output_pdb_path << "/complex" << open_valence_index << "-" << open_atom_name << "-" << moiety_name;

    if (post_gridsearch_affinity > 0){
        output_pdb_name << "-clash";
    }

    output_pdb_name << ".pdb";

    PdbFileSpace::PdbFile* best_pdb = cocomplex->GetCoComplexAssembly()->BuildPdbFileStructureFromAssembly();
    best_pdb->Write(output_pdb_name.str());
    std::cout << "Wrote pdb file " << output_pdb_name.str() << std::endl;
    gridsearch_log << "Wrote pdb file " << output_pdb_name.str() << std::endl;

    cocomplex->WriteDerivatizedLigandOffFile();
    cocomplex->WriteDerivatizedLigandAndReceptorPdbFile(output_pdb_path);

    open_valence->RemoveDerivativeMoiety();

    std::cout << "End moiety" << std::endl << std::endl;
    gridsearch_log << "End moiety" << std::endl << std::endl;
}

void ProcessOpenValenceGridSearchInfo(CoComplex* cocomplex, std::vector<OpenValence*>& open_valences, int interval, int num_threads, std::string& output_pdb_path, 
		                      std::ofstream& gridsearch_log, std::vector<open_valence_gridsearching_results>& open_valence_gridsearch_info){

    //Reproduce top affinity pose of each moiety. 
    std::cout << "Write the final pdb with the best moiety at each open valence position" << std::endl;
    AtomVector all_moiety_atoms;
    std::vector<AtomVector> all_torsions;
    for (unsigned int i = 0; i < open_valences.size(); i++){
	OpenValence* open_valence = open_valences[i];

        double top_affinity = open_valence_gridsearch_info[i].top_affinity_moiety_name_map.begin()->first;
	std::string& top_moiety_filename = open_valence_gridsearch_info[i].top_affinity_moiety_name_map.begin()->second;
	std::vector<double>& top_moiety_torsion_values = open_valence_gridsearch_info[i].moiety_name_top_pose_torsion_values_map[top_moiety_filename];

        std::string moiety_path2 = open_valence->GetMoietyPath();
        std::string moiety_name_pattern = open_valence->GetMoietyNamePattern();
	DerivativeMoiety* moiety = new DerivativeMoiety(moiety_path2, top_moiety_filename, num_threads);
	open_valences[i]->Derivatize(moiety);
        AtomVector real_moiety_atoms = moiety->GetRealAtoms();
        all_moiety_atoms.insert(all_moiety_atoms.end(), real_moiety_atoms.begin(), real_moiety_atoms.end());
	
	std::vector<std::pair<AtomVector, double> > preset_torsions = open_valence->GetPresetTorsions();
        for (unsigned int a = 0; a < preset_torsions.size(); a++){
            AtomVector& this_tor = preset_torsions[a].first;
            double& this_prset_value = preset_torsions[a].second;

            for (unsigned int b = 0; b < num_threads; b++){
                SetDihedral(this_tor[0], this_tor[1], this_tor[2], this_tor[3], this_prset_value, b);
            }
        }


	std::vector<AtomVector> free_tors = open_valence->GetRotatableBonds();
        all_torsions.insert(all_torsions.end(), free_tors.begin(), free_tors.end());

	for (unsigned int x = 0; x < free_tors.size(); x++){
            //std::cout << "Top moiety highest torisons " << top_moiety_torsion_values[x] << std::endl;
	    for (unsigned int t = 0; t < num_threads; t++){
                SetDihedral(free_tors[x][0], free_tors[x][1], free_tors[x][2], free_tors[x][3], top_moiety_torsion_values[x], t);
                //std::cout << "But actually this torsions is: " << GetDihedral(free_tors[x][0], free_tors[x][1], free_tors[x][2], free_tors[x][3], t) << std::endl;
	    }
        }   
    }

    AtomVector ligand_atoms = cocomplex->GetLigandAtoms();
    AtomVector ligand_plus_moiety_atoms = ligand_atoms;
    ligand_plus_moiety_atoms.insert(ligand_plus_moiety_atoms.end(), all_moiety_atoms.begin(), all_moiety_atoms.end());
    AtomVector receptor_atoms = cocomplex->GetReceptorAtoms();

    for (unsigned int z= 0; z < all_torsions.size(); z++){
        std::cout << "This bond: " << all_torsions[z][0]->GetName() << "-" << all_torsions[z][1]->GetName() << "-" << all_torsions[z][2]->GetName() << "-" << all_torsions[z][3]->GetName() << std::endl;
    }

    if (InternalClashesExist(all_moiety_atoms, ligand_plus_moiety_atoms, 0)){
        std::cout << "If each moiety applies its best pose, they clash with each other. Attempt to resolve them." << std::endl;
        std::pair<double, std::vector<double> > highest_affinity_torsion_values = MonteCarlo(cocomplex, open_valences[0], receptor_atoms, ligand_atoms, all_moiety_atoms, all_torsions, interval, num_threads);
        std::vector<double>& best_torsion_values = highest_affinity_torsion_values.second;
        //FIXME: Openvalence parameter isn't really used at all. For now, just give any open valence. Remove this arg later on. 

        std::cout << "All moiety affinity after final clash resolution " << highest_affinity_torsion_values.first << std::endl;
        for (unsigned int x = 0; x < all_torsions.size(); x++){
            SetDihedral(all_torsions[x][0], all_torsions[x][1], all_torsions[x][2], all_torsions[x][3], best_torsion_values[x], 0);
        }
    }

    std::string output_path_and_filename = output_pdb_path + "/complex_best_each_position.pdb";
    cocomplex->GetCoComplexAssembly()->BuildPdbFileStructureFromAssembly()->Write(output_path_and_filename);

    //Remove last "_"
    cocomplex->WriteDerivatizedLigandAndReceptorPdbFile(output_pdb_path);


    //TODO:check if moieties clash with each other. If so, how to resolve the clashes.

}

void GridSearchingForOpenValenceAtoms(CoComplex* cocomplex, std::vector<OpenValence*>& open_valences, int interval, int num_threads, std::string output_pdb_path, std::string& logfile_path, std::string& requested_combinations){

    std::ofstream gridsearch_log(logfile_path);
    std::ofstream entropy_penalty("entropic_penalties.txt");

    //std::stringstream output_pdb_name;
    //output_pdb_name << output_pdb_path << "/" << "best-";

    std::vector<open_valence_gridsearching_results> open_valence_gridsearch_info;

    for (unsigned int i = 0; i < open_valences.size(); i++){
        std::cout << "One open valence" << std::endl;
        OpenValence* open_valence = open_valences[i];
        open_valence_gridsearch_info.emplace_back(open_valence_gridsearching_results());
        std::string open_atom_name = open_valence->GetOpenValenceAtom()->GetName();
        double total_entropic_penalty = 0;
        std::string moiety_path = open_valence->GetMoietyPath();
        std::string moiety_name_pattern = open_valence->GetMoietyNamePattern();
        std::cout << "Moiety name pattern: " << moiety_name_pattern << std::endl;

        std::vector<std::string> all_moiety_filenames = glob(moiety_path, moiety_name_pattern);

	for (unsigned int j = 0; j < all_moiety_filenames.size(); j++){
            std::string& this_moiety_filename = all_moiety_filenames[j];
	    GridsearchingForIndividualOpenValenceAtomAndMoiety(cocomplex, open_valence, i, moiety_path, this_moiety_filename, interval, num_threads, output_pdb_path, gridsearch_log, entropy_penalty,
			                                                       total_entropic_penalty, open_valence_gridsearch_info);
	}

    }

    ProcessOpenValenceGridSearchInfo(cocomplex, open_valences, interval, num_threads, output_pdb_path, gridsearch_log, open_valence_gridsearch_info);

}

#endif //GRIDSEARCH_PTHREAD_HPP
