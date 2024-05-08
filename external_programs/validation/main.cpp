
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

#include "../src/vina_bond_by_distance_for_pdb.hpp"
#include "../src/pdb2glycam.hpp"

//#include "boost/tokenizer.hpp"
#include <vector>
#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdlib>
#include <pthread.h>
#include <iterator>
#include <sstream>
//#include <boost/filesystem.hpp>
#include <functional> //std::greater

struct available_atom{
    available_atom(std::string residue_index_str, std::string atom_name, std::string atom_to_replace){
        this->residue_index_str_ = residue_index_str;
	this->atom_name_ = atom_name;
	this->atom_to_replace_ = atom_to_replace;
    }
    std::string residue_index_str_, atom_name_, atom_to_replace_;
};

struct response{
    response(bool valid, bool pdb2glycam_available, std::vector<available_atom> available_atoms, std::vector<std::string> comments){
        this->is_valid_ = valid;
	this->pdb2glycam_available_ = pdb2glycam_available;
	this->available_atoms_ = available_atoms; 
	this->comments_ = comments;
    }
    bool is_valid_ = false;
    bool pdb2glycam_available_ = false;
    std::vector<available_atom> available_atoms_;
    std::vector<std::string> comments_;
};

typedef std::vector<MolecularModeling::Atom*> AtomVector;
int main(int argc, char* argv[]){
    std::string file_path_str = std::string(argv[1]);
    MolecularModeling::Assembly assemblyA(file_path_str, gmml::InputFileType::PDB); 
    VinaBondByDistanceForPDB(assemblyA, 0);

    std::vector<std::string> amino_libs;
    amino_libs.push_back("../../gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/amino12.lib");
    amino_libs.push_back("../../gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminoct12.lib");
    amino_libs.push_back("../../gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminont12.lib");
    std::string prep = "../../gmml/dat/prep/GLYCAM_06j-1.prep";

    //Valid = have sugars and available open valence positions.
    bool is_valid = false, pdb2glycam_available = false;
    std::vector<std::string> comments;

    std::vector<Glycan::Monosaccharide*> monos= std::vector<Glycan::Monosaccharide*>();
    std::vector<Glycan::Oligosaccharide*> oligos = assemblyA.ExtractSugars(amino_libs,monos,false,false);

    if (oligos.empty()){
	is_valid = false;
        comments.push_back("Not elegible for pdb2glycam because no sugars were detected");
    }

    //Attempt pdb2glycam matching
    std::map<MolecularModeling::Atom*, MolecularModeling::Atom*> actual_template_atom_match;
    AtomVector atoms = assemblyA.GetAllAtomsOfAssembly();
    bool pdb2glycam_successful = pdb2glycam_matching(file_path_str, actual_template_atom_match, atoms, gmml::InputFileType::PDB, amino_libs, prep);

    if (!pdb2glycam_successful){
        comments.push_back("Pdb2glycam matching failed. Cannot use this feature");
	pdb2glycam_available = false;
    }
    else{
        pdb2glycam_available = true;
    }

    //Detect available atoms for derivatization
    AtomVector side_atoms;
    std::vector<available_atom> available_atoms;  

    for (unsigned int i = 0; i < monos.size(); i++){
        Glycan::Monosaccharide* mono = monos[i];
	AtomVector cycle_atoms = mono->cycle_atoms_;
	MolecularModeling::Residue* this_residue = cycle_atoms[0]->GetResidue();

	std::string residue_id = this_residue->GetId();
        std::vector<std::string> underscore_split_token = gmml::Split(residue_id, "_");
        std::string residue_index = underscore_split_token[2];
	AtomVector this_residue_atoms = this_residue->GetAtoms();

	for (unsigned int j = 0; j < cycle_atoms.size(); j++){
	    MolecularModeling::Atom* cycle_atom = cycle_atoms[j];
	    AtomVector cycle_neighbors = cycle_atom->GetNode()->GetNodeNeighbors();

	    for (unsigned int k = 0; k < cycle_neighbors.size(); k++){
	        MolecularModeling::Atom* neighbor = cycle_neighbors[k];
		AtomVector neighbor_neighbors = neighbor->GetNode()->GetNodeNeighbors();

		if ( (std::find(cycle_atoms.begin(), cycle_atoms.end(), neighbor) == cycle_atoms.end()) && neighbor->GetElementSymbol() != "H" && 
		      std::find(this_residue_atoms.begin(), this_residue_atoms.end(), neighbor) != this_residue_atoms.end()){

		    if (neighbor->GetElementSymbol() == "C"){
			for (unsigned int l = 0; l < neighbor_neighbors.size(); l++){
			    MolecularModeling::Atom* nn = neighbor_neighbors[l];

			    if (nn->GetElementSymbol() == "O"){
				if (std::find(side_atoms.begin(), side_atoms.end(), nn) == side_atoms.end()){
			            side_atoms.push_back(nn);
                                    AtomVector nnns = nn->GetNode()->GetNodeNeighbors();

				    for(unsigned int m = 0; m < nnns.size(); m++){ 
                                        MolecularModeling::Atom* nnn = nnns[m];
					//if (nnn->GetElementSymbol() == "H")
					if (nnn != neighbor && std::find(this_residue_atoms.begin(), this_residue_atoms.end(), nnn) != this_residue_atoms.end()){
				            available_atoms.emplace_back(available_atom(residue_index, nn->GetName(), nnn->GetName()));
					}
				    }
				}
			    }
			}
		    }
		    else{
			if (std::find(side_atoms.begin(), side_atoms.end(), neighbor) == side_atoms.end()){
                            side_atoms.push_back(neighbor);
                            
			    for(unsigned int l = 0; l < neighbor_neighbors.size(); l++){
                                MolecularModeling::Atom* nn = neighbor_neighbors[l];

				//if (nn->GetElementSymbol() == "H")
				if (!nn->GetIsCycle() && std::find(this_residue_atoms.begin(), this_residue_atoms.end(), nn) != this_residue_atoms.end()){
			            available_atoms.emplace_back(available_atom(residue_index, neighbor->GetName(), nn->GetName()));
				}
			    }
			}
		    }
		}
	    }
	}
    }
	
    for (unsigned int i = 0; i < available_atoms.size(); i++){
        available_atom& atom = available_atoms[i];
	//std::string residue_index_str_, atom_name_, atom_to_replace_;
	std::cout << "Open for derivatization: " << atom.residue_index_str_ << "-" << atom.atom_name_ << "-" << atom.atom_to_replace_ << std::endl;
    }

    if (available_atoms.empty()){
        comments.push_back("No available positions for modification detected. For now must be ring hydroxyl/amino groups");
	is_valid = false;
    }
    else{
        is_valid = true;
    }
 
    response this_response(is_valid, pdb2glycam_available, available_atoms, comments);
}
