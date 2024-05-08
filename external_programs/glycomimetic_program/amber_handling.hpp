#ifndef AMBER_HANDLING_HPP
#define AMBER_HANDLING_HPP

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


void RenameDisulfideCYS2CYX(std::vector<MolecularModeling::Residue*>& assembly_residues){
   for (unsigned int i = 0; i < assembly_residues.size(); i++){
       MolecularModeling::Residue* residue = assembly_residues[i];
       std::string resname = residue->GetName();

       if (resname == "CYS"){
           AtomVector res_atoms = residue->GetAtoms();    
	       for (unsigned int j = 0; j < res_atoms.size(); j++){
	           MolecularModeling::Atom* this_res_atom = res_atoms[j];

	           if (this_res_atom->GetName() == "SG"){
	               AtomVector sg_atom_neighbors = this_res_atom->GetNode()->GetNodeNeighbors();
		           for (unsigned int k = 0; k < sg_atom_neighbors.size(); k++){
		               MolecularModeling::Atom* this_sg_neighbor = sg_atom_neighbors[k];
		               MolecularModeling::Residue* neighbor_residue = this_sg_neighbor->GetResidue();

		               //If this SG neighbor is bonded to another SG atom in another residue, then both CYS gets renames to CYX
		               if (neighbor_residue != residue && neighbor_residue->GetName() == "CYS" && this_sg_neighbor->GetName() == "SG"){
		                   residue->SetName("CYX");
			               neighbor_residue->SetName("CYX");
		               }
		           }    
	           }
	       }
       }
   }

}

#endif
