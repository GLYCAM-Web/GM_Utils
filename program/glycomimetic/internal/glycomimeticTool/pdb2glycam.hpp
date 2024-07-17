#include "includes/gmml.hpp"
#include "includes/MolecularModeling/assembly.hpp"
#include "includes/MolecularModeling/atom.hpp"
#include "includes/MolecularModeling/atomnode.hpp"
#include "includes/ParameterSet/PrepFileSpace/prepfile.hpp"
#include "includes/ParameterSet/PrepFileSpace/prepfileresidue.hpp"
#include "includes/ParameterSet/PrepFileSpace/prepfileprocessingexception.hpp"
#include "includes/ParameterSet/OffFileSpace/offfile.hpp"
#include "includes/ParameterSet/OffFileSpace/offfileresidue.hpp"
#include "includes/ParameterSet/OffFileSpace/offfileprocessingexception.hpp"
#include "includes/InputSet/CondensedSequenceSpace/condensedsequence.hpp"
#include "includes/InputSet/Utilities/response.hpp"
#include "includes/Glycan/note.hpp"

#include "vina_atom_data.hpp"
#include "vina_bond_by_distance_for_pdb.hpp"
#include "utility.hpp"

#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <map>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <utility>
#include <iterator>

std::map<std::string, int> max_neighbors_lookup_map = {{"C", 4}, {"N-nonterminal", 3}, {"N-terminal", 4}};

bool is_terminal(MolecularModeling::Atom* atom){
    int num_heavy_atom_neighbors = 0;
    AtomVector bonded_neighbors = atom->GetNode()->GetNodeNeighbors();

    for (unsigned int i = 0; i < bonded_neighbors.size(); i++){
        if (bonded_neighbors[i]->GetElementSymbol() != "H"){
            num_heavy_atom_neighbors++;
        }
    }

    if (num_heavy_atom_neighbors <= 1){
        return true;
    }

    return false;
}

int DetermineMaxNeighborsCount(MolecularModeling::Atom* atom){
    std::string element = atom->GetElementSymbol();
    if (element == "N"){
        if (is_terminal(atom)){
	    element += "-terminal";
	}
    }

    if (max_neighbors_lookup_map.find(element) != max_neighbors_lookup_map.end()){
        return max_neighbors_lookup_map[element];
    }

    return -1;
}

void RemoveExtraHydrogensFromCarbon(MolecularModeling::Assembly& assembly){
    AtomVector assembly_atoms = assembly.GetAllAtomsOfAssembly();

    for (unsigned int i = 0; i < assembly_atoms.size(); i++){
	MolecularModeling::Atom* assembly_atom = assembly_atoms[i];
	int max_neighbor_count = DetermineMaxNeighborsCount(assembly_atom);

	if (max_neighbor_count != -1){
	    AtomVector neighbors = assembly_atom->GetNode()->GetNodeNeighbors();
	    if (neighbors.size() > max_neighbor_count){
		
		int num_h_to_remove = neighbors.size() - max_neighbor_count;
	        AtomVector heavy_atom_neighbors;
	        AtomVector hydrogen_neighbors;

	        for (unsigned int j = 0; j < neighbors.size(); j++){
		    if (neighbors[j]->GetElementSymbol() == "H"){
		        hydrogen_neighbors.push_back(neighbors[j]);
		    }
		    else{
		        heavy_atom_neighbors.push_back(neighbors[j]);
		    }
		} 

		if (hydrogen_neighbors.size() < num_h_to_remove){
		    std::cout << "Too many heavy atoms are bonded to atom " << assembly_atom->GetId() << std::endl;
		    std::exit(1);
		}

		double double_max = std::numeric_limits<double>::max();
                std::map<MolecularModeling::Atom*, double> h_min_distance_map; 
	        for (unsigned int j = 0; j < hydrogen_neighbors.size(); j++){

	            MolecularModeling::Atom* this_h = hydrogen_neighbors[j];
		    h_min_distance_map[this_h] = double_max;
		    for (unsigned int k = 0; k < heavy_atom_neighbors.size(); k++){

			MolecularModeling::Atom* this_heavy = heavy_atom_neighbors[k];
		        double h_heavy_distance = this_h->GetCoordinate()->Distance(this_heavy->GetCoordinate());
			if (h_heavy_distance < h_min_distance_map[this_h]){
			    h_min_distance_map[this_h] = h_heavy_distance;
			}
		    }

		}

		std::map<double, MolecularModeling::Atom*> min_distance_h_map;
	        for (std::map<MolecularModeling::Atom*, double>::iterator mapit = h_min_distance_map.begin(); mapit != h_min_distance_map.end(); mapit++){
		    min_distance_h_map[mapit->second] = mapit->first;
		}	

		int num_h_removed = 0;
		for (std::map<double, MolecularModeling::Atom*>::iterator mapit = min_distance_h_map.begin(); mapit != min_distance_h_map.end(); mapit++){
		    MolecularModeling::Atom* h_to_remove = mapit->second;
		    std::cout << "Removing redundant hydrogen atom " << h_to_remove->GetId();
		    //h_to_remove->GetResidue()->RemoveAtom(h_to_remove, true);

		    AtomVector h_neighbors = h_to_remove->GetNode()->GetNodeNeighbors();
		    for (unsigned int j = 0; j < h_neighbors.size(); j++){
		        h_neighbors[j]->GetResidue()->RemoveAtom(h_to_remove,true);
		    }

		    num_h_removed++;
		    if (num_h_removed >= num_h_to_remove){
		        break;
		    }

		}

	    }

	}
    }
}

bool pdb2glycam_matching(std::string file_path, std::map<MolecularModeling::Atom*, MolecularModeling::Atom*>& actual_template_atom_match, AtomVector& actual_atoms, gmml::InputFileType file_type,
		         std::vector<std::string>& amino_libs, std::string prep)
{
    //pdb2glycam
    std::cout << "Begin pdb2glycam" << std::endl;

    MolecularModeling::Assembly assemblyA(file_path, file_type);
    if (file_type == gmml::InputFileType::PDBQT){
        VinaBondByDistance(assemblyA, vina_atom_data);
    }
    else if (file_type == gmml::InputFileType::PDB){
       VinaBondByDistanceForPDB(assemblyA, 0); 
    }

    AtomVector all_atoms = assemblyA.GetAllAtomsOfAssembly();

    std::map<MolecularModeling::Atom*, AtomVector> input_heavy_atom_protons_map;
    RecordProtonSet(all_atoms, input_heavy_atom_protons_map);

    std::map<MolecularModeling::Atom*, MolecularModeling::Atom*> assemblyA_actual_atom_map;
    for (unsigned int i = 0;i < all_atoms.size(); i++){
	    assemblyA_actual_atom_map[all_atoms[i]] = actual_atoms[i];
    }

    typedef std::vector<Glycan::Oligosaccharide*> OligosaccharideVector;
    typedef MolecularModeling::Assembly::Pdb2glycamMatchingTracker pdb2glycam_matching_tracker;
    typedef MolecularModeling::Assembly::Pdb2glycamMatchingFailInfo pdb2glycam_matching_fail_info;
    //std::string working_Directory = Find_Program_Working_Directory();
    /*std::vector<std::string> amino_libs;
    amino_libs.push_back("../gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/amino12.lib");
    amino_libs.push_back("../gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminoct12.lib");
    amino_libs.push_back("../gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminont12.lib");
    std::string prep = "../gmml/dat/prep/GLYCAM_06j-1.prep";*/

    std::vector<Glycan::Monosaccharide*> monos= std::vector<Glycan::Monosaccharide*>();
    //The sugar identification code in monosaccharide.cc is written for non-hydrogenated structure. Must remove H before using pdb2glycam
    RemoveProtons(all_atoms);
    std::vector<Glycan::Oligosaccharide*> oligos = assemblyA.ExtractSugars(amino_libs,monos,false,false);
    ApplyProtonSet(all_atoms, input_heavy_atom_protons_map);


    //Right now side_atoms only contain the first atom of a side chain. Below I added the codes to attach all atoms to side_atoms.
    for (std::vector<Glycan::Monosaccharide*>::iterator mono_it = monos.begin(); mono_it != monos.end(); mono_it++){
	    (*mono_it)->InitiateDetectionOfCompleteSideGroupAtoms ();
    }


    //Now all side chain atoms are added.Then, make one monosaccharide a new residue, replacing the corresponding one in input pdb file. This is to solve the problem where
    //    one residue contains multiple sugars, for example, a LacNac residue.
    assemblyA.UpdateMonosaccharides2Residues(monos);
    AtomVector assAatoms = assemblyA.GetAllAtomsOfAssembly();

    std::map<Glycan::Oligosaccharide*, std::vector<std::string> > oligo_id_map;
    std::map<Glycan::Oligosaccharide*, std::vector<MolecularModeling::Residue*> > oligo_residue_map;

    for (std::vector<Glycan::Oligosaccharide*>::iterator oligo_it = oligos.begin(); oligo_it != oligos.end(); oligo_it++){
	    std::vector<std::string> empty_vector = std::vector<std::string>();
	    oligo_id_map[*oligo_it] = empty_vector; 
	    std::vector<MolecularModeling::Residue*> empty_residue_vector = std::vector<MolecularModeling::Residue*>();
	    oligo_residue_map[*oligo_it] = empty_residue_vector;
    }
    
    gmml::GlycamResidueNamingMap res_map = assemblyA.ExtractResidueGlycamNamingMap(oligos, oligo_id_map, oligo_residue_map);
    assemblyA.PutAglyconeInNewResidueAndRearrangeGlycanResidues(oligos, oligo_residue_map);

    for (std::map<Glycan::Oligosaccharide*, std::vector<MolecularModeling::Residue*> >::iterator mapit = oligo_residue_map.begin(); mapit != oligo_residue_map.end(); mapit++){
	    std::vector<MolecularModeling::Residue*> res_vec = mapit->second;
	    std::cout << "New oligo: " << std::endl;
	    for (unsigned int t = 0; t < res_vec.size(); t++){
	        std::cout << res_vec[t]->GetName() << std::endl;
	    }
    }

    assemblyA.TestUpdateResidueName2GlycamName(res_map, prep);
    //assemblyA.UpdateResidueName2GlycamName(res_map, prep);

    std::map<Glycan::Oligosaccharide*, pdb2glycam_matching_tracker*> match_tracker;
    assemblyA.MatchPdbAtoms2Glycam(oligo_residue_map, prep, match_tracker);

    bool all_oligos_matched = true;
    for (unsigned int i = 0; i < oligos.size(); i++){
        pdb2glycam_matching_tracker* this_oligo_match_tracker = match_tracker[oligos[i]];
        std::vector<std::map<MolecularModeling::Atom*, MolecularModeling::Atom*>>& all_isomorphisms = this_oligo_match_tracker->all_isomorphisms;

        if (all_isomorphisms.empty()){
            all_oligos_matched = false;
            std::cout << "Oligosaccharide " << i+1 << " matching failed." << std::endl;
            std::cout << "Here are the atoms that might be the issue:" << std::endl;

            int largest_iteration_length = this_oligo_match_tracker->largest_iteration_length;
            std::cout << "Largest iteration length: " << largest_iteration_length << std::endl;

            std::vector<pdb2glycam_matching_fail_info*>& failures = this_oligo_match_tracker->failures;
            for (unsigned int j = 0; j < failures.size(); j++){
                pdb2glycam_matching_fail_info* this_failure = failures[j];
                if (this_failure->iteration_length == largest_iteration_length){
                    std::cout << "Failed atom: " << this_failure->failed_atom->GetResidue()->GetName() << "-" << this_failure->failed_atom->GetName() << std::endl;
                    std::cout << "Failure message: " << this_failure->failure_notice << std::endl << std::endl;
                }
            }
 
        }
        else{
            std::map<MolecularModeling::Atom*, MolecularModeling::Atom*>& first_match = all_isomorphisms[0];

            for (std::map<MolecularModeling::Atom*, MolecularModeling::Atom*>::iterator mapit = first_match.begin(); mapit != first_match.end(); mapit++){
                MolecularModeling::Atom* assemblyA_atom = mapit->first;
                MolecularModeling::Atom* glycam_template_atom = mapit->second;
                //Just do the match for GLYCAM type and charge, don't change the name.
                //assemblyA_atom->SetName(glycam_template_atom->GetName());

                MolecularModeling::Atom* actual_atom = assemblyA_actual_atom_map[assemblyA_atom];
                actual_template_atom_match[actual_atom] = glycam_template_atom;
            }
        }
    }

    std::ofstream pdb2glycam_log("pdb2glycam.log");
    if (!all_oligos_matched){
        std::cout << "Pdb2glycam matching failed." << std::endl;
        pdb2glycam_log << "Pdb2glycam matching failed." << std::endl;
	    return false;
    }

    std::cout << "Pdb2glycam matching successful." << std::endl;
    pdb2glycam_log << "Pdb2glycam matching successful." << std::endl;
    pdb2glycam_log.close();
    return true;
//pdb2glycam

} 
