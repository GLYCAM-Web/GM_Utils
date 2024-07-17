#ifndef VINA_BOND_BY_DISTANCE_HPP 
#define VINA_BOND_BY_DISTANCE_HPP 

#include "includes/gmml.hpp"
#include "includes/MolecularModeling/assembly.hpp"
#include "includes/MolecularModeling/atom.hpp"
#include "includes/MolecularModeling/atomnode.hpp"

#include <iostream>
#include <string>
#include <map>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <utility>
#include <iterator>

std::map<std::string, double> element_covalent_radius_map = {
        { "C", 0.77}, //  0
        { "N", 0.75}, //  2
        { "O", 0.73}, //  3
        { "P", 1.06}, //  4
        { "S", 1.02}, //  5
        { "H", 0.37}, //  6
        { "F", 0.71}, //  7
        { "I", 1.33}, //  8
        {"Mg", 1.30}, // 13
        {"Mn", 1.39}, // 14
        {"Zn", 1.31}, // 15
        {"Ca", 0.00}, // 16
        {"Fe", 1.25}, // 17
        {"Cl", 0.99}, // 18
        {"Br", 1.14}  // 19
};

bool element_in_map(std::string element){
    if (element_covalent_radius_map.find(element) != element_covalent_radius_map.end()){
        return true;		    
    }

    return false;

}

void VinaBondByDistanceForPDB(MolecularModeling::Assembly& assembly, int model_index = 0){
    AtomVector all_atoms_of_assembly = assembly.GetAllAtomsOfAssembly();
    double allowance_factor = 1.15;

    for(MolecularModeling::AtomVector::iterator it = all_atoms_of_assembly.begin(); it != all_atoms_of_assembly.end(); it++){
        MolecularModeling::Atom* atom = (*it);
        MolecularModeling::AtomNode* atom_node = new MolecularModeling::AtomNode();
        atom_node->SetAtom(atom);
        atom->SetNode(atom_node);
    }

    for(MolecularModeling::AtomVector::iterator it = all_atoms_of_assembly.begin(); it != --all_atoms_of_assembly.end(); it++)
    {
        MolecularModeling::Atom* atom = (*it);
	    std::string atom_element = atom->GetElementSymbol();
        MolecularModeling::AtomNode* atom_node = atom->GetNode();

	    for(MolecularModeling::AtomVector::iterator it1 = it + 1; it1 != all_atoms_of_assembly.end(); it1++)
        {
            MolecularModeling::Atom* neighbor_atom = (*it1);
	        std::string neighbor_atom_element = neighbor_atom->GetElementSymbol();
	        double sum_covalent_radii= (element_in_map(atom_element) && element_in_map(neighbor_atom_element)) ? element_covalent_radius_map[atom_element] + element_covalent_radius_map[neighbor_atom_element] : 1.65 ;
	        double cutoff = allowance_factor * sum_covalent_radii;

            // X distance
            if(atom->GetCoordinates().at(model_index)->GetX() - neighbor_atom->GetCoordinates().at(model_index)->GetX() < cutoff)
            {
                // Y distance
                if(atom->GetCoordinates().at(model_index)->GetY() - neighbor_atom->GetCoordinates().at(model_index)->GetY() < cutoff)
                {
                    // Z distance
                    if(atom->GetCoordinates().at(model_index)->GetZ() - neighbor_atom->GetCoordinates().at(model_index)->GetZ() < cutoff)
                    {
                        if((atom->GetCoordinates().at(model_index)->Distance(*(neighbor_atom->GetCoordinates().at(model_index)))) < cutoff)
                        {
                            MolecularModeling::AtomNode* neighbor_node = neighbor_atom->GetNode();
                            atom_node->AddNodeNeighbor(neighbor_atom);
                            neighbor_node->AddNodeNeighbor(atom);
                        }
                    }
                }
            }
        }
    }

}
#endif
