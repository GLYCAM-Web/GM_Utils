#include "includes/gmml.hpp"
#include "includes/MolecularModeling/assembly.hpp"
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

#include "../src/vina_atom_data.hpp"
#include "../src/vina_bond_by_distance_for_pdb.hpp"

#include <cstdlib>
#include <string>
#include <vector>

typedef std::vector<MolecularModeling::Atom*> AtomVector;
std::map<std::string, int> element_atomic_number_map = {{"H",1}, {"C", 6}, {"N", 7}, {"O", 8}, {"F", 9}, {"P", 15}, {"S", 16}, {"Cl", 17}, {"Br", 35}, {"I", 53}};
std::vector<std::string> polar_elements = {"N","O","F","P","S","Cl","Br","I"};

AtomVector DetectAliphaticHydrogens(AtomVector& atoms){
    AtomVector aliphatic_hydrogens;
    for (unsigned int i = 0; i < atoms.size(); i++){
        MolecularModeling::Atom* atom = atoms[i];
        std::string element = atom->GetElementSymbol();

        if (element == "C"){
            AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
            bool has_no_polar_neighbor = true;

            for (unsigned int j = 0; j < neighbors.size(); j++){
                MolecularModeling::Atom* neighbor = neighbors[j];

                if (neighbor->GetElementSymbol() == "H"){
                    aliphatic_hydrogens.push_back(neighbor); 
                }
            }
        }
    }

    return aliphatic_hydrogens;
}

bool is_trigonal_planar(MolecularModeling::Atom* atom){
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    if (neighbors.size() != 3){
        return false;
    }

    double abs_improper_dihedral_degrees = std::abs(GetDihedral(neighbors[0], neighbors[1], neighbors[2], atom, 0));
    //Allow a cutoff of 10 degrees, below which it is deemed planar
    if (abs_improper_dihedral_degrees < 10 || std::abs(abs_improper_dihedral_degrees - 180) < 10){
        return true;
    }
    return false;
}

std::vector<std::set<int>> FindSymmetricTerminalAtoms(MolecularModeling::Atom* atom, AtomVector& all_atoms){
    std::vector<std::set<int>> symmetrical_atom_indices;
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    bool tetrahedral_3_neighbor_nitrogen = false;
    if (atom->GetElementSymbol() == "N" && neighbors.size() == 3 && !is_trigonal_planar(atom)){
        tetrahedral_3_neighbor_nitrogen = true;
    }

    if (neighbors.size() == 4 || is_trigonal_planar(atom) || tetrahedral_3_neighbor_nitrogen){
        //Filter for terminal atoms bonded to this C or N (not bonded to any other atoms)
        std::map<std::string, int> neighbor_terminal_atom_element_count;
        AtomVector symmetrical_atoms;
        for (unsigned int j = 0; j < neighbors.size(); j++){
            MolecularModeling::Atom* neighbor = neighbors[j];

            if (neighbor->GetNode()->GetNodeNeighbors().size() == 1){//Is terminal atom
                std::string neighbor_element = neighbor->GetElementSymbol();
                if (neighbor_terminal_atom_element_count.find(neighbor_element) == neighbor_terminal_atom_element_count.end()){
                    neighbor_terminal_atom_element_count[neighbor_element] = 1;
                }
                else{
                    neighbor_terminal_atom_element_count[neighbor_element]++;
                }
            }
        }

        for (std::map<std::string, int>::iterator mapit = neighbor_terminal_atom_element_count.begin(); mapit != neighbor_terminal_atom_element_count.end(); mapit++){
            int count = mapit->second;
            std::string element = mapit->first;

            if (count > 1){
                std::set<int> symmetric_terminal_atoms_indices;
                for (unsigned int j = 0; j < neighbors.size(); j++){
                    MolecularModeling::Atom* neighbor = neighbors[j];
                    if (neighbor->GetElementSymbol() == element){
                        int index = std::distance(all_atoms.begin(), std::find(all_atoms.begin(), all_atoms.end(), neighbor)) + 1;
                        symmetric_terminal_atoms_indices.insert(index);
                    }
                }
                symmetrical_atom_indices.push_back(symmetric_terminal_atoms_indices);
            }

        }
    }
    return symmetrical_atom_indices;
}

std::vector<std::set<int>> DetectSymmetricalAtoms(AtomVector& all_atoms){
    std::vector<std::set<int>> symmetrical_atom_indices;
    for (unsigned int i = 0; i < all_atoms.size(); i++){
        MolecularModeling::Atom* atom = all_atoms[i];
        std::string element = atom->GetElementSymbol();
        
        if (element == "C" || element == "N" || element == "S" || element == "P"){
            std::vector<std::set<int>> symmetrical_terminal_atom_indices = FindSymmetricTerminalAtoms(atom, all_atoms);
            symmetrical_atom_indices.insert(symmetrical_atom_indices.end(), symmetrical_terminal_atom_indices.begin(), symmetrical_terminal_atom_indices.end());
        }
    }
    return symmetrical_atom_indices;
}

void WriteRespInputFile(MolecularModeling::Assembly& rgroup, std::string net_charge_str, std::string resp_input_path){
    std::ofstream resp_input_file(resp_input_path);
    if (resp_input_file.fail()){
        std::cout << "Failed to open " << resp_input_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_part = R"(single stage fitting
 &cntrl nmol=1, ihfree=0, qwt=0.0001,ioutopt=1, iqopt=1,
 &end
    1.0)";
    resp_input_file << constant_part << std::endl;
    resp_input_file << "Autogeneratd by C++" << std::endl;

    AtomVector all_atoms = rgroup.GetAllAtomsOfAssembly();
    resp_input_file << std::setw(5) << std::right << net_charge_str << std::setw(5) << std::right << all_atoms.size() << std::endl; 

    AtomVector aliphatic_hydrogens = DetectAliphaticHydrogens(all_atoms);
    std::vector<std::set<int>> symmetrical_atoms = DetectSymmetricalAtoms(all_atoms);

    for (unsigned int i = 0; i < all_atoms.size(); i++){
        MolecularModeling::Atom* atom = all_atoms[i];
        std::string element = atom->GetElementSymbol();

        if (element_atomic_number_map.find(element) == element_atomic_number_map.end()){
            std::cout << "No atomic number look up data for element: " << element << std::endl;
            std::exit(1);
        }

        int atomic_number = element_atomic_number_map[element];
        int restraint_number = -99999;

        //No charge for aliphatic hydrogens
        if (std::find(aliphatic_hydrogens.begin(), aliphatic_hydrogens.end(), atom) != aliphatic_hydrogens.end()){
            restraint_number = -1;
        }

        else{
            bool is_symmetric_atom = false;
            for (unsigned int j = 0; j < symmetrical_atoms.size(); j++){
                std::set<int> symmetrical_atom_set = symmetrical_atoms[j];

                for (std::set<int>::iterator setit = symmetrical_atom_set.begin(); setit != symmetrical_atom_set.end(); setit++){
                    int set_index = std::distance(symmetrical_atom_set.begin(), setit);
                    int atom_index = *(setit);

                    if (atom_index == i + 1){
                        is_symmetric_atom = true;

                        if (set_index == 0){ //The 1st atom in the set has no restraint
                            restraint_number = 0;
                        }
                        else{ //Otherwise, it is set to the index of the 1st atom in the set. 
                            restraint_number = *(symmetrical_atom_set.begin());
                        }
                    }
                }
            }
            if (!is_symmetric_atom){ //No restraint
                restraint_number = 0;
            }
        }

        //Debugging now. Apply no restraint by using 0 all the time. 
        //restraint_number = 0;
        resp_input_file << std::setw(5) << std::right << atomic_number << std::setw(5) << std::right << restraint_number << std::endl;

    }
    resp_input_file << std::endl;
    resp_input_file.close();
}

int main(int argc, char* argv[])
{
    std::string pdbqt_file_path(argv[1]);
    std::string net_charge(argv[2]);
    std::string resp_input_path(argv[3]);

    //MolecularModeling::Assembly rgroup(pdbqt_file_path, gmml::InputFileType::PDBQT);
    //VinaBondByDistance(rgroup, vina_atom_data);
    MolecularModeling::Assembly rgroup(pdbqt_file_path, gmml::InputFileType::PDB);
    VinaBondByDistanceForPDB(rgroup, 0);

    WriteRespInputFile(rgroup, net_charge, resp_input_path);
    
    return 0;
} 

