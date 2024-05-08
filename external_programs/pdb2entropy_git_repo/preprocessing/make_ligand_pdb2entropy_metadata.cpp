#include<string>
#include<fstream>
#include<cstdlib>
#include<iterator>
#include<cmath>
#include<sstream>

#include "/home/yao/glycomimetics/src/vina_atom_data.hpp"
#include "/home/yao/glycomimetics/src/utility.hpp"
#include "includes/gmml.hpp"
#include "includes/MolecularModeling/assembly.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtfile.hpp"
#include "includes/utils.hpp"

bool bond_within_cycles(MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, std::vector<AtomVector>& cycles){
    for (unsigned int i = 0; i < cycles.size(); i++){
        AtomVector& cycle = cycles[i];
		//If both atom2 and atom3 on cycle, this bond is on the cycle.
		if (std::find(cycle.begin(), cycle.end(), atom2) != cycle.end() && std::find(cycle.begin(), cycle.end(), atom3) != cycle.end()){
	    	return true;
		}
    }
    return false;
}

bool bond_already_analyzed(MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>> bonds){
    for (unsigned int i = 0; i < bonds.size(); i++){
        std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>& bond = bonds[i];
		if (atom2 == bond.first && atom3 == bond.second){
	    	return true;
		}
		else if (atom3 == bond.first && atom2 == bond.second){
	    	return true;
		}
    }

    return false;
}

bool is_trigonal_planar(MolecularModeling::Atom* atom){
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    if (neighbors.size() != 3){
        return false;
    }

    double abs_improper_dihedral_degrees = std::abs(GetDihedral(neighbors[0], neighbors[1], neighbors[2], atom, 0));
    //Allow a cutoff of 2.5 degrees, below which it is deemed planar
    if (abs_improper_dihedral_degrees < 5 || std::abs(abs_improper_dihedral_degrees - 180) < 5){
        return true;
    }
    return false;
}

bool is_linear(MolecularModeling::Atom* atom){
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    if (neighbors.size() != 2){
        return false;
    }

    double abs_angle_degrees = std::abs(GetAngle(neighbors[0], atom, neighbors[1], 0))/3.14159*180;
    if (abs_angle_degrees < 5 || abs_angle_degrees > 175){
        return true;
    }
    return false;
}

bool is_anomeric_carbon(MolecularModeling::Atom* atom, std::vector<AtomVector> cycles){
    if (atom->GetElementSymbol() != "C"){
        return false;
    }

    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    if(neighbors.size() != 4){
        return false;
    }

    for (unsigned int i = 0; i < cycles.size(); i++){
        AtomVector& cycle = cycles[i];
		if (std::find(cycle.begin(), cycle.end(), atom) != cycle.end()){ //If carbon on ring
	    	int on_ring_O_or_N_count = 0, exocyclic_O_or_N_count = 0;
	    
	    	for (unsigned int j = 0; j < neighbors.size(); j++){
	        	MolecularModeling::Atom* neighbor = neighbors[j];
				std::string element = neighbor->GetElementSymbol();

				if (element == "O" || element == "N"){
		    		if (std::find(cycle.begin(), cycle.end(), neighbor) != cycle.end()){ //If neighbor on ring
		        		on_ring_O_or_N_count++;
		    		}
		    		else{  //If neighbor outside of ring
		        		exocyclic_O_or_N_count++;
		    		}
				}
	    	}

	    	if (on_ring_O_or_N_count == 1 && exocyclic_O_or_N_count ==1){
	        	return true;
	    	}
		}
    }

    return false;

}

bool bond_rotatable(MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, std::vector<AtomVector>& cycles){
    if (is_trigonal_planar(atom2) && is_trigonal_planar(atom3)){ //If double bond
        return false;
    }
    else if (is_linear(atom2) && is_linear(atom3)){  //If triple bond
        return false;
    }
    else if (is_anomeric_carbon(atom2, cycles) || is_anomeric_carbon(atom3, cycles)){ //If anomeric linkage
        return false;
    }

    return true;
}

bool is_methyl_sulfate_phosphate(MolecularModeling::Atom* atom){
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    if (neighbors.size() != 4){
        return false;
    }

    std::map<std::string, int> neighbor_element_count;
    for (unsigned int i = 0; i < neighbors.size(); i ++){
		MolecularModeling::Atom* neighbor = neighbors[i];
		std::string neighbor_element = neighbor->GetElementSymbol();
		neighbor_element_count[neighbor_element]++;
    }

    std::string element = atom->GetElementSymbol();
    if (element == "C" && neighbor_element_count["H"] == 3){ //Carbon bonded to 3 hydrogens, methyl
        return true;
    }
    else if ((element == "P" || element == "S") && neighbor_element_count["O"] == 4){ //Phosphate or sulfate bonded to 4 oxygens, phophate or sulfate
        return true;
    }

    return false;
}

int determine_atom_symmetry(MolecularModeling::Atom* atom){
    if (is_methyl_sulfate_phosphate(atom)){
        return 3;
    }
    else if (is_trigonal_planar(atom)){
        return 2;
    }

    return 1;
}

int determine_bond_symmetry(MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3){
    int atom2_symmetry = determine_atom_symmetry(atom2);
    int atom3_symmetry = determine_atom_symmetry(atom3);
    return std::max(atom2_symmetry, atom3_symmetry);    
}

bool bond_terminal(MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, MolecularModeling::Atom*& atom1, MolecularModeling::Atom*& atom4){
    AtomVector atom2_neighbors = atom2->GetNode()->GetNodeNeighbors();
    AtomVector atom3_neighbors = atom3->GetNode()->GetNodeNeighbors();

    AtomVector possible_atom1 = atom2_neighbors;
    possible_atom1.erase(std::find(possible_atom1.begin(), possible_atom1.end(), atom3));
    AtomVector possible_atom4 = atom3_neighbors;
    possible_atom4.erase(std::find(possible_atom4.begin(), possible_atom4.end(), atom2));

    //Now I find the bond atom2-atom3.Next find atom 1 and 4
    if (possible_atom1.empty() || possible_atom4.empty()){ //If this bond is terminal, cannot form a torsion
		return true;
    } 

    atom1 = possible_atom1[0];
    atom4 = possible_atom4[0];

    return false;
}

int main(int argc, char* argv[]){

	if (argc != 5){
		std::cout << "Usage: ./make_ligand_pdb2entropy_metadata.exe input_pdbqt_file output_torsion_dat_file output_pdb2trent_dat_file moiety_name" << std::endl;
		std::exit(1);
	}

    std::string sample_pdb_path(argv[1]);
    std::string torsion_dat_path(argv[2]);
    std::cout << "Torsion dat: " << torsion_dat_path << std::endl;
    std::ofstream torsion_dat(torsion_dat_path);
    if (torsion_dat.fail()){
        std::cout << "Failed to open " << torsion_dat_path << " for writing." << std::endl;
		std::exit(1);
    }

	//The ligand must be reformatted into a single residue. 
    MolecularModeling::Assembly sample_pdb(sample_pdb_path, gmml::InputFileType::PDBQT);
    VinaBondByDistance(sample_pdb, vina_atom_data);
	std::vector<std::string> non_ligand_resnames = {"WAT","HOH", "EP1", "EP2", "CA"};

	ResidueVector residues = sample_pdb.GetResidues();
	ResidueVector ligand_residues;
	ResidueVector receptor_residues;
    AtomVector ligand_atoms;

	int num_receptor_residues = 0;
	bool first_ligand_residue_encountered = false;
	int first_ligand_residue_number = -1;

	for (unsigned int i = 0; i < residues.size(); i++){
		MolecularModeling::Residue* res = residues[i];
		std::string resname = res->GetName();
		bool is_protein = res->CheckIfProtein();
		//std::cout << "This residue:  " << resname << std::endl;
		if (!is_protein && std::find(non_ligand_resnames.begin(), non_ligand_resnames.end(), resname) == non_ligand_resnames.end()){
			std::cout << "Found ligand residue: " << resname << std::endl;

			if (!first_ligand_residue_encountered){
				first_ligand_residue_number = i + 1;
				first_ligand_residue_encountered = true;
			}

			ligand_residues.push_back(res);
			AtomVector atoms = res->GetAtoms();
			ligand_atoms.insert(ligand_atoms.end(), atoms.begin(), atoms.end());
		}
		else if(is_protein){
			num_receptor_residues++;
			receptor_residues.push_back(res);
		}
	}

	if (ligand_residues.empty()){
		std::cout << "Error, no ligand residue found." << std::endl;
		std::exit(1);
	}

	std::string common_ligand_chain_id = "Y";
	std::stringstream alignment_token;
	alignment_token << common_ligand_chain_id << ":";

	double lr_dist_cutoff = 6.00;
	std::vector<int> rres_added;

	for (unsigned int i = 0; i < ligand_residues.size(); i++){
		MolecularModeling::Residue* lres = ligand_residues[i];
		AtomVector latoms = lres->GetAtoms();

		for (unsigned int j = 0; j < latoms.size(); j++){
			MolecularModeling::Atom* latom = latoms[j];
			GeometryTopology::Coordinate* lcoord = latom->GetCoordinate();
		
			for (unsigned int k = 0; k < receptor_residues.size(); k++){
				MolecularModeling::Residue* rres = receptor_residues[k];
				AtomVector ratoms = rres->GetAtoms();

				for (unsigned int l = 0; l < ratoms.size(); l++){
					MolecularModeling::Atom* ratom = ratoms[l];	
					GeometryTopology::Coordinate* rcoord = ratom->GetCoordinate();

					double lr_distance = lcoord->Distance(rcoord);
					if (lr_distance < lr_dist_cutoff){
						if (std::find(rres_added.begin(), rres_added.end(), k) == rres_added.end()){
							rres_added.push_back(k);
							alignment_token << k+1 << ",";
						}
					}
				}

			}
		}
	}

	std::string alignment_token_str = alignment_token.str();
	alignment_token_str.erase(alignment_token_str.size() -1, 1); //Removing trailing ","
	alignment_token_str += ":CA";

	std::string common_resname = ligand_residues[0]->GetName();
    std::vector<AtomVector> ligand_rings = DetectCyclesByDFS(ligand_atoms);

    //Look at each torsion
    std::string tor = "tor";
    int torsion_index = 1;
    std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom* >> bonds_already_analyzed;
	
	std::stringstream entropy_token;
	entropy_token << common_ligand_chain_id << ":" << first_ligand_residue_number << ":";
	bool no_heavy_atom_in_ligand = true;

    for (unsigned int i = 0; i < ligand_atoms.size(); i++){
        MolecularModeling::Atom* atom2 = ligand_atoms[i];
		if (atom2->GetElementSymbol() != "H"){
			no_heavy_atom_in_ligand = false;
			std::string atomname = atom2->GetName();
			entropy_token << atomname << ",";
		}
		
		AtomVector atom2_neighbors = atom2->GetNode()->GetNodeNeighbors();

		for (unsigned int j = 0; j < atom2_neighbors.size(); j++){
	    	MolecularModeling::Atom* atom3 = atom2_neighbors[j];
	    	if (bond_already_analyzed(atom2, atom3, bonds_already_analyzed)){ //prevent the same torsion from being analyzed twice
	        	continue;
	    	}
	    	bonds_already_analyzed.push_back(std::make_pair(atom2, atom3));

	    	if (bond_within_cycles(atom2, atom3, ligand_rings)){ //Bonds on a ring is definitely not rotatable
	        	continue;
	    	}

	    	if (!bond_rotatable(atom2, atom3, ligand_rings)){
	        	continue;
	    	}

	    	MolecularModeling::Atom* atom1 = NULL;
	    	MolecularModeling::Atom* atom4 = NULL;
	    	if (bond_terminal(atom2, atom3, atom1, atom4)){
	        	continue;
	    	}


	    	int bond_symmetry = determine_bond_symmetry(atom2, atom3);
	    	std::stringstream tors_name;
	    	tors_name << tor << torsion_index;
	    	std::cout << "TORS "<< common_resname << " " << tors_name.str() << " " << atom1->GetName() << " " << atom2->GetName() << " " << atom3->GetName() << " " << atom4->GetName() << " " << bond_symmetry << std::endl;
	    	torsion_dat       << "TORS "<< common_resname << " " << tors_name.str() << " " << atom1->GetName() << " " << atom2->GetName() << " " << atom3->GetName() << " " << atom4->GetName() << " " << bond_symmetry << std::endl;
	    	torsion_index++;
		}
    }
    torsion_dat.close();

	std::string entropy_token_str = entropy_token.str();

	if (no_heavy_atom_in_ligand){
		std::cout << "No heavy atom was found in the ligand. They are used to calculate TR entropy. Check what happened." << std::endl;
		std::exit(1);
	}

	//Remove trailing "," in entropy_token_str
	entropy_token_str.erase(entropy_token_str.length()-1, 1);

	std::string pdb2trent_dat_path(argv[3]);
    std::string moiety_name(argv[4]);
    std::cout << "Pdb2trent dat: " << pdb2trent_dat_path << std::endl;
    //std::ofstream pdb2trent_dat(pdb2trent_dat_path, std::ios_base::app);
    std::ofstream pdb2trent_dat(pdb2trent_dat_path);
    if (pdb2trent_dat.fail()){
        std::cout << "Failed to open " << torsion_dat_path << " for writing." << std::endl;
        std::exit(1);
    }

	pdb2trent_dat << moiety_name << "@" << alignment_token_str << "@" << entropy_token_str << std::endl;
	pdb2trent_dat.close();

	std::cout << alignment_token_str << std::endl;
	std::cout << entropy_token_str << std::endl;

    return 0;
}
