#ifndef MAPPING_CPP
#define MAPPING CPP

#include "mainparm.cpp"
#include "frcmod.cpp"
#include "../glycomimeticTool/utility.hpp"

#include <vector>
#include <string>

struct mol2_atom{
    mol2_atom(std::string index, std::string atom_name, std::string coord_x, std::string coord_y, std::string coord_z, std::string gaff_type, std::string residue_number, std::string residue_name, std::string gaff_charge){
        this->index_ = index;
        this->atom_name_ = atom_name;
        this->coord_x_ = coord_x;
        this->coord_y_ = coord_y;
        this->coord_z_ = coord_z;
        this->gaff_type_ = gaff_type;
        this->residue_number_ = residue_number;
        this->residue_name_ = residue_name;
        this->gaff_charge_ = std::stod(gaff_charge);
    }

    std::string index_; 
    std::string atom_name_;
    std::string coord_x_;
    std::string coord_y_;
    std::string coord_z_;
    std::string gaff_type_;
    std::string residue_number_;
    std::string residue_name_;
    double gaff_charge_;
};

void BuildBondFromMol2(MolecularModeling::Assembly& ligand_pdb, std::vector<std::pair<int, int>>& mol2_bonding_indices, std::string resp_charge_output_file_path){

    AtomVector all_atoms = ligand_pdb.GetAllAtomsOfAssembly();

    for (unsigned int i = 0; i < all_atoms.size(); i++){
        MolecularModeling::Atom* atom = all_atoms[i];
        std::cout << " Ligand pdb atom: " << all_atoms[i]->GetName() << std::endl;
        MolecularModeling::AtomNode* new_node = new MolecularModeling::AtomNode();

        new_node->SetAtom(atom);
        atom->SetNode(new_node); 
    }

    for (unsigned int i = 0; i < mol2_bonding_indices.size(); i++){
        std::pair<int, int>& bond_indices = mol2_bonding_indices[i];
        int atom1_index = bond_indices.first - 1;
        int atom2_index = bond_indices.second - 1;
        
        MolecularModeling::Atom* atom1 = all_atoms[atom1_index];
        MolecularModeling::Atom* atom2 = all_atoms[atom2_index];
        std::cout << "Atom " << atom1->GetName() << " is bonded to: " << atom2->GetName() << std::endl;

        atom1->GetNode()->AddNodeNeighbor(atom2);
        atom2->GetNode()->AddNodeNeighbor(atom1);

    }
    return;
}

void ParseMol2File(char* path, std::vector<mol2_atom>& mol2_atoms, std::vector<std::pair<int, int>>& mol2_bonding_indices){
    std::ifstream mol2(path);
    if (mol2.fail()){
        std::cout << "Failed to open mol2 file" << std::endl;
        std::exit(1);
    }

    std::string mol2_line_before_atoms;
    while(std::getline(mol2, mol2_line_before_atoms)){
        if (mol2_line_before_atoms.find("@<TRIPOS>ATOM") != std::string::npos){
            break;
        }
    }

    std::string index, atom_name, coord_x, coord_y, coord_z, gaff_type, residue_number, residue_name, gaff_charge;

    bool atom_section_ends = false;
    while (!atom_section_ends){
        mol2 >> index;
        if (index.find("@<TRIPOS>BOND") != std::string::npos){
            atom_section_ends =  true;
        }
        if (atom_section_ends){
            break;
        }
        mol2 >> atom_name >> coord_x >> coord_y >> coord_z >> gaff_type >> residue_number >> residue_name >> gaff_charge;
        mol2_atoms.emplace_back(mol2_atom(index, atom_name, coord_x, coord_y, coord_z, gaff_type, residue_number, residue_name, gaff_charge));
    }

    //Now we're at the 1st line of bonding info.
    std::string id, atom1_index, atom2_index, bond_type; 
    while (mol2 >> id >> atom1_index >> atom2_index >> bond_type){
        if (id.find("@<TRIPOS>SUBSTRUCTURE") != std::string::npos){
            break;
        }
        mol2_bonding_indices.emplace_back(std::pair<int, int>(std::stoi(atom1_index), std::stoi(atom2_index)));
    }

    mol2.close();
    return;
}

struct pdb2glycam_entry{
    //OLDNAME   RENAMED   IFGLYCAM  G_TYPE    G_CHARGE
    pdb2glycam_entry(std::string old_name, std::string new_name, std::string if_glycam, std::string glycam_type, std::string glycam_charge){
        this->old_name_ = old_name;
        this->new_name_ = new_name;
        this->if_glycam_ = if_glycam;
        this->glycam_type_ = glycam_type;
        this->glycam_charge_ = glycam_charge;
    }

    std::string old_name_;
    std::string new_name_;
    std::string if_glycam_;
    std::string glycam_type_;
    std::string glycam_charge_;
};

bool ParsePdb2GlycamLogFile(char* path, std::vector<pdb2glycam_entry>& pdb2glycam_entries){
    bool pdb2glycam_file_given = true;

    std::string path_str(path);
    if (path_str.find("none") != std::string::npos){
        pdb2glycam_file_given = false;
        return pdb2glycam_file_given;
    }

    std::ifstream pdb2glycam_log(path);
    if (pdb2glycam_log.fail()){
        std::cout << "Failed to open pdb2glcam log file: " << path << std::endl;
        std::exit(1);
    }

    //Discard the 1st line
    std::string line;
    std::getline(pdb2glycam_log, line);

    std::string old_name, new_name, if_glycam, glycam_type, glycam_charge;
    while(pdb2glycam_log >> old_name >> new_name >> if_glycam >> glycam_type >> glycam_charge){
        pdb2glycam_entries.emplace_back(pdb2glycam_entry(old_name, new_name, if_glycam, glycam_type, glycam_charge));
    }

    pdb2glycam_log.close();
    return pdb2glycam_file_given;
}

bool ParseRespChargeFile(std::string resp_charge_output_file_path, std::vector<double>& resp_charges){
    bool resp_charges_given = false;
    if (resp_charge_output_file_path.find("none") == std::string::npos){
        resp_charges_given = true;
    }

    std::ifstream resp_charge_output(resp_charge_output_file_path);
    if (resp_charge_output.fail() && resp_charges_given){
        std::cout << "Failed to open " << resp_charge_output_file_path << std::endl;
        std::exit(1);
    }

    std::string charge;
    while (resp_charge_output >> charge){
        resp_charges.push_back(std::stod(charge));
    }
    resp_charge_output.close();

    return resp_charges_given;
}

void ApplyGAFFParametersAndCharges(AtomVector atoms, std::vector<mol2_atom> mol2_atoms, std::vector<pdb2glycam_entry> pdb2glycam_log_info, bool resp_charges_given, std::vector<double>& resp_charges){
    for (unsigned int i = 0; i < atoms.size(); i++){
        MolecularModeling::Atom* pdb_atom = atoms[i];
        mol2_atom& antechamber_atom = mol2_atoms[i];
        double gaff_charge =antechamber_atom.gaff_charge_;
        pdb2glycam_entry& pdb2glycam_log_atom = pdb2glycam_log_info[i];

        if (resp_charges_given){
            pdb_atom->MolecularDynamicAtom::SetAtomType(antechamber_atom.gaff_type_);
            pdb_atom->MolecularDynamicAtom::SetCharge(resp_charges[i]);
        }
        else{
            pdb_atom->MolecularDynamicAtom::SetAtomType(antechamber_atom.gaff_type_);
            //This moiety resp charge is pre-computed. 
            double moiety_resp_charge = std::stod(pdb2glycam_log_atom.glycam_charge_);
            //pdb_atom->MolecularDynamicAtom::SetCharge(antechamber_atom.gaff_charge_);
            pdb_atom->MolecularDynamicAtom::SetCharge(moiety_resp_charge);
        }
    }
}

void OverWriteGAFFParametersWithGLYCAM(AtomVector atoms, std::vector<mol2_atom> mol2_atoms, std::vector<pdb2glycam_entry> pdb2glycam_log_info, std::map<MolecularModeling::Atom*, double>& atom_charge_diff_map, std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>>& glycam_gaff_bonds, bool resp_charges_given, std::vector<double>& resp_charges){

    for (unsigned int i = 0; i < atoms.size(); i++){
        MolecularModeling::Atom* pdb_atom = atoms[i];
        mol2_atom& antechamber_atom = mol2_atoms[i];
        double gaff_charge =antechamber_atom.gaff_charge_;
        pdb2glycam_entry& pdb2glycam_log_atom = pdb2glycam_log_info[i];

        if (pdb2glycam_log_atom.if_glycam_ == "YES"){
            pdb_atom->MolecularDynamicAtom::SetAtomType(pdb2glycam_log_atom.glycam_type_);
            double glycam_charge = std::stod(pdb2glycam_log_atom.glycam_charge_);
            pdb_atom->MolecularDynamicAtom::SetCharge(glycam_charge);

            bool is_glycam_gaff_bond = false;
            for (unsigned int i = 0; i < glycam_gaff_bonds.size(); i++){
                MolecularModeling::Atom* glycam_atom_this_bond = glycam_gaff_bonds[i].first;

                if (glycam_atom_this_bond == pdb_atom){
                    is_glycam_gaff_bond = true;
                    break;
                }
            }

            if (is_glycam_gaff_bond){
                double glycam_gaff_charge_difference = std::abs(glycam_charge - gaff_charge);
                atom_charge_diff_map[pdb_atom] = glycam_gaff_charge_difference;
                std::cout << "Diff map added " << pdb_atom->GetName() << std::endl;
            }
        }
        /*else if (resp_charges_given){
            pdb_atom->MolecularDynamicAtom::SetAtomType(antechamber_atom.gaff_type_);            
            pdb_atom->MolecularDynamicAtom::SetCharge(resp_charges[i]);
        }
        else{
            pdb_atom->MolecularDynamicAtom::SetAtomType(antechamber_atom.gaff_type_);
            double moiety_resp_charge = std::stod(pdb2glycam_log_atom.glycam_charge_);
            //pdb_atom->MolecularDynamicAtom::SetCharge(antechamber_atom.gaff_charge_);
            pdb_atom->MolecularDynamicAtom::SetCharge(moiety_resp_charge);
        }*/
    }
}

std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>> GetGlycamGaffBonds(AtomVector atoms, std::vector<pdb2glycam_entry> pdb2glycam_log_info){
    std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>> glycam_gaff_bonds;
    for (unsigned int i = 0; i < atoms.size(); i++){
        MolecularModeling::Atom* pdb_atom = atoms[i];
        pdb2glycam_entry& pdb2glycam_log_atom = pdb2glycam_log_info[i];

        if (pdb2glycam_log_atom.if_glycam_ == "YES"){

            AtomVector glycam_atom_neighbors = pdb_atom->GetNode()->GetNodeNeighbors();
            for (unsigned int j = 0; j < glycam_atom_neighbors.size(); j++){

                MolecularModeling::Atom* glycam_neighbor = glycam_atom_neighbors[j];
                AtomVector::iterator it = std::find(atoms.begin(), atoms.end(), glycam_neighbor);
                int neighbor_index = std::distance(atoms.begin(), it);
                pdb2glycam_entry& neighbor_pdb2glycam_log = pdb2glycam_log_info[neighbor_index];

                if (neighbor_pdb2glycam_log.if_glycam_ == "NO"){
                    glycam_gaff_bonds.emplace_back(std::make_pair(pdb_atom, glycam_neighbor));
                    std::cout << "Found glycam gaff bond " << pdb_atom->GetName() << "  " << glycam_neighbor->GetName() << std::endl;
                }
            }
        }
    }
    return glycam_gaff_bonds;
}

struct angle{
    angle(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3){
        this->atom1_ = atom1;
        this->atom2_ = atom2;
        this->atom3_ = atom3;
    }

    MolecularModeling::Atom* atom1_ = NULL;
    MolecularModeling::Atom* atom2_ = NULL;
    MolecularModeling::Atom* atom3_ = NULL;
};

struct torsion{
    torsion(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, MolecularModeling::Atom* atom4){
        this->atom1_ = atom1;
        this->atom2_ = atom2;
        this->atom3_ = atom3;
        this->atom4_ = atom4;
    }

    MolecularModeling::Atom* atom1_ = NULL;
    MolecularModeling::Atom* atom2_ = NULL;
    MolecularModeling::Atom* atom3_ = NULL;
    MolecularModeling::Atom* atom4_ = NULL;
};

bool IfAngleDuplicate(angle& this_angle, std::vector<angle>& existing_angles){
    MolecularModeling::Atom* this_atom1 = this_angle.atom1_;
    MolecularModeling::Atom* this_atom2 = this_angle.atom2_;
    MolecularModeling::Atom* this_atom3 = this_angle.atom3_;

    for (unsigned int i = 0; i < existing_angles.size(); i++){
        angle& existing_angle = existing_angles[i];
        MolecularModeling::Atom* existing_atom1 = existing_angle.atom1_;
        MolecularModeling::Atom* existing_atom2 = existing_angle.atom2_;
        MolecularModeling::Atom* existing_atom3 = existing_angle.atom3_;

        if ((this_atom1 == existing_atom1 && this_atom2 == existing_atom2 && this_atom3 == existing_atom3) || (this_atom1 == existing_atom3 && this_atom2 == existing_atom2 && this_atom3 == existing_atom1)){
            return true;
        }
    }

    return false;
}

bool AtomAlreadyInAngle(MolecularModeling::Atom* atom , angle& angle){
    if (atom != angle.atom1_ && atom != angle.atom2_ && atom != angle.atom3_){
        return false;
    }

    return true;
}

bool IfTorsionDuplicate(torsion& this_torsion, std::vector<torsion>& existing_torsions){
    MolecularModeling::Atom* this_atom1 = this_torsion.atom1_;
    MolecularModeling::Atom* this_atom2 = this_torsion.atom2_;
    MolecularModeling::Atom* this_atom3 = this_torsion.atom3_;
    MolecularModeling::Atom* this_atom4 = this_torsion.atom4_;

    for (unsigned int i = 0; i < existing_torsions.size(); i++){
        torsion& existing_torsion = existing_torsions[i];
        MolecularModeling::Atom* existing_atom1 = existing_torsion.atom1_;
        MolecularModeling::Atom* existing_atom2 = existing_torsion.atom2_;
        MolecularModeling::Atom* existing_atom3 = existing_torsion.atom3_;
        MolecularModeling::Atom* existing_atom4 = existing_torsion.atom4_;

        if ((this_atom1 == existing_atom1 && this_atom2 == existing_atom2 && this_atom3 == existing_atom3 && this_atom4 == existing_atom4) ||
            (this_atom1 == existing_atom4 && this_atom2 == existing_atom3 && this_atom3 == existing_atom2 && this_atom4 == existing_atom1)){
            return true;
        }
    }

    return false;
}

void ProfileGlycamGaffAnglesAndTorsions(std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>>& glycam_gaff_bonds, std::vector<angle>& glycam_gaff_angles, std::vector<torsion>& glycam_gaff_torsions){
    //Let A stands for glycam and B stands for gaff.
    for (unsigned int i = 0; i < glycam_gaff_bonds.size(); i++){
        MolecularModeling::Atom* glycam_atom = glycam_gaff_bonds[i].first;
        MolecularModeling::Atom* gaff_atom = glycam_gaff_bonds[i].second;

        //Based on bond AB, extend left or right for the 3rd atom.
        //Extend left
        AtomVector glycam_neighbor = glycam_atom->GetNode()->GetNodeNeighbors();
        for (unsigned int j = 0; j < glycam_neighbor.size(); j++){
            if (glycam_neighbor[j] != gaff_atom){
                MolecularModeling::Atom* atom1 = glycam_neighbor[j];
                angle new_angle(atom1, glycam_atom, gaff_atom);

                if (!IfAngleDuplicate(new_angle, glycam_gaff_angles)){
                    glycam_gaff_angles.push_back(new_angle);
                }
            }
        }

        //Extend right
        AtomVector gaff_neighbor = gaff_atom->GetNode()->GetNodeNeighbors();
        for (unsigned int j = 0; j < gaff_neighbor.size(); j++){
            if (gaff_neighbor[j] != glycam_atom){
                MolecularModeling::Atom* atom3 = gaff_neighbor[j];
                angle new_angle(glycam_atom, gaff_atom, atom3);

                if (!IfAngleDuplicate(new_angle, glycam_gaff_angles)){
                    glycam_gaff_angles.push_back(new_angle);
                }
            }
        }

        //For all angle terms, extend left or right for torsions. There will be repetition between extending the 1st set of angle to the right and the second set to the left.
        for (unsigned int i = 0; i < glycam_gaff_angles.size(); i++){
            angle& this_angle = glycam_gaff_angles[i];

            //Extend left
            AtomVector atom1_neighbors = this_angle.atom1_->GetNode()->GetNodeNeighbors();
            for (unsigned int j = 0; j < atom1_neighbors.size(); j++){
                MolecularModeling::Atom* this_neighbor = atom1_neighbors[j];

                if (!AtomAlreadyInAngle(this_neighbor, this_angle)){
                    torsion new_torsion = torsion(this_neighbor, this_angle.atom1_, this_angle.atom2_, this_angle.atom3_);
                    if (!IfTorsionDuplicate(new_torsion, glycam_gaff_torsions)){
                        glycam_gaff_torsions.push_back(new_torsion);
                    }
                }
            }

	    //Extend right
            AtomVector atom3_neighbors = this_angle.atom3_->GetNode()->GetNodeNeighbors();
            for (unsigned int j = 0; j < atom3_neighbors.size(); j++){
                MolecularModeling::Atom* this_neighbor = atom3_neighbors[j];

                if (!AtomAlreadyInAngle(this_neighbor, this_angle)){
                    torsion new_torsion = torsion(this_angle.atom1_, this_angle.atom2_, this_angle.atom3_, this_neighbor);
                    if (!IfTorsionDuplicate(new_torsion, glycam_gaff_torsions)){
                        glycam_gaff_torsions.push_back(new_torsion);
                    }
                }
            }
        }

    }
}

bool type_matches(std::string type1, std::string type2){
    gmml::Trim(type1);
    gmml::Trim(type2);

    if (type1 == type2){
        return true;
    }
    else if (type1 == "X" || type2 == "X"){
        return true;
    }

    return false;
}

bool atom_on_ring(MolecularModeling::Atom* atom, std::vector<AtomVector>& rings){
    for (unsigned int i = 0; i < rings.size(); i++){
        AtomVector& this_ring = rings[i];
	if (std::find(this_ring.begin(), this_ring.end(), atom) != this_ring.end()){
	    return true;
	}
    }

    return false;
}

std::vector<torsion> DetectImproperTorsions(AtomVector& pdb_atoms, std::vector<pdb2glycam_entry>& log_info){
    std::vector<torsion> improper_torsions;
    std::vector<AtomVector> rings = DetectCyclesByDFS(pdb_atoms);

    //If an atom is not on ring, and has exactly three neighbors forming a plane, then this is an improper torsion.
    for(unsigned int i = 0; i < pdb_atoms.size();  i++){
        MolecularModeling::Atom* atom = pdb_atoms[i];

	if (!atom_on_ring(atom, rings)){
	    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();

	    if (neighbors.size() == 3){
                double angle_degrees = GetDihedral(atom, neighbors[0], neighbors[1], neighbors[2], 0);	    
	        double angle_radians = angle_degrees / 180 * 3.14159;
	        double cosine = std::cos(angle_radians);

	        //If dihedral between atom1-3 and 2-4 is < 5 deg or > 175 deg, consider it planar and thus it is an improper dihedral
	        if (std::abs(cosine) > 0.996){
	            improper_torsions.emplace_back(torsion(atom, neighbors[0], neighbors[1], neighbors[2]));
	        } 
	    }
	}
    }

    //Check whether or not this improper torsion involves both glycam and gaff atom types. 
    std::vector<torsion> glycam_gaff_improper_torsions;
    for(unsigned int i = 0; i < improper_torsions.size(); i++){
        torsion& this_torsion = improper_torsions[i];
	bool glycam_atoms_exist = false, gaff_atoms_exist = false;

	MolecularModeling::Atom* atom1 = this_torsion.atom1_;
	MolecularModeling::Atom* atom2 = this_torsion.atom2_;
	MolecularModeling::Atom* atom3 = this_torsion.atom3_;
	MolecularModeling::Atom* atom4 = this_torsion.atom4_;

	int index_1 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom1));
	int index_2 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom2));
	int index_3 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom3));
	int index_4 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom4));

	if (log_info[index_1].if_glycam_ == "YES" || log_info[index_2].if_glycam_ == "YES" || log_info[index_3].if_glycam_ == "YES" || log_info[index_4].if_glycam_ == "YES"){
	    glycam_atoms_exist = true;
	}
	if (log_info[index_1].if_glycam_ == "NO" || log_info[index_2].if_glycam_ == "NO" || log_info[index_3].if_glycam_ == "NO" || log_info[index_4].if_glycam_ == "NO"){
	    gaff_atoms_exist = true;
	}

	if (glycam_atoms_exist && gaff_atoms_exist){
	    glycam_gaff_improper_torsions.push_back(this_torsion);
	}

    }

    return glycam_gaff_improper_torsions;
}

void ChargeAdjustment(std::string molecule_net_charge_str, std::vector<mol2_atom>& mol2_atoms, AtomVector& pdb_atoms, std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>>& glycam_gaff_bonds, std::map<MolecularModeling::Atom*, double>& atom_charge_diff_map, bool resp_charges_given, std::vector<double>& resp_charges){
    int num_atoms = mol2_atoms.size();
    //This net charge is parsed in as an argument, not the sum from antechamber mol2 file. 
    double molecule_net_charge = std::stod(molecule_net_charge_str);

    double antechamber_net_charge = 0;
    double glycam_gaff_mixed_net_charge = 0;

    for (unsigned int i = 0; i < num_atoms; i++){
        if (resp_charges_given){
            antechamber_net_charge += resp_charges[i];
        }
        else{
            antechamber_net_charge += mol2_atoms[i].gaff_charge_;
        }
        glycam_gaff_mixed_net_charge += pdb_atoms[i]->MolecularDynamicAtom::GetCharge();
    }

    //std::cout << "Antechamber net charge: " << antechamber_net_charge << " and mixed net charge: " << glycam_gaff_mixed_net_charge << std::endl;
    std::cout << "Real net charge: " << molecule_net_charge << " and mixed net charge: " << glycam_gaff_mixed_net_charge << std::endl;
    //double diff = antechamber_net_charge - glycam_gaff_mixed_net_charge;
    //Now use the parsed charge value instead of antechamber net charge. 
    double diff = molecule_net_charge - glycam_gaff_mixed_net_charge;

    //If there is no glycam-gaff bond (i.e natural ligand), no change is necessary. Set change to zero
    //double change_per_atom  = (glycam_gaff_bonds.empty()) ? 0 : diff / ( 2 * glycam_gaff_bonds.size());
    //std::cout << "Change per atom: " << change_per_atom << std::endl;

    double total_bonding_glycam_atom_charge_difference = 0; 
    for (std::map<MolecularModeling::Atom*, double>::iterator mapit = atom_charge_diff_map.begin(); mapit != atom_charge_diff_map.end(); mapit++){
        total_bonding_glycam_atom_charge_difference += mapit->second;
    }

    std::cout << "Total pertubation: " << total_bonding_glycam_atom_charge_difference << std::endl; 

    for (unsigned int i = 0; i < glycam_gaff_bonds.size(); i++){
	std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>& bond = glycam_gaff_bonds[i];
        MolecularModeling::Atom* glycam_atom = bond.first;
	double glycam_atom_current_charge = glycam_atom->MolecularDynamicAtom::GetCharge();

        double weight = atom_charge_diff_map[glycam_atom] / total_bonding_glycam_atom_charge_difference;
        double adjustment_per_atom_this_bond = (double) (diff * weight / 2) ; 

        MolecularModeling::Atom* gaff_atom = bond.second;
	double gaff_atom_current_charge = gaff_atom->MolecularDynamicAtom::GetCharge();
        std::cout << "Fraction for bond " << glycam_atom->GetName() << "-" << gaff_atom->GetName() << ": " << weight << " and adjustment per atom: " << adjustment_per_atom_this_bond << std::endl;

	//glycam_atom->MolecularDynamicAtom::SetCharge(glycam_atom_current_charge + change_per_atom);
	//gaff_atom->MolecularDynamicAtom::SetCharge(gaff_atom_current_charge + change_per_atom);
	glycam_atom->MolecularDynamicAtom::SetCharge(glycam_atom_current_charge + adjustment_per_atom_this_bond);
	gaff_atom->MolecularDynamicAtom::SetCharge(gaff_atom_current_charge + adjustment_per_atom_this_bond);

	std::cout << "Adjusted charge on glycam atom " << glycam_atom->GetName() << " from : " << glycam_atom_current_charge << " to " <<  glycam_atom->MolecularDynamicAtom::GetCharge() << std::endl;
	std::cout << "Adjusted charge on gaff   atom " << gaff_atom->GetName() <<   " from : " << gaff_atom_current_charge   << " to " <<  gaff_atom->MolecularDynamicAtom::GetCharge()   << std::endl;
    }

    antechamber_net_charge = 0; 
    glycam_gaff_mixed_net_charge = 0;
    for (unsigned int i = 0; i < num_atoms; i++){
        antechamber_net_charge += mol2_atoms[i].gaff_charge_;
        glycam_gaff_mixed_net_charge += pdb_atoms[i]->MolecularDynamicAtom::GetCharge();
    }
}

std::vector<std::vector<int>> arrangements_of_four = {{0,1,2,3}, {0,1,3,2}, {0,2,1,3}, {0,2,3,1}, {0,3,1,2}, {0,3,2,1}, {1,0,2,3}, {1,0,3,2},
                                                      {1,2,0,3}, {1,2,3,0}, {1,3,0,2}, {1,3,2,0}, {2,0,1,3}, {2,0,3,1}, {2,1,0,3}, {2,1,3,0},
                                                      {2,3,0,1}, {2,3,1,0}, {3,0,1,2}, {3,0,2,1}, {3,1,0,2}, {3,1,2,0}, {3,2,0,1}, {3,2,1,0}};

bool torsion_matches(torsion& glycam_gaff_torsion, TorsionBlock* std_torsion, AtomVector& pdb_atoms, std::vector<mol2_atom>& mol2_atoms, std::vector<TorsionBlock*>& interface_torsions, bool improper = false){
    MolecularModeling::Atom* atom1 =  glycam_gaff_torsion.atom1_;
    MolecularModeling::Atom* atom2 =  glycam_gaff_torsion.atom2_;
    MolecularModeling::Atom* atom3 =  glycam_gaff_torsion.atom3_;
    MolecularModeling::Atom* atom4 =  glycam_gaff_torsion.atom4_;

    int index1 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom1));
    int index2 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom2));
    int index3 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom3));
    int index4 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom4));

    std::string gaff_type1 = mol2_atoms[index1].gaff_type_;
    std::string gaff_type2 = mol2_atoms[index2].gaff_type_;
    std::string gaff_type3 = mol2_atoms[index3].gaff_type_;
    std::string gaff_type4 = mol2_atoms[index4].gaff_type_;

    std::string ipt = std_torsion->IPT;
    std::string jpt = std_torsion->JPT;
    std::string kpt = std_torsion->KPT;
    std::string lpt = std_torsion->LPT;

    bool match = false;
    //If improper torsion
    if (improper){
	std::vector<std::string> interface_torsion_gaff_types = {gaff_type1, gaff_type2, gaff_type3, gaff_type4};
        std::vector<std::string> template_types = {ipt, jpt, kpt, lpt};

        for (unsigned int i = 0; i < arrangements_of_four.size(); i++){
	    std::vector<int>& arrangement = arrangements_of_four[i];
	    if (type_matches(gaff_type1, template_types[arrangement[0]]) && type_matches(gaff_type2, template_types[arrangement[1]]) && type_matches(gaff_type3, template_types[arrangement[2]]) &&
		type_matches(gaff_type4, template_types[arrangement[3]])){
	        
		match = true;
	    }
            
	}

    }
    //If proper torsion
    else if ((type_matches(gaff_type1, ipt) && type_matches(gaff_type2, jpt) && type_matches(gaff_type3, kpt) && type_matches(gaff_type4, lpt)) ||
             (type_matches(gaff_type1, lpt) && type_matches(gaff_type2, kpt) && type_matches(gaff_type3, jpt) && type_matches(gaff_type4, ipt))){

	match = true;
    }

    if (match){
        TorsionBlock* new_torsion_block = new TorsionBlock(atom1->MolecularDynamicAtom::GetAtomType(), atom2->MolecularDynamicAtom::GetAtomType(), atom3->MolecularDynamicAtom::GetAtomType(),
                                                           atom4->MolecularDynamicAtom::GetAtomType(), "", "", "", "", std_torsion->COMMENT);
        interface_torsions.push_back(new_torsion_block);
        //The 1st term is all empty. Remove.
        new_torsion_block->terms.pop_back();
        //Replicate the terms of the std torsions

        std::vector<TorsionTerm*>& std_torsion_terms = std_torsion->terms;
        for (unsigned int k = 0; k < std_torsion_terms.size(); k++){
            TorsionTerm* term = std_torsion_terms[k];
            std::stringstream comment;
            if (improper){
                comment << term->COMMENT << "    Borrowed from improper " << ipt << "-" << jpt << "-" << kpt << "-" << lpt;
            }
            else{
                comment << term->COMMENT << "    Borrowed from " << ipt << "-" << jpt << "-" << kpt << "-" << lpt;
            }
            TorsionTerm* new_term = new TorsionTerm(term->IDIVF, term->PK, term->PHASE, term->PN, comment.str());
            new_torsion_block->AddTerm(new_term);
        }
    }

    return match;
}

void MapInterface2GaffParm(std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>>& glycam_gaff_bonds, std::vector<angle>& glycam_gaff_angles, std::vector<torsion>& glycam_gaff_torsions, 
		           std::vector<torsion>& glycam_gaff_improper_torsions, std::vector<BondLine*>& interface_bond_lines, std::vector<AngleLine*>& interface_angle_lines, 
			   std::vector<TorsionBlock*>& interface_torsions, std::vector<TorsionBlock*>& interface_improper_torsions, SixTwelvePotential* interface_nonbon, MainParm& amber_gaff_dat,
			   Frcmod& antechamber_frcmod, AtomVector& pdb_atoms, std::vector<mol2_atom>& mol2_atoms){

    std::vector<BondLine*> std_gaff_bonds = amber_gaff_dat.bond_lines_;
    std_gaff_bonds.insert(std_gaff_bonds.end(), antechamber_frcmod.bond_lines_.begin(), antechamber_frcmod.bond_lines_.end());

    std::vector<AngleLine*> std_gaff_angles = amber_gaff_dat.angle_lines_;
    std_gaff_angles.insert(std_gaff_angles.end(), antechamber_frcmod.angle_lines_.begin(), antechamber_frcmod.angle_lines_.end());

    std::vector<TorsionBlock*> std_gaff_torsions = amber_gaff_dat.torsion_blocks_;
    std_gaff_torsions.insert(std_gaff_torsions.end(), antechamber_frcmod.torsion_blocks_.begin(), antechamber_frcmod.torsion_blocks_.end());

    std::vector<TorsionBlock*> std_gaff_improper_torsions = amber_gaff_dat.improper_torsion_blocks_;
    std_gaff_improper_torsions.insert(std_gaff_improper_torsions.end(), antechamber_frcmod.improper_torsion_blocks_.begin(), antechamber_frcmod.improper_torsion_blocks_.end());

    for (unsigned int i = 0; i < glycam_gaff_bonds.size(); i++){
        std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>& this_bond = glycam_gaff_bonds[i];
	MolecularModeling::Atom* atom1 = this_bond.first;
	MolecularModeling::Atom* atom2 = this_bond.second;

	int index1 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom1));
	int index2 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom2));

	std::string gaff_type1 = mol2_atoms[index1].gaff_type_;
	std::string gaff_type2 = mol2_atoms[index2].gaff_type_;

	std::string real_type_1 = atom1->MolecularDynamicAtom::GetAtomType();
	std::string real_type_2 = atom2->MolecularDynamicAtom::GetAtomType();

	for (unsigned int j = 0; j < std_gaff_bonds.size(); j++){
	    BondLine* std_bond = std_gaff_bonds[j];
	    std::string& ibt = std_bond->IBT;
	    std::string& jbt = std_bond->JBT;

	    if ((type_matches(gaff_type1, ibt) && type_matches(gaff_type2, jbt)) || (type_matches(gaff_type1, jbt) && type_matches(gaff_type2,ibt))){

	        std::stringstream comment;
	        comment << std_bond->COMMENT << "    Borrowed from " << ibt << "-" << jbt;
		interface_bond_lines.emplace_back(new BondLine(real_type_1, real_type_2, std_bond->RK, std_bond->REQ, comment.str()));
		break;
	    }
	}
    }

    for (unsigned int i = 0; i < glycam_gaff_angles.size(); i++){
        angle& this_angle = glycam_gaff_angles[i];
	MolecularModeling::Atom* atom1 = this_angle.atom1_;
	MolecularModeling::Atom* atom2 = this_angle.atom2_;
	MolecularModeling::Atom* atom3 = this_angle.atom3_;

	int index1 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom1));
	int index2 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom2));
	int index3 = std::distance(pdb_atoms.begin(), std::find(pdb_atoms.begin(), pdb_atoms.end(), atom3));

	std::string gaff_type1 = mol2_atoms[index1].gaff_type_;
	std::string gaff_type2 = mol2_atoms[index2].gaff_type_;
	std::string gaff_type3 = mol2_atoms[index3].gaff_type_;

	std::string real_type_1 = atom1->MolecularDynamicAtom::GetAtomType();
	std::string real_type_2 = atom2->MolecularDynamicAtom::GetAtomType();
	std::string real_type_3 = atom2->MolecularDynamicAtom::GetAtomType();

	for (unsigned int j = 0; j < std_gaff_angles.size(); j++){
            AngleLine* std_angle = std_gaff_angles[j];
	    std::string itt = std_angle->ITT;
	    std::string jtt = std_angle->JTT;
	    std::string ktt = std_angle->KTT;

	    if ((type_matches(gaff_type1, itt) && type_matches(gaff_type2, jtt) && type_matches(gaff_type3, ktt)) || 
		(type_matches(gaff_type1, ktt) && type_matches(gaff_type2, jtt) && type_matches(gaff_type3, itt))){

		std::stringstream comment;
	        comment << std_angle->COMMENT << "    Borrowed from " << itt << "-" << jtt << "-" << ktt;
	        interface_angle_lines.emplace_back(new AngleLine(atom1->MolecularDynamicAtom::GetAtomType(), atom2->MolecularDynamicAtom::GetAtomType(), atom3->MolecularDynamicAtom::GetAtomType(),
					                         std_angle->TK, std_angle->TEQ, comment.str()));
		break;
	    }
	}
    }

    for (unsigned int i = 0; i < glycam_gaff_torsions.size(); i++){
        torsion& this_torsion = glycam_gaff_torsions[i];

	for (unsigned int j = 0; j < std_gaff_torsions.size(); j++){
	    TorsionBlock* std_torsion = std_gaff_torsions[j];

	    if(torsion_matches(this_torsion, std_torsion, pdb_atoms, mol2_atoms, interface_torsions, false)){
		break;
	    }
	}
    }

    for (unsigned int i = 0; i < glycam_gaff_improper_torsions.size(); i++){
        torsion& this_torsion = glycam_gaff_improper_torsions[i];

        for (unsigned int j = 0; j < std_gaff_improper_torsions.size(); j++){
            TorsionBlock* std_improper_torsion = std_gaff_improper_torsions[j];

	    if(torsion_matches(this_torsion, std_improper_torsion, pdb_atoms, mol2_atoms, interface_improper_torsions, true)){
                break;
            }
        }
    }
}
#endif
