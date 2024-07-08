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
#include <functional> //std::greater
//#include <boost/filesystem.hpp>
//#include "boost/tokenizer.hpp"

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

#include "../glycomimetic_program/vina_bond_by_distance_for_pdb.hpp"
#include "../glycomimetic_program/pdb2glycam.hpp"


struct available_atom{
    available_atom(std::string residue_index_str, std::string resname, std::string chain_id, std::string atom_name, std::string atom_to_replace){
    	this->residue_index_str_ = residue_index_str;
		this->resname_ = resname;
		this->chain_id_ = chain_id;
		this->atom_name_ = atom_name;
		this->atom_to_replace_ = atom_to_replace;
    }
	void print_attribute(std::ofstream& output){
		//std::cout << "Available open valence atom: " << std::endl;
		//std::cout << "Residue index: " << this->residue_index_str_ << std::endl;
		//std::cout << "Atom to modify: " << this->atom_name_ << std::endl;
		//std::cout << "Downstream atom to replace: " << this->atom_to_replace_ << std::endl;
		//std::cout << "New option: " << this->residue_index_str_ << "-" << this->atom_name_ << "-" << this->atom_to_replace_ << std::endl;
		output << this->residue_index_str_ << "-" << this->resname_ << "-" << this->chain_id_ << "-" << this->atom_name_ << "-" << this->atom_to_replace_ << std::endl;
	}
    std::string residue_index_str_, resname_, chain_id_, atom_name_, atom_to_replace_;
};


std::vector<available_atom> detect_available_atoms(std::vector<Glycan::Monosaccharide*> monos){
    std::vector<available_atom> available_atoms = std::vector<available_atom>();

    for (unsigned int i = 0; i < monos.size(); i++){
        Glycan::Monosaccharide* mono = monos[i];
		AtomVector cycle_atoms = mono->cycle_atoms_;
		MolecularModeling::Residue* this_residue = cycle_atoms[0]->GetResidue();

		std::string residue_id = this_residue->GetId();
        std::vector<std::string> underscore_split_token = gmml::Split(residue_id, "_");
        std::string residue_index = underscore_split_token[2];
		std::string chain_id = this_residue->GetChainID();
		std::string resname = this_residue->GetName(); 
		AtomVector this_residue_atoms = this_residue->GetAtoms();

		for (unsigned int j = 0; j < cycle_atoms.size(); j++){
	    	MolecularModeling::Atom* cycle_atom = cycle_atoms[j];
	    	AtomVector cycle_neighbors = cycle_atom->GetNode()->GetNodeNeighbors();

	    	for (unsigned int k = 0; k < cycle_neighbors.size(); k++){
	        	MolecularModeling::Atom* neighbor = cycle_neighbors[k];
				std::string neighbor_element = neighbor->GetElementSymbol();

				if (std::find(cycle_atoms.begin(), cycle_atoms.end(), neighbor) != cycle_atoms.end()) continue;
				if (std::find(this_residue_atoms.begin(), this_residue_atoms.end(), neighbor) == this_residue_atoms.end()) continue; 
				if (neighbor_element != "N" && neighbor_element != "O") continue;
				
		    	available_atoms.emplace_back(available_atom(residue_index, resname, chain_id, cycle_atom->GetName(), neighbor->GetName()));
	    	}
		}
    }

    return available_atoms;
}

typedef std::vector<MolecularModeling::Atom*> AtomVector;
int main(int argc, char* argv[]){
    // Setup
    char* _GEMSHOME = std::getenv("GEMSHOME");
    if (!_GEMSHOME){
        std::cout << "GEMSHOME environment variable must be set. Aborting." << std::endl;
        return 0;
    }
    std::string GEMSHOME(_GEMSHOME);

    if (argc != 3){
        std::cout << "Usage: " << argv[0] << " <input_pdb> <output_file>" << std::endl;
        return 1;
    }
    std::string pdb_file_path_str = std::string(argv[1]);
    std::string output_file_path_str = std::string(argv[2]);

    std::string lib1 = GEMSHOME + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/amino12.lib";
    std::string lib2 = GEMSHOME + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminoct12.lib";
    std::string lib3 = GEMSHOME + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminont12.lib";
    std::vector<std::string> amino_libs = {lib1, lib2, lib3};
    std::string prep = GEMSHOME + "/gmml/dat/prep/GLYCAM_06j-1.prep";

    // Begin Evaluation of the input PDB file
    MolecularModeling::Assembly assemblyA(pdb_file_path_str, gmml::InputFileType::PDB); 
    VinaBondByDistanceForPDB(assemblyA, 0);

    // Valid = have sugars and available open valence positions.
    bool is_valid = false, pdb2glycam_available = false, sugars_detected = false;

    std::vector<Glycan::Monosaccharide*> monos= std::vector<Glycan::Monosaccharide*>();
    std::vector<Glycan::Oligosaccharide*> oligos = assemblyA.ExtractSugars(amino_libs,monos,false,false);

    if (!oligos.empty()){
        sugars_detected = true;
    }

    // Attempt pdb2glycam matching
    std::map<MolecularModeling::Atom*, MolecularModeling::Atom*> actual_template_atom_match;
    AtomVector atoms = assemblyA.GetAllAtomsOfAssembly();
    pdb2glycam_available = pdb2glycam_matching(pdb_file_path_str, actual_template_atom_match, atoms, gmml::InputFileType::PDB, amino_libs, prep);

    // Detect available atoms for derivatization
    std::vector<available_atom> available_atoms = detect_available_atoms(monos);
	
	std::ofstream output_file(output_file_path_str);
	if (output_file.fail()){
		std::cout << "Failed to create " << output_file_path_str << " for writing." << std::endl;
		std::exit(1);
	}

    for (unsigned int i = 0; i < available_atoms.size(); i++){
        available_atom& atom = available_atoms[i];
		//std::string residue_index_str_, atom_name_, atom_to_replace_;
		//std::cout << "Open for derivatization: " << atom.residue_index_str_ << "-" << atom.atom_name_ << "-" << atom.atom_to_replace_ << std::endl;
		atom.print_attribute(output_file);
    }
    output_file << "END" << std::endl;
    is_valid = !available_atoms.empty() && sugars_detected;

    output_file << std::endl;
    output_file << "valid_pdb=" << is_valid << std::endl;
    output_file << "pdb2glycam_available=" << pdb2glycam_available << std::endl;
    output_file << "sugars_detected=" << sugars_detected << std::endl;
    output_file << "available_atoms=" << available_atoms.size() << std::endl;
	output_file.close();

    return 0;
}