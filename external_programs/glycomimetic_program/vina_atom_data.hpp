#ifndef VINA_ATOM_DATA_HPP
#define VINA_ATOM_DATA_HPP

#include "includes/gmml.hpp"
#include "includes/MolecularModeling/atom.hpp"
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

#include "utility.hpp"

#include <string>
#include <cstring>

typedef std::vector<MolecularModeling::Atom*> AtomVector;

struct atom_data {
    std::string name;
    double radius;
    double depth;
    double solvation;
    double volume;
    double covalent_radius; // from http://en.wikipedia.org/wiki/Atomic_radii_of_the_elements_(data_page)
};

// generated from edited AD4_parameters.data using a script, 
// then covalent radius added from en.wikipedia.org/wiki/Atomic_radii_of_the_elements_(data_page)
atom_data vina_atom_data[] = { // name, radius, depth, solvation parameter, volume, covalent radius
        { "C",    2.00000,    0.15000,   -0.00143,   33.51030,   0.77}, //  0
        { "A",    2.00000,    0.15000,   -0.00052,   33.51030,   0.77}, //  1
        { "N",    1.75000,    0.16000,   -0.00162,   22.44930,   0.75}, //  2
        { "O",    1.60000,    0.20000,   -0.00251,   17.15730,   0.73}, //  3
        { "P",    2.10000,    0.20000,   -0.00110,   38.79240,   1.06}, //  4
        { "S",    2.00000,    0.20000,   -0.00214,   33.51030,   1.02}, //  5
        { "H",    1.00000,    0.02000,    0.00051,    0.00000,   0.37}, //  6
        { "F",    1.54500,    0.08000,   -0.00110,   15.44800,   0.71}, //  7
        { "I",    2.36000,    0.55000,   -0.00110,   55.05850,   1.33}, //  8
        {"NA",    1.75000,    0.16000,   -0.00162,   22.44930,   0.75}, //  9
        {"OA",    1.60000,    0.20000,   -0.00251,   17.15730,   0.73}, // 10
        {"SA",    2.00000,    0.20000,   -0.00214,   33.51030,   1.02}, // 11
        {"HD",    1.00000,    0.02000,    0.00051,    0.00000,   0.37}, // 12
        {"Mg",    0.65000,    0.87500,   -0.00110,    1.56000,   1.30}, // 13
        {"Mn",    0.65000,    0.87500,   -0.00110,    2.14000,   1.39}, // 14
        {"Zn",    0.74000,    0.55000,   -0.00110,    1.70000,   1.31}, // 15
        {"Ca",    0.99000,    0.55000,   -0.00110,    2.77000,   0.00}, // 16
        {"Fe",    0.65000,    0.01000,   -0.00110,    1.84000,   1.25}, // 17
        {"Cl",    2.04500,    0.27600,   -0.00110,   35.82350,   0.99}, // 18
        {"Br",    2.16500,    0.38900,   -0.00110,   42.56610,   1.14}, // 19
        {"NR",    1.75000,    0.16000,   -0.00162,   22.44930,   0.75}, // 20 
};
//{"Ca",    0.99000,    0.55000,   -0.00110,    2.77000,   1.74} Temporary changing Ca's radius to 0. This 1.74 value is causing CA to be covalently bonded to its chelated moieties. 

int EL_C = 0, EL_N = 1, EL_O = 2, EL_P = 3, EL_S = 4, EL_H = 5, EL_F = 6, EL_I = 7, EL_MET = 8, EL_Cl = 9, EL_Br = 10, EL_NR = 11;
int EL_SIZE = 12;
/*std::map<std::string, std::string> AD_EL_TYPE_MAP = {
        {"C","EL_C"}, {"A","EL_C"}, {"N","EL_N"}, {"NA", "EL_N"}, {"O","EL_O"}, {"P","EL_P"}, {"S","EL_S"}, {"H","EL_H"}, {"F","EL_F"}, {"I","EL_I"}, {"Na","EL_N"}, {"OA","EL_O"},
        {"SA","EL_S"}, {"HD","EL_H"}, {"Mg","EL_MET"}, {"Mn","EL_MET"}, {"Zn","EL_MET"}, {"Ca","EL_MET"}, {"Fe","EL_MET"}, {"Cl","EL_Cl"}, {"Br", "EL_Br"}, {"NR", "EL_NR"}
};*/
std::map<std::string, int> AD_EL_TYPE_MAP = {
        {"C", EL_C}, {"A",EL_C}, {"N",EL_N}, {"NA", EL_N}, {"O",EL_O}, {"P",EL_P}, {"S",EL_S}, {"H",EL_H}, {"HD",EL_H}, {"F",EL_F}, {"I",EL_I}, {"Na",EL_N}, {"OA",EL_O},
        {"SA",EL_S}, {"HD",EL_H}, {"Mg",EL_MET}, {"Mn",EL_MET}, {"Zn",EL_MET}, {"Ca",EL_MET}, {"Fe",EL_MET}, {"Cl",EL_Cl}, {"Br", EL_Br}, {"NR", EL_NR}
};

int XS_H = 0, XS_C_H = 1, XS_C_A_P = 2, XS_C_A_H = 3, XS_C_P = 4, XS_N_D = 5, XS_N_P = 6, XS_N_A = 7, XS_N_DA = 8, XS_O_P = 9, XS_O_D = 10, XS_O_A = 11, XS_O_DA = 12, XS_S_P = 13,
    XS_P_P = 14, XS_F_H = 15, XS_Cl_H = 16, XS_Br_H = 17, XS_I_H = 18, XS_Met_D = 19, XS_N_R = 20;
int XS_SIZE = 21;
/*std::map<std::string, double> element_xs_vdw_radii = {{"XS_H", 1.2}, {"XS_C_H", 1.9}, {"XS_C_A_P", 1.9}, {"XS_C_A_H", 1.9}, {"XS_C_P", 1.9}, {"XS_N_D", 1.8}, {"XS_N_P", 1.8}, {"XS_N_D", 1.8}, 
	                                              {"XS_N_A", 1.8}, {"XS_N_DA", 1.8},  {"XS_O_P", 1.7}, {"XS_O_D", 1.7}, {"XS_O_A", 1.7}, {"XS_O_DA", 1.7}, {"XS_S_P", 2.0}, 
						      {"XS_P_P", 2.1}, {"XS_F_H",1.5},   {"XS_Cl_H", 1.8}, {"XS_Br_H", 2.0}, {"XS_I_H", 2.2}, {"XS_Met_D", 1.2}, {"XS_N_R", 1.8}};*/
std::map<int, double> element_xs_vdw_radii = {{XS_H, 1.2}, {XS_C_H, 1.9}, {XS_C_A_P, 1.9}, {XS_C_A_H, 1.9}, {XS_C_P, 1.9}, {XS_N_D, 1.8}, {XS_N_P, 1.8}, {XS_N_D, 1.8}, 
	                                              {XS_N_A, 1.8}, {XS_N_DA, 1.8},  {XS_O_P, 1.7}, {XS_O_D, 1.7}, {XS_O_A, 1.7}, {XS_O_DA, 1.7}, {XS_S_P, 2.0}, 
						      {XS_P_P, 2.1}, {XS_F_H,1.5},   {XS_Cl_H, 1.8}, {XS_Br_H, 2.0}, {XS_I_H, 2.2}, {XS_Met_D, 1.2}, {XS_N_R, 1.8}};


//std::vector<std::string> hydrophobic_elements = {"XS_C_A_H","XS_C_H","XS_Cl_H","XS_Br_H","XS_I_H","XS_F_H"};
std::vector<int> hydrophobic_elements = {XS_C_A_H, XS_C_H, XS_Cl_H, XS_Br_H, XS_I_H, XS_F_H};
//std::vector<std::string> hb_acceptor_types = {"XS_N_A","XS_N_DA","XS_O_A","XS_O_DA"};
std::vector<int> hb_acceptor_types = {XS_N_A, XS_N_DA, XS_O_A, XS_O_DA};
//std::vector<std::string> hb_donor_types = {"XS_N_D","XS_O_D","XS_N_DA","XS_O_DA","XS_Met_D","XS_N_R"};
std::vector<int> hb_donor_types = {XS_N_D, XS_O_D, XS_N_DA, XS_O_DA, XS_Met_D, XS_N_R};

double cutoff = 8, heavy_heavy_cutoff_for_HH_repulsion = 6, HH_repulsion_cutoff = 2.5;
double gau1_ofs = 0, gau1_wdh = 0.5, gau2_ofs = 3, gau2_wdh = 2, rep_ofs = 0, pho_good = 0.5, pho_bad = 1.5, hb_good = -0.7, hb_bad = 0;
double wt_gau1 = -0.035579, wt_gau2 = -0.005156, wt_rep = 0.840245, wt_pho = -0.035069, wt_hb = -0.587439, wt_catpi = -0.40, wt_pi_pi = -0.00, wt_ch_pi = -0.600000;
double catpi_const = 0.45, sigma = 0.5, miu = 3.8;
//double pi_pi_const = 0.052, pi_pi_sigma = 0.43, pi_pi_miu = 4.70;
double pi_pi_const = 0.25, pi_pi_sigma = 0.80, pi_pi_miu = 4.40, pi_repulsion_k = 4000.0, pi_repulsion_dispow = 8.30, pi_repulsion_startdis = 3.0;
double pi_repulsion_dispow2 = 3.10, pi_repulsion_startdis2 = 4.2, pi_repulsion_dispow3 = 3.40, pi_repulsion_startdis3 = 4.7;

double pi_cauchy_const = 0.80, pi_cauchy_gamma = 4.0, pi_cauchy_x0 = 5.5;

double chpi_freq = 1.00, chpi_phase = 0.00, chpi_cos_pow =2.00; //Peak at 0 deg. 
//double chpi_freq = (18.00/17.00), chpi_phase = -(2.00 * 3.1415/17.00), chpi_cos_pow = 2.00; //Peak at 5 deg. 
//double chpi_freq = (9.00/8.00), chpi_phase = -(1.00 * 3.1415/16.00), chpi_cos_pow = 2.00; //Peak at 10 deg. 
//double chpi_freq = 1.20, chpi_phase = -0.31415, chpi_cos_pow = 2.00; //Peak at 15 deg. 
//double chpi_freq = (9.00/7.00), chpi_phase = -(1.00 * 3.1415/7.00), chpi_cos_pow = 2.00; //Peak at 20 deg. 

unsigned int VINA_ATOM_DATA_ARRAY_SIZE = sizeof(vina_atom_data)/sizeof(vina_atom_data[0]);

double slope_step(double x_bad, double x_good, double x){
        if(x_bad < x_good) {
                if(x <= x_bad) return 0;
                if(x >= x_good) return 1;
        }
        else {
                if(x >= x_bad) return 0;
                if(x <= x_good) return 1;
        }
        return (x - x_bad) / (x_good - x_bad);
}

bool is_acceptor(std::string& ad_type){
        return ad_type == "OA" || ad_type == "NA";
}

bool is_heteroatom(MolecularModeling::Atom* atom){
    std::string ad_type = atom->MolecularDynamicAtom::GetAtomType();
    return ad_type != "A" && ad_type != "C" && ad_type != "H" && ad_type != "HD";
}

bool bonded_to_heteroatom(MolecularModeling::Atom* atom){
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    for (AtomVector::iterator it = neighbors.begin(); it != neighbors.end(); it++){
        if (is_heteroatom(*it)){
            return true;
        }
    }
    return false;
}

bool bonded_to_HD(MolecularModeling::Atom* atom){
    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    for (AtomVector::iterator it = neighbors.begin(); it != neighbors.end(); it++){
        if ((*it)->MolecularDynamicAtom::GetAtomType()  == "HD"){
            return true;
        }
    }
    return false;
}

bool atom_exists_between(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, AtomVector& relevant_atoms){
    double atom_1_2_distance = atom1->GetCoordinate()->Distance(atom2->GetCoordinate());
    for (AtomVector::iterator it1 = relevant_atoms.begin(); it1 != relevant_atoms.end(); it1++){
        MolecularModeling::Atom* atom3 = *it1;
        if (atom3 == atom1 || atom3 == atom2) continue;
        double atom_1_3_distance = atom1->GetCoordinate()->Distance(atom3->GetCoordinate());
        double atom_2_3_distance = atom2->GetCoordinate()->Distance(atom3->GetCoordinate());
        if (atom_1_3_distance < atom_1_2_distance && atom_2_3_distance < atom_1_2_distance){
            //std::cout << "My atom exists between return ture" << std::endl;
            return true;
        }
    }
    //std::cout << "My atom exists between return false" << std::endl;
    return false;
}

void VinaBondByDistance(MolecularModeling::Assembly& assembly, atom_data(& vina_atom_data)[21] ){
    AtomVector all_atoms = assembly.GetAllAtomsOfAssembly();
    double allowance_factor = 1.1;
    //Vina bead approximation
    std::vector<std::pair<MolecularModeling::Atom*, AtomVector> > beads;
    double bead_radius = 15;
    for (AtomVector::iterator it1 = all_atoms.begin(); it1 != all_atoms.end(); it1++){
        MolecularModeling::Atom* atom1 = *it1;
        bool in_bead = false;
        for (std::vector<std::pair<MolecularModeling::Atom*, AtomVector> >::iterator bead_it = beads.begin(); bead_it != beads.end(); bead_it++){
            std::pair<MolecularModeling::Atom*, AtomVector>& bead_instance = *bead_it;
            MolecularModeling::Atom* center_atom = bead_instance.first;
            AtomVector& atoms_in_bead = bead_instance.second;
            if (atom1->GetCoordinate()->Distance(center_atom->GetCoordinate()) < bead_radius){
                atoms_in_bead.push_back(atom1);
                in_bead = true;
                break;
            }
        }
        if (!in_bead){
            AtomVector new_vec;
            new_vec.push_back(atom1);
            beads.push_back(std::make_pair(atom1, new_vec));
        }
    }
    
    for (AtomVector::iterator it1 = all_atoms.begin(); it1 != all_atoms.end(); it1++){
        MolecularModeling::Atom* atom = *it1;
        MolecularModeling::AtomNode* new_node = new MolecularModeling::AtomNode();
        new_node->SetAtom(atom);
        atom->SetNode(new_node);
    }

    unsigned int max_size = sizeof(vina_atom_data)/sizeof(vina_atom_data[0]);
    for (AtomVector::iterator it1 = all_atoms.begin(); it1 != all_atoms.end(); it1++){
        MolecularModeling::Atom* atom1 = *it1;
        std::string adtype1 = atom1->MolecularDynamicAtom::GetAtomType();
        double radius_1 = 1.74;//Equivalent to max_covalent_radius method in Vina, which return the max value (Ca).
        for (unsigned int i = 0; i < max_size; i++){
            if (vina_atom_data[i].name == adtype1){
                radius_1 = vina_atom_data[i].covalent_radius;
                break;
            }
        }

        //Find relevant atoms.
        AtomVector relevant_atoms;
        double bead_cutoff = bead_radius + allowance_factor * (radius_1 + 1.74);
        //std::cout << "My bead cutoff is : " << bead_cutoff << std::endl;

        for (std::vector<std::pair<MolecularModeling::Atom*, AtomVector> >::iterator bead_it = beads.begin(); bead_it != beads.end(); bead_it++){
            std::pair<MolecularModeling::Atom*, AtomVector>& bead_instance = *bead_it;
            MolecularModeling::Atom* center_atom = bead_instance.first;
            AtomVector& atoms_in_bead = bead_instance.second;
            if (atom1->GetCoordinate()->Distance(center_atom->GetCoordinate()) > bead_cutoff) continue;

            for (AtomVector::iterator it2 = atoms_in_bead.begin(); it2 != atoms_in_bead.end(); it2++){
                MolecularModeling::Atom* atom2 = *it2;
                if (atom1 == atom2) continue;
                double relevant_atom_cutoff = allowance_factor * (radius_1 + 1.74);
                double x1 = atom1->GetCoordinate()->GetX(), y1 = atom1->GetCoordinate()->GetY(), z1 = atom1->GetCoordinate()->GetZ();
                double x2 = atom2->GetCoordinate()->GetX(), y2 = atom2->GetCoordinate()->GetY(), z2 = atom2->GetCoordinate()->GetZ();
                double delta_x = std::abs(x1 - x2), delta_y = std::abs(y1 - y2), delta_z = std::abs(z1 - z2);
                //Do bond by distance
                if (delta_x < relevant_atom_cutoff){
                    if (delta_y < relevant_atom_cutoff) {
                        if (delta_z < relevant_atom_cutoff){
                            double distance = std::pow(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z, 0.5);
                            if(distance < relevant_atom_cutoff){
                                //relevant_atoms_map[atom1].push_back(atom2);
                                relevant_atoms.push_back(atom2);
                            }
                        }
                    }
                }
            }
        }

        //Find bonded atoms
        unsigned int atom_1_global_index = std::distance(all_atoms.begin(), it1);
        for (AtomVector::iterator relevant_it = relevant_atoms.begin(); relevant_it != relevant_atoms.end(); relevant_it++){
            MolecularModeling::Atom* relevant_atom = *relevant_it;
            AtomVector::iterator relevant_global_it = std::find (all_atoms.begin(), all_atoms.end(), relevant_atom);
            unsigned int relevant_global_index = std::distance(all_atoms.begin(), relevant_global_it);

            if (atom_1_global_index >= relevant_global_index) continue; //A bonding pair doesn't get considered twice
            std::string adtype_relevant = relevant_atom->MolecularDynamicAtom::GetAtomType();
            double radius_relevant = 1.74;
            for (unsigned int i = 0; i < max_size; i++){
                if (vina_atom_data[i].name == adtype_relevant){
                    radius_relevant = vina_atom_data[i].covalent_radius;
                    break;
                }
            }
	    //std::cout << "Relevant atom name " << relevant_atom->GetName() << " and radius relevant " << radius_relevant << std::endl;
	    //std::cout << "Radius 1 " << radius_1 << std::endl;
            double bonding_cutoff = allowance_factor * (radius_1 + radius_relevant);
	    //std::cout << "Bonding cutoff for " << atom1->GetName() << " and " << relevant_atom->GetName() << " " << bonding_cutoff << std::endl;
            double x1 = atom1->GetCoordinate()->GetX(), y1 = atom1->GetCoordinate()->GetY(), z1 = atom1->GetCoordinate()->GetZ();
            double x2 = relevant_atom->GetCoordinate()->GetX(), y2 = relevant_atom->GetCoordinate()->GetY(), z2 = relevant_atom->GetCoordinate()->GetZ();
            double delta_x = std::abs(x1 - x2), delta_y = std::abs(y1 - y2), delta_z = std::abs(z1 - z2);
            //Do bond by distance
            if (delta_x < bonding_cutoff){
                if (delta_y < bonding_cutoff) {
                    if (delta_z < bonding_cutoff){
                        //double distance = std::pow(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z, 0.5);
			double distance = atom1->GetCoordinate()->Distance(relevant_atom->GetCoordinate());

			//I have no idea why the atoms exists between check is necessary here. It's causing problem that some atoms are supposed to be bonded aren't because this function returns true.
                        //if(distance < bonding_cutoff && !atom_exists_between(atom1, relevant_atom, relevant_atoms)){
                        if(distance < bonding_cutoff){
			    AtomVector atom1_neighbors = atom1->GetNode()->GetNodeNeighbors();
			    AtomVector relevant_atom_neighbors = relevant_atom->GetNode()->GetNodeNeighbors();

			    if (std::find(atom1_neighbors.begin(), atom1_neighbors.end(), relevant_atom) == atom1_neighbors.end()){
                                atom1->GetNode()->AddNodeNeighbor(relevant_atom);
			    }
			    if (std::find(relevant_atom_neighbors.begin(), relevant_atom_neighbors.end(), atom1) == relevant_atom_neighbors.end()){
                                relevant_atom->GetNode()->AddNodeNeighbor(atom1);
			    }
                        }
                    }
                }
            }
        }//Assign bonds
    }

}

bool donor_NorO(std::map<std::string, int>& AD_EL_TYPE_MAP, MolecularModeling::Atom* atom){
    std::string ad_type = atom->MolecularDynamicAtom::GetAtomType();
    return (AD_EL_TYPE_MAP[ad_type] == EL_MET) || (bonded_to_HD(atom));
}

int Get_xs_from_el (std::map<std::string, int>& AD_EL_TYPE_MAP, MolecularModeling::Atom* atom){
    std::string ad_type = atom->MolecularDynamicAtom::GetAtomType();
    int el_type = (AD_EL_TYPE_MAP.find(ad_type) != AD_EL_TYPE_MAP.end()) ? AD_EL_TYPE_MAP[ad_type] : EL_SIZE;

    if (el_type == EL_C){
        //return bonded_to_heteroatom(atom) ? "XS_C_P" : (atom->MolecularDynamicAtom::GetAtomType() == "A" ? "XS_C_A" : "XS_C_H");
        return atom->MolecularDynamicAtom::GetAtomType() == "A" ? (bonded_to_heteroatom(atom) ? XS_C_A_P : XS_C_A_H) : (bonded_to_heteroatom(atom) ? XS_C_P : XS_C_H);
    }
    else if (el_type == EL_N){
	std::string resname = atom->GetResidue()->GetName();
	std::string atomname = atom->GetName(); 
	if (resname == "ARG" && (atomname == "NE" || atomname == "NH1" || atomname == "NH2") ){
	    return XS_N_R;
	}

        return (is_acceptor(ad_type) && donor_NorO(AD_EL_TYPE_MAP, atom)) ? XS_N_DA : (is_acceptor(ad_type) ? XS_N_A : (donor_NorO(AD_EL_TYPE_MAP, atom)? XS_N_D : XS_N_P));
    }
    else if (el_type == EL_O){
        return (is_acceptor(ad_type) && donor_NorO(AD_EL_TYPE_MAP, atom)) ? XS_O_DA : (is_acceptor(ad_type) ? XS_O_A : (donor_NorO(AD_EL_TYPE_MAP, atom)? XS_O_D : XS_O_P));
    }
    else if (el_type == EL_S)    return XS_S_P;
    else if (el_type == EL_P)    return XS_P_P;
    else if (el_type == EL_F)    return XS_F_H;
    else if (el_type == EL_Cl)   return XS_Cl_H;
    else if (el_type == EL_Br)   return XS_Br_H;
    else if (el_type == EL_I)    return XS_I_H;
    else if (el_type == EL_MET)  return XS_Met_D;
    else if (el_type == EL_NR)   return XS_N_R;
    else if (el_type == EL_H)    return XS_H;
    return XS_SIZE;
}

void ObtainAtomXsType(AtomVector& atoms, std::map<MolecularModeling::Atom*, int>& atom_xs_type_map){
    for (unsigned int i = 0; i < atoms.size(); i++){
        atom_xs_type_map[atoms[i]] = Get_xs_from_el(AD_EL_TYPE_MAP, atoms[i]);
    }
}

double CHpiConvertAngle2FirstQuadrant(double angle_in_rad){
    int k = (int) angle_in_rad / (2*M_PI);
    double angle_in_rad_converted = (angle_in_rad > 0) ? angle_in_rad - 2*k*M_PI : angle_in_rad - 2*(k-1)*M_PI; //Convert angle in any quadrant to their corresponding one in the 1st quadrant.

    if (angle_in_rad_converted >= 0 && angle_in_rad_converted < M_PI_2){ //If angle in 1st quadrant
        //angle_converted = angle_in_rad_converted;
	return angle_in_rad_converted;
    }
    else if (angle_in_rad_converted >= M_PI_2 && angle_in_rad_converted <= M_PI){
        //angle_converted = M_PI - angle_in_rad_converted;
	return (M_PI - angle_in_rad_converted);
    }
    else if (angle_in_rad_converted >= M_PI && angle_in_rad_converted <= 1.50 * M_PI ){
        //angle_converted = M_PI + angle_in_rad_converted;
	return -(angle_in_rad_converted - M_PI);
    }
    else if (angle_in_rad_converted >= 1.50 * M_PI && angle_in_rad_converted <= 2.00 * M_PI ){
        //angle_converted = -angle_in_rad_converted;
	return -(2*M_PI - angle_in_rad_converted);
    }

    std::cout << "CH-pi: cannot convert this angle value " << angle_in_rad_converted << std::endl;
    std::cout << "Returning NaN" << std::endl;
    return (angle_in_rad_converted / 0.00);

}
double EvaluateCHpi(MolecularModeling::Atom* aliphatic_carbon, AtomVector& pi_ring, int pi_ring_index, AtomVector& ligand_or_receptor_hydrogens, double& tot_gau1, double& tot_gau2, double& tot_rep, 
		    std::map<MolecularModeling::Atom*, int>& atom_xs_type_map, double* receptor_ring_centroids, double* receptor_ring_normals, 
		    std::map<MolecularModeling::Atom*, std::map<MolecularModeling::Atom*, std::vector<double> > >& receptor_CH_vectors,
		    bool ring_is_receptor = false,  int carbon_coord_index = 0, int pi_coord_index = 0){

    double tot_ch_pi = 0.000000;    
    GeometryTopology::Coordinate* carbon_coord = aliphatic_carbon->GetCoordinates()[carbon_coord_index];

    AtomVector carbon_neighbors = aliphatic_carbon->GetNode()->GetNodeNeighbors();
    AtomVector carbon_hydrogen_neighbors;
    for (unsigned int j = 0; j < carbon_neighbors.size(); j++){
        if (carbon_neighbors[j]->GetElementSymbol() == "H"){
            carbon_hydrogen_neighbors.push_back(carbon_neighbors[j]);
        }	
    }

    double centroid[3];
    if (ring_is_receptor){ //receptor_ring_centroids is an array of doubles, with the x,y,z value of the 1st, 2nd, 3rd etc receptor centroids;
        centroid[0] = receptor_ring_centroids[pi_ring_index * 3 ]; 
        centroid[1] = receptor_ring_centroids[pi_ring_index * 3 + 1]; 
        centroid[2] = receptor_ring_centroids[pi_ring_index * 3 + 2]; 
    }
    else{
        GetGeometricCenter(pi_ring, centroid, 0, pi_coord_index);
    }

    double c_centroid_distance = std::sqrt((carbon_coord->GetX() - centroid[0])*(carbon_coord->GetX() - centroid[0]) + 
                                           (carbon_coord->GetY() - centroid[1])*(carbon_coord->GetY() - centroid[1]) +
                                           (carbon_coord->GetZ() - centroid[2])*(carbon_coord->GetZ() - centroid[2]));
    if (c_centroid_distance >= 8){ //Use aliphatic-centroid distance of 8A as cutoff.
	return 0;
    }

    //If they are within cutoff, record this aliphatic-aromatic pair as reacting. Use later in H VDW calculations;
    //interacting_aliphatic_aromatic_indices[i].push_back(pi_ring_index);

    double normal[3];
    if (ring_is_receptor){
        normal[0] = receptor_ring_normals[pi_ring_index * 3 ]; 
        normal[1] = receptor_ring_normals[pi_ring_index * 3 + 1]; 
        normal[2] = receptor_ring_normals[pi_ring_index * 3 + 2]; 
    }
    else{
        GetPlaneNormal(pi_ring[0], pi_ring[1], pi_ring[2], normal, 0, pi_coord_index);
    }
    double normal_length = std::sqrt(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2]);

    double centroid_c_vector[3];
    centroid_c_vector[0] = carbon_coord->GetX() - centroid[0];
    centroid_c_vector[1] = carbon_coord->GetY() - centroid[1];
    centroid_c_vector[2] = carbon_coord->GetZ() - centroid[2];

    double c_centroid_normal_projection_length = std::abs(centroid_c_vector[0]*normal[0] + centroid_c_vector[1]*normal[1] + centroid_c_vector[2]*normal[2]) / normal_length; 

    double c_centroid_normal_cos_abs = c_centroid_normal_projection_length /  std::sqrt(centroid_c_vector[0]*centroid_c_vector[0] + centroid_c_vector[1]*centroid_c_vector[1] + centroid_c_vector[2]*centroid_c_vector[2]);
    //double horizontal_displacement_angular_dependency = c_centroid_normal_cos_abs * c_centroid_normal_cos_abs; //cos^2 angle as dependence. 
    double horizontal_displacement_angular_dependency = 1.000000; //cos^2 angle as dependence. 

    for (unsigned int i = 0; i < carbon_hydrogen_neighbors.size(); i++){
        MolecularModeling::Atom* hydrogen = carbon_hydrogen_neighbors[i];
        GeometryTopology::Coordinate* hydrogen_coord = hydrogen->GetCoordinates()[carbon_coord_index];
        //int hydrogen_index = std::distance(receptor_atoms.begin(), std::find(receptor_atoms.begin(), receptor_atoms.end(), hydrogen));
	//std::cout << "Aliphatic carbon " << aliphatic_carbon->GetResidue()->GetName() << "-" << aliphatic_carbon->GetName() << " and hydrogen " << hydrogen->GetName() << std::endl;
		
	double centroid_H_vector[3];
	centroid_H_vector[0] = hydrogen_coord->GetX() - centroid[0];
	centroid_H_vector[1] = hydrogen_coord->GetY() - centroid[1];
	centroid_H_vector[2] = hydrogen_coord->GetZ() - centroid[2];

	double h_centroid_normal_projection = (centroid_H_vector[0]*normal[0] + centroid_H_vector[1]*normal[1] + centroid_H_vector[2]*normal[2]) / normal_length;

	if (std::abs(h_centroid_normal_projection) < c_centroid_normal_projection_length){ //This means that the H points towards the ring, not away from. 

	    double H_aliphatic_C_vector[3];
	    if (ring_is_receptor){
	        H_aliphatic_C_vector[0] = carbon_coord->GetX() - hydrogen_coord->GetX(); 
	        H_aliphatic_C_vector[1] = carbon_coord->GetY() - hydrogen_coord->GetY(); 
	        H_aliphatic_C_vector[2] = carbon_coord->GetZ() - hydrogen_coord->GetZ(); 
	    }
	    else{
	        H_aliphatic_C_vector[0] = receptor_CH_vectors[aliphatic_carbon][hydrogen][0];
	        H_aliphatic_C_vector[1] = receptor_CH_vectors[aliphatic_carbon][hydrogen][1];
	        H_aliphatic_C_vector[2] = receptor_CH_vectors[aliphatic_carbon][hydrogen][2];
	        //H_aliphatic_C_vector[0] = receptor_CH_vectors[current_CH_vector_array_index];
	        //H_aliphatic_C_vector[1] = receptor_CH_vectors[current_CH_vector_array_index +1];
	        //H_aliphatic_C_vector[2] = receptor_CH_vectors[current_CH_vector_array_index +2];
	    }
	    double H_aliphatic_C_vector_length = std::sqrt(H_aliphatic_C_vector[0]*H_aliphatic_C_vector[0] + H_aliphatic_C_vector[1]*H_aliphatic_C_vector[1] + 
			                                   H_aliphatic_C_vector[2]*H_aliphatic_C_vector[2]);

	    double H_aliphatic_C_normal_cosine = (H_aliphatic_C_vector[0]*normal[0] + H_aliphatic_C_vector[1]*normal[1] + H_aliphatic_C_vector[2]*normal[2]) / 
	                                         (H_aliphatic_C_vector_length * normal_length);

	    //std::cout << "H aliphatic C xyz: " << H_aliphatic_C_vector[0] << " " <<  H_aliphatic_C_vector[1] << " " <<  H_aliphatic_C_vector[2] << " " << std::endl;
	    //std::cout << "H aliphatic C normal length: " << H_aliphatic_C_vector_length << " and cos " << H_aliphatic_C_normal_cosine << std::endl;

            //double angular_dependency = std::pow(std::abs(H_aliphatic_C_normal_cosine), 1.2);
	    //For H-repulsion only form
            double angular_dependency = std::pow(std::abs(H_aliphatic_C_normal_cosine), 1.3);
            double distance_only_chpi = 0.0;
            for (unsigned int k = 0; k < pi_ring.size(); k++){
                MolecularModeling::Atom* this_ring_atom = pi_ring[k];
                if (this_ring_atom->MolecularDynamicAtom::GetAtomType() == "A"){
                    double H_C_distance = hydrogen->GetCoordinates()[carbon_coord_index]->Distance(this_ring_atom->GetCoordinates()[pi_coord_index]);
                    //double chpi_miu = 4.02, chpi_sigma = 0.20, chpi_const = 0.11; //This reproduces Boltzmann
		    //For H VDW form
                    /*double chpi_miu = 3.20, chpi_sigma = 0.90, chpi_const = 0.12, skew_alpha = 0.00, skew_const = 2.39; //This reproduces QM, with a skewed gaussian distribution
                    double gaussian = chpi_const * std::pow(2.718, (-1) * (H_C_distance - chpi_miu) * (H_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) / 
			              std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
	            double gaussian_cdf = (1 + std::erf(skew_alpha * (H_C_distance - chpi_miu) / (chpi_sigma * std::sqrt(2)) )) /2;
	            double skew_gaussian = skew_const * 2 * gaussian * gaussian_cdf;
	            distance_only_chpi += skew_gaussian;*/

		    //For non-H-VDW form
                    /*double chpi_miu = 3.09, chpi_sigma = 0.25, chpi_const = 0.12; //This reproduces QM, for the non-H-VDW functional form, then comment out the H-VDW section below. 
                    double gaussian = chpi_const * std::pow(2.718, (-1) * (H_C_distance - chpi_miu) * (H_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) / 
			              std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
		    distance_only_chpi += gaussian;*/

		    //For H-repulsion 25% H VDW attraction form
                    double chpi_miu = 3.10, chpi_sigma = 0.75, chpi_const = 0.30; //This reproduces QM, for the H-VDW only functional form, then comment out the H-VDW Gauss 1 and 2 section below.
                    double gaussian = chpi_const * std::pow(2.718, (-1) * (H_C_distance - chpi_miu) * (H_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) /
                                      std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
                    distance_only_chpi += gaussian;
                }
            }
	    //std::cout << "Ang: " << angular_dependency << " Dist: " << distance_only_chpi << std::endl;
	    tot_ch_pi += (horizontal_displacement_angular_dependency * angular_dependency * distance_only_chpi);
	}
    }

    AtomVector aliphatic_atoms = carbon_hydrogen_neighbors;
    aliphatic_atoms.push_back(aliphatic_carbon);
    AtomVector ring_atom_and_hydrogens = pi_ring;

    /*for (unsigned int i = 0; i < pi_ring.size(); i++){
        AtomVector this_atom_neighbors = pi_ring[i]->GetNode()->GetNodeNeighbors();
	for (unsigned int j = 0; j < this_atom_neighbors.size(); j++){
	    if (this_atom_neighbors[j]->GetElementSymbol() == "H"){
	        ring_atom_and_hydrogens.push_back(this_atom_neighbors[j]); 
	    }
	}
    }*/

    //For CH-pi, other than the sigma-pi orbital overlap above, also include H-heavy VDW (gau1,gau2,repulsion) terms. But I'm not including these for H-H.
    for (unsigned int i = 0; i < aliphatic_atoms.size(); i++){
        MolecularModeling::Atom* this_aliphatic_atom = aliphatic_atoms[i];
	for (unsigned int j = 0; j < ring_atom_and_hydrogens.size(); j++){
            MolecularModeling::Atom* this_ring_atom = ring_atom_and_hydrogens[j];

	    //Skip heavy-heavy pairs
	    if (this_aliphatic_atom->GetElementSymbol() == "H" || this_ring_atom->GetElementSymbol() == "H"){
	        double distance = this_aliphatic_atom->GetCoordinates()[carbon_coord_index]->Distance(this_ring_atom->GetCoordinates()[pi_coord_index]);
		int aliphatic_atom_xs_type = atom_xs_type_map[this_aliphatic_atom];

		if (distance < cutoff){
	            int ring_atom_xs_type = atom_xs_type_map[this_ring_atom];
	            double r_optimal = distance - element_xs_vdw_radii[aliphatic_atom_xs_type] - element_xs_vdw_radii[ring_atom_xs_type];

	            double gau1_distance = r_optimal - gau1_ofs;
                    //tot_gau1 += std::exp(-std::pow(gau1_distance/gau1_wdh,2));
                    double gau2_distance = r_optimal - gau2_ofs;
                    //tot_gau2 += std::exp(-std::pow(gau2_distance/gau2_wdh,2));

		    //25% H VDW attraction?
                    tot_ch_pi += 0.50 * std::abs(wt_gau1 * std::exp(-std::pow(gau1_distance/gau1_wdh,2)));
                    tot_ch_pi += 0.50 * std::abs(wt_gau2 * std::exp(-std::pow(gau2_distance/gau2_wdh,2)));

                    double rep_distance = r_optimal - rep_ofs;
                    if (rep_distance < 0){
                        //tot_rep += rep_distance * rep_distance;
                        tot_ch_pi -= 0.50 * (wt_rep * rep_distance * rep_distance);
                    }
	        }
	    }
	}
    }

    //std::cout << "Total num pairs " << aliphatic_atoms.size() * ring_atom_and_hydrogens.size() << std::endl;
    return tot_ch_pi;
}

struct VinaScorePrerequisites{
    AtomVector ligand_atoms_;
    AtomVector receptor_atoms_;
    AtomVector ligand_atoms_valid_types_no_H_;
    AtomVector receptor_atoms_valid_types_no_H_;
    AtomVector receptor_aliphatic_carbon_atoms_;
    AtomVector ligand_aliphatic_carbon_atoms_;
    AtomVector ligand_hydrogens_;
    AtomVector receptor_hydrogens_;
    std::map<MolecularModeling::Atom*, int> atom_xs_type_map_;
    std::map<MolecularModeling::Atom*, AtomVector> heavy_atom_H_neighbor_map_;
    std::vector<AtomVector> receptor_aromatic_cycles_;
    std::vector<AtomVector> ligand_aromatic_cycles_;
    double* receptor_ring_centroids_ = NULL;
    double* receptor_ring_normals_ = NULL;
    std::map<MolecularModeling::Atom*, std::map<MolecularModeling::Atom*, std::vector<double> > > receptor_CH_vectors_;
    bool* ligand_receptor_score_bools_ = NULL; //1d bool array. Each ligand-protein non-H atom pair has 4 booleans, indicating whether gauss1_2_repulsion, hydrophobic, hbond, and catpi should be evaluated.

    void PrecomputeVinaScorePrerequisites(AtomVector& ligand_atoms, AtomVector& receptor_atoms, AtomVector& ligand_atoms_valid_types_no_H, AtomVector& receptor_atoms_valid_types_no_H, 
		                          AtomVector& ligand_hydrogens, AtomVector& receptor_hydrogens, AtomVector& receptor_aliphatic_carbon_atoms, AtomVector& ligand_aliphatic_carbon_atoms, 
					  std::map<MolecularModeling::Atom*, int>& atom_xs_type_map, std::vector<AtomVector>& receptor_aromatic_cycles,  std::vector<AtomVector>& ligand_aromatic_cycles,
					  double** receptor_ring_centroids, double** receptor_ring_normals, bool** ligand_receptor_score_bools, 
					  std::map<MolecularModeling::Atom*, std::map<MolecularModeling::Atom*, std::vector<double> > >& receptor_CH_vectors, 
					  std::map<MolecularModeling::Atom*, AtomVector>& heavy_atom_H_neighbor_map){

        ObtainAtomXsType(ligand_atoms, atom_xs_type_map);
        ObtainAtomXsType(receptor_atoms, atom_xs_type_map);

	ResidueVector ligand_residues;
	for (unsigned int i = 0; i < ligand_atoms.size(); i++){
            MolecularModeling::Residue* this_atom_residue = ligand_atoms[i]->GetResidue();
            if (std::find(ligand_residues.begin(), ligand_residues.end(), this_atom_residue) == ligand_residues.end()){
                ligand_residues.push_back(this_atom_residue);
            }
        }

	//Must use ligand atoms instead of residues, because the atoms being parsed in are actually atoms that are rotated by the last torsion. 
	//That being said, using residues will also include aromatic cycles outside of the rotated atoms. 
        //ligand_aromatic_cycles = DetectAromaticCycles(ligand_residues);
        ligand_aromatic_cycles = DetectAromaticCycles(ligand_atoms);

	for (unsigned int i = 0; i < ligand_atoms.size(); i++){
	    if (ligand_atoms[i]->MolecularDynamicAtom::GetAtomType() == "C"){
	        ligand_aliphatic_carbon_atoms.push_back(ligand_atoms[i]);
	    }   
	}

	for (unsigned int i = 0; i < ligand_atoms.size(); i++){
	    if (ligand_atoms[i]->GetElementSymbol() != "H"){
	        AtomVector this_atom_neighbors = ligand_atoms[i]->GetNode()->GetNodeNeighbors();
		for (unsigned int j = 0; j < this_atom_neighbors.size(); j++){
		    if (this_atom_neighbors[j]->GetElementSymbol() == "H"){
		        heavy_atom_H_neighbor_map[ligand_atoms[i]].push_back(this_atom_neighbors[j]);
		    }
		}
	    }
	}

	for (unsigned int i = 0; i < receptor_atoms.size(); i++){
            if (receptor_atoms[i]->GetElementSymbol() != "H"){
                AtomVector this_atom_neighbors = receptor_atoms[i]->GetNode()->GetNodeNeighbors();
                for (unsigned int j = 0; j < this_atom_neighbors.size(); j++){
                    if (this_atom_neighbors[j]->GetElementSymbol() == "H"){
                        heavy_atom_H_neighbor_map[receptor_atoms[i]].push_back(this_atom_neighbors[j]);
                    }
                }
            }
        }

        ResidueVector receptor_residues;
        for (unsigned int i = 0; i < receptor_atoms.size(); i++){
            MolecularModeling::Residue* this_atom_residue = receptor_atoms[i]->GetResidue();
            if (std::find(receptor_residues.begin(), receptor_residues.end(), this_atom_residue) == receptor_residues.end()){
                receptor_residues.push_back(this_atom_residue);
            }
        }
        receptor_aromatic_cycles = DetectAromaticCycles(receptor_residues);

        GetGeometricCenter(receptor_aromatic_cycles, receptor_ring_centroids, 0);
        GetPlaneNormal(receptor_aromatic_cycles, receptor_ring_normals, 0);

        int num_CH_vectors = 0; 
	for (unsigned int i = 0; i < receptor_atoms.size(); i++){
            if (receptor_atoms[i]->MolecularDynamicAtom::GetAtomType() == "C"){
	        MolecularModeling::Atom* this_receptor_C = receptor_atoms[i];
	        receptor_aliphatic_carbon_atoms.push_back(this_receptor_C);
	        AtomVector C_neighbors = this_receptor_C->GetNode()->GetNodeNeighbors();

	        for (unsigned int j = 0; j < C_neighbors.size(); j++){
	            if (C_neighbors[j]->GetElementSymbol() == "H"){
	                num_CH_vectors++;
		    }
		}
	    }
	}

	//Allocate memory for 1d arrary of CH_vectors
           
	for (unsigned int i = 0; i < receptor_aliphatic_carbon_atoms.size(); i++){
            MolecularModeling::Atom* this_receptor_C = receptor_aliphatic_carbon_atoms[i];
            GeometryTopology::Coordinate* this_receptor_C_coord = this_receptor_C->GetCoordinate();
            AtomVector this_atom_neighbors = this_receptor_C->GetNode()->GetNodeNeighbors();

            for(unsigned int j = 0; j < this_atom_neighbors.size(); j++){
                if (this_atom_neighbors[j]->GetElementSymbol() == "H"){
                    MolecularModeling::Atom* this_neighbor_H = this_atom_neighbors[j];
                    GeometryTopology::Coordinate* this_neighbor_H_coord = this_neighbor_H->GetCoordinate();

	            //receptor_CH_vectors.push_back(this_receptor_C_coord->GetX() - this_neighbor_H_coord->GetX());
	            //receptor_CH_vectors.push_back(this_receptor_C_coord->GetY() - this_neighbor_H_coord->GetY());
	            //receptor_CH_vectors.push_back(this_receptor_C_coord->GetZ() - this_neighbor_H_coord->GetZ());
	            receptor_CH_vectors[this_receptor_C][this_neighbor_H].push_back(this_receptor_C_coord->GetX() - this_neighbor_H_coord->GetX());
		    receptor_CH_vectors[this_receptor_C][this_neighbor_H].push_back(this_receptor_C_coord->GetY() - this_neighbor_H_coord->GetY());
		    receptor_CH_vectors[this_receptor_C][this_neighbor_H].push_back(this_receptor_C_coord->GetZ() - this_neighbor_H_coord->GetZ());
                       
                }
            }

        }

	//std::exit(1);


	//Precompute whether each ligand-protein atom pair needs to be evaluated, based on atom type. 
	for (unsigned int i = 0; i < ligand_atoms.size(); i++){
	    int this_atom_xs_type = atom_xs_type_map[ligand_atoms[i]];
	    if (this_atom_xs_type != XS_H && this_atom_xs_type != XS_SIZE){
	        ligand_atoms_valid_types_no_H.push_back(ligand_atoms[i]);
	    }
	    else if (this_atom_xs_type == XS_H){
	        ligand_hydrogens.push_back(ligand_atoms[i]);
	    }
	}
	for (unsigned int i = 0; i < receptor_atoms.size(); i++){
	    int this_atom_xs_type = atom_xs_type_map[receptor_atoms[i]];
	    if (this_atom_xs_type != XS_H && this_atom_xs_type != XS_SIZE){
	        receptor_atoms_valid_types_no_H.push_back(receptor_atoms[i]);
	    }
	    else if (this_atom_xs_type == XS_H){
	        receptor_hydrogens.push_back(receptor_atoms[i]);
	    }
	}

	int bool_array_size = 3 * ligand_atoms_valid_types_no_H.size() * receptor_atoms_valid_types_no_H.size() * sizeof(bool);
	(*ligand_receptor_score_bools) = (bool*)std::malloc(bool_array_size);
	for (unsigned int i = 0; i < bool_array_size; i++){ //Initialize all booleans in array to false;
	    (*ligand_receptor_score_bools)[i] = false; 
	}

        int current_index = 0;

	for (int i = 0; i < ligand_atoms_valid_types_no_H.size(); i++){
	    MolecularModeling::Atom* this_ligand_atom = ligand_atoms_valid_types_no_H[i];
	    int lig_xs_type = atom_xs_type_map[this_ligand_atom];

	    for (int j = 0; j < receptor_atoms_valid_types_no_H.size(); j++){
	        MolecularModeling::Atom* this_receptor_atom = receptor_atoms_valid_types_no_H[j];
		int rec_xs_type = atom_xs_type_map[this_receptor_atom];

	        if (std::find(hydrophobic_elements.begin(), hydrophobic_elements.end(), lig_xs_type) != hydrophobic_elements.end() &&
                    std::find(hydrophobic_elements.begin(), hydrophobic_elements.end(), rec_xs_type) != hydrophobic_elements.end()){ //Should evaluate phobic
                    (*ligand_receptor_score_bools)[current_index] = true;
	        }

	        if (std::find(hb_donor_types.begin(), hb_donor_types.end(), lig_xs_type) != hb_donor_types.end() &&
                    std::find(hb_acceptor_types.begin(), hb_acceptor_types.end(), rec_xs_type) != hb_acceptor_types.end()){ //Should evalute hbond
	            (*ligand_receptor_score_bools)[current_index+1] = true;
	        }
	        else if (std::find(hb_donor_types.begin(), hb_donor_types.end(), rec_xs_type) != hb_donor_types.end() &&
                        std::find(hb_acceptor_types.begin(), hb_acceptor_types.end(), lig_xs_type) != hb_acceptor_types.end()){ //Should evalute hbond
                    (*ligand_receptor_score_bools)[current_index+1] = true;
	        }

	        if ( (rec_xs_type == XS_N_R && (lig_xs_type == XS_C_A_H || lig_xs_type == XS_C_A_P)) ||
                    (lig_xs_type == XS_N_R && (rec_xs_type == XS_C_A_H || rec_xs_type == XS_C_A_P)) ){ //Should evaluate catpi
                    (*ligand_receptor_score_bools)[current_index+2] = true;
		}
	        current_index +=3;
	    }
	}

        return;
    }

    VinaScorePrerequisites(AtomVector& ligand_atoms, AtomVector& receptor_atoms){
        this->ligand_atoms_ = ligand_atoms;
        this->receptor_atoms_ = receptor_atoms;
        PrecomputeVinaScorePrerequisites(this->ligand_atoms_, this->receptor_atoms_, this->ligand_atoms_valid_types_no_H_, this->receptor_atoms_valid_types_no_H_, this->ligand_hydrogens_, 
			                 this->receptor_hydrogens_, this->receptor_aliphatic_carbon_atoms_, this->ligand_aliphatic_carbon_atoms_, this->atom_xs_type_map_, this->receptor_aromatic_cycles_,
					 this->ligand_aromatic_cycles_, &this->receptor_ring_centroids_, &this->receptor_ring_normals_, &this->ligand_receptor_score_bools_, this->receptor_CH_vectors_, 
					 this->heavy_atom_H_neighbor_map_);

	//std::exit(1);
    }

    ~VinaScorePrerequisites(){
	    std::free(this->receptor_ring_centroids_);
	    std::free(this->receptor_ring_normals_);
	    std::free(this->ligand_receptor_score_bools_);
    }



};

std::vector<double> VinaScoreInPlace(VinaScorePrerequisites& prerequisites, int coord_index = 0){
    //Return a vector of score, in the order of: total, gau1, gau2, repulsion, phobic, hbond.

    AtomVector& ligand_atoms = prerequisites.ligand_atoms_;
    AtomVector& receptor_atoms = prerequisites.receptor_atoms_;
    AtomVector& ligand_atoms_valid_types_no_H = prerequisites.ligand_atoms_valid_types_no_H_;
    AtomVector& receptor_atoms_valid_types_no_H = prerequisites.receptor_atoms_valid_types_no_H_;
    AtomVector& ligand_hydrogens = prerequisites.ligand_hydrogens_;
    AtomVector& receptor_hydrogens = prerequisites.receptor_hydrogens_;
    AtomVector& receptor_aliphatic_carbon_atoms = prerequisites.receptor_aliphatic_carbon_atoms_;
    AtomVector& ligand_aliphatic_carbon_atoms = prerequisites.ligand_aliphatic_carbon_atoms_;
    std::map<MolecularModeling::Atom*, int>& atom_xs_type_map = prerequisites.atom_xs_type_map_;
    std::vector<AtomVector>& ligand_aromatic_rings = prerequisites.ligand_aromatic_cycles_;
    std::vector<AtomVector>& receptor_aromatic_rings = prerequisites.receptor_aromatic_cycles_;
    double* receptor_ring_centroids = prerequisites.receptor_ring_centroids_;
    double* receptor_ring_normals = prerequisites.receptor_ring_normals_;
    bool* ligand_receptor_score_bools = prerequisites.ligand_receptor_score_bools_;

    std::map<MolecularModeling::Atom*, std::map<MolecularModeling::Atom*, std::vector<double> > >& receptor_CH_vectors = prerequisites.receptor_CH_vectors_;
    std::map<MolecularModeling::Atom*, AtomVector>& heavy_atom_H_neighbor_map = prerequisites.heavy_atom_H_neighbor_map_;

    double tot_gau1 = 0, tot_gau2 = 0, tot_rep = 0, tot_pho = 0, tot_hb = 0, tot_catpi = 0, tot_pi_pi = 0, tot_ch_pi = 0;

    int current_index = 0;
    int num_times_entered = 0;
    for (unsigned int lig_index = 0; lig_index < ligand_atoms_valid_types_no_H.size(); lig_index++){
        MolecularModeling::Atom* lig_atm = ligand_atoms_valid_types_no_H[lig_index];
	int lig_xs_type = atom_xs_type_map[lig_atm];
	AtomVector& lig_atm_H_neighbors = heavy_atom_H_neighbor_map[lig_atm];

        for (unsigned int rec_index = 0; rec_index < receptor_atoms_valid_types_no_H.size(); rec_index++){
            MolecularModeling::Atom* rec_atm = receptor_atoms_valid_types_no_H[rec_index];
	    int rec_xs_type = atom_xs_type_map[rec_atm];

            double distance = 0.000;
	    bool distance_within_cutoff = DistanceWithinCutoff(lig_atm, rec_atm, distance, cutoff, coord_index, 0);
	    if (distance_within_cutoff){
                double lig_atm_xs_radius = 0, rec_atm_xs_radius = 0;
                if (element_xs_vdw_radii.find(lig_xs_type) != element_xs_vdw_radii.end() && element_xs_vdw_radii.find(rec_xs_type) != element_xs_vdw_radii.end()){
                    lig_atm_xs_radius = element_xs_vdw_radii[lig_xs_type];
                    rec_atm_xs_radius = element_xs_vdw_radii[rec_xs_type];
                }
                else {
                    std::cout << "Some atom XS radius value doesn't exist" << std::endl;
                    std::cout << "Ligand atom name: " << lig_atm->GetName() << std::endl;
                    std::cout << "Receptor atom name: " << rec_atm->GetName() << std::endl;
                    std::cout << "Ligand ad type: " << lig_atm->MolecularDynamicAtom::GetAtomType() << std::endl;
                    std::cout << "Ligand xs type: " << lig_xs_type << " receptor xs type: " << rec_xs_type << std::endl;
                    std::exit(1);
                }
                double r_optimal = distance - lig_atm_xs_radius - rec_atm_xs_radius;

                double gau1_distance = r_optimal - gau1_ofs;
                tot_gau1 += std::exp(-std::pow(gau1_distance/gau1_wdh,2));
                double gau2_distance = r_optimal - gau2_ofs;
                tot_gau2 += std::exp(-std::pow(gau2_distance/gau2_wdh,2));
                double rep_distance = r_optimal - rep_ofs;
                if (rep_distance < 0){
                    tot_rep += rep_distance * rep_distance;
                    //std::cout << "Rep between " << lig_atm->GetName() << " and " << rec_atm->GetResidue()->GetName() << "-" << rec_atm->GetName()  << "is: " << (double)(rep_distance * rep_distance) << std::endl;
                }

	        if (ligand_receptor_score_bools[current_index]){ //Hydrophobic should be evaluated
                    tot_pho += slope_step(pho_bad, pho_good, r_optimal);
                }

	        if (ligand_receptor_score_bools[current_index+1]){ //Hbond should be evaluated
                    tot_hb += slope_step(hb_bad, hb_good, r_optimal);
                }
	        if (ligand_receptor_score_bools[current_index+2]){ //Catpi should be evaluated
                    tot_catpi += catpi_const * std::pow(2.718, (-1) * (distance - miu) * (distance - miu) / (2* sigma * sigma)) / std::pow(2* 3.1415* sigma * sigma, 0.5);
                }
	    }

	    //HH repulsion if heavy atom distance within cutoff  
            //double cutoff = 8, heavy_heavy_cutoff_for_H_repulsion = 6; HH_repulsion_cutoff = 2.5;
	    /*if (distance_within_cutoff && distance < heavy_heavy_cutoff_for_HH_repulsion){
	        AtomVector& rec_atm_H_neighbors = heavy_atom_H_neighbor_map[rec_atm];

		for (unsigned int lig_H_index = 0; lig_H_index < lig_atm_H_neighbors.size(); lig_H_index++){
		    MolecularModeling::Atom* lig_H = lig_atm_H_neighbors[lig_H_index];
		    int lig_H_xs_type = atom_xs_type_map[lig_H]; 
		    int lig_H_xs_vdw_radius = element_xs_vdw_radii[lig_H_xs_type];

		    for (unsigned int rec_H_index = 0; rec_H_index < rec_atm_H_neighbors.size(); rec_H_index++){
		        MolecularModeling::Atom* rec_H = rec_atm_H_neighbors[rec_H_index];

			double HH_distance = 0.000;
			if (DistanceWithinCutoff(lig_H, rec_H, HH_distance, HH_repulsion_cutoff, coord_index, 0)){
		            int rec_H_xs_type = atom_xs_type_map[rec_H]; 
		            int rec_H_xs_vdw_radius = element_xs_vdw_radii[rec_H_xs_type];

			    double HH_rep_distance = HH_distance - lig_H_xs_vdw_radius - rec_H_xs_vdw_radius - rep_ofs;
			    if (HH_rep_distance < 0){
				if (HH_rep_distance > -1){ //between 0 and -1, return repulsion distance raised to poewr 1.5, which is greater than quadratic. 
				    //tot_rep -= chpi_weight * 1.55 * std::pow(-HH_rep_distance, 0.333);
				    tot_rep -= wt_ch_pi * 1.55 * std::sqrt(-HH_rep_distance);
				    //tot_rep += chpi_weight * HH_rep_distance;
				}
				else{
			            tot_rep -= wt_ch_pi * 1.55 * HH_rep_distance * HH_rep_distance;
				}
			    }
			}
		    }
		}
	    }*/

	    current_index += 3;
	}
    }

    for (unsigned int i = 0; i < receptor_aliphatic_carbon_atoms.size(); i++){
        for (unsigned int j = 0; j < ligand_aromatic_rings.size(); j++){
            double chpi_1 = EvaluateCHpi(receptor_aliphatic_carbon_atoms[i], ligand_aromatic_rings[j], j, ligand_hydrogens, tot_gau1, tot_gau2, tot_rep, atom_xs_type_map, receptor_ring_centroids, 
			                 receptor_ring_normals, receptor_CH_vectors, false, 0, coord_index);
            tot_ch_pi += chpi_1;
        }
    }

    for (unsigned int i = 0; i < ligand_aliphatic_carbon_atoms.size(); i++){
        for (unsigned int j = 0;  j < receptor_aromatic_rings.size(); j++){
            double chpi_2 = EvaluateCHpi(ligand_aliphatic_carbon_atoms[i], receptor_aromatic_rings[j], j, receptor_hydrogens, tot_gau1, tot_gau2, tot_rep, atom_xs_type_map, receptor_ring_centroids, 
			                 receptor_ring_normals, receptor_CH_vectors, true, coord_index, 0);
            tot_ch_pi += chpi_2;
	}
    }

    //std::cout << "This ligand ring size: " << ligand_aromatic_rings.size() << std::endl;
    //std::cout << "This receptor ring size: " << receptor_aromatic_rings.size() << std::endl;

    //The below comments are the CHpi functon version based only on heavy atoms, and fitted to Boltzmann. 
    /*for (unsigned int i = 0; i < ligand_aromatic_rings.size(); i++){
        AtomVector& this_ring = ligand_aromatic_rings[i];
	double centroid[3];
	double normal[3];
        GetGeometricCenter(this_ring, centroid, 0, coord_index);
        GetPlaneNormal(this_ring[0], this_ring[1], this_ring[2], normal, 0, coord_index);

        for (unsigned int j = 0; j < receptor_atoms.size(); j++){
            MolecularModeling::Atom* this_rec_atom = receptor_atoms[j];
            std::string this_atm_ad_type = this_rec_atom->MolecularDynamicAtom::GetAtomType();
            if (this_atm_ad_type == "C"){
                //GeometryTopology::Coordinate C_centroid = GeometryTopology::Coordinate(this_rec_atom->GetCoordinates()[coord_index]->GetX() - centroid.GetX(),
                //this_rec_atom->GetCoordinates()[coord_index]->GetY() - centroid.GetY(), this_rec_atom->GetCoordinates()[coord_index]->GetZ() - centroid.GetZ());

                GeometryTopology::Coordinate C_centroid = GeometryTopology::Coordinate(this_rec_atom->GetCoordinates()[0]->GetX() - centroid[0],
                this_rec_atom->GetCoordinates()[0]->GetY() - centroid[1], this_rec_atom->GetCoordinates()[0]->GetZ() - centroid[2]);

                //double angle_in_rad = std::acos(C_centroid.DotProduct(normal) / (normal.length() * C_centroid.length()) ); //Angle in radian

                double angle_in_rad = std::acos((C_centroid.GetX()*normal[0] + C_centroid.GetY()*normal[1] + C_centroid.GetZ()*normal[2]) / 
				                (std::sqrt(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2]) * C_centroid.length()) ); //Angle in radian


                double angle_converted = CHpiConvertAngle2FirstQuadrant(angle_in_rad); //Convert angle in any quadrant to their corresponding one in the 1st quadrant.
                if (std::isnan(angle_converted)){  //If cannot convert angle, skip.
                    continue;
                }
                double angular_dependency = std::pow(std::cos(chpi_freq * angle_converted + chpi_phase), chpi_cos_pow);

		//std::cout << "Angular: " << angular_dependency << std::endl;
                //std::cout << angle_in_rad /3.14 * 180 << " " << angle_converted /3.14 * 180 << " " << angular_dependency << std::endl;

                double distance_only_chpi = 0.00;
                for (unsigned int k = 0; k < this_ring.size(); k++){
                    MolecularModeling::Atom* this_ring_atom = this_ring[k];
                    if (this_ring_atom->MolecularDynamicAtom::GetAtomType() == "A"){
                        double C_C_distance = this_rec_atom->GetCoordinates()[0]->Distance(this_ring_atom->GetCoordinates()[coord_index]);
                        //double chpi_miu = 4.02, chpi_sigma = 0.20, chpi_const = 0.11; //This reproduces Boltzmann
                        double chpi_miu = 3.82, chpi_sigma = 0.40, chpi_const = 0.14; //This reproduces Boltzmann
                        distance_only_chpi += chpi_const * std::pow(2.718, (-1) * (C_C_distance - chpi_miu) * (C_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) / std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
                    }
                }

                tot_ch_pi += (angular_dependency * distance_only_chpi);
            }
        }
    }

    for (unsigned int i = 0; i < receptor_aromatic_rings.size(); i++){
        AtomVector this_ring = receptor_aromatic_rings[i];
        double centroid [3];
	double normal [3];
        //GetGeometricCenter(centroid, 0, coord_index);
        //GetPlaneNormal(this_ring[0], this_ring[1], this_ring[2], normal, 0, coord_index);
	centroid[0] = receptor_ring_centroids[3*i];
	centroid[1] = receptor_ring_centroids[3*i +1];
	centroid[2] = receptor_ring_centroids[3*i +2];

	normal[0] = receptor_ring_normals[3*i];
	normal[1] = receptor_ring_normals[3*i +1];
	normal[2] = receptor_ring_normals[3*i +2];
        
        for (unsigned int j = 0; j < ligand_atoms.size(); j++){
            MolecularModeling::Atom* this_lig_atom = ligand_atoms[j];
            std::string this_atm_ad_type = this_lig_atom->MolecularDynamicAtom::GetAtomType();

            if (this_atm_ad_type == "C"){
                GeometryTopology::Coordinate C_centroid = GeometryTopology::Coordinate(this_lig_atom->GetCoordinates()[coord_index]->GetX() - centroid[0],
                this_lig_atom->GetCoordinates()[coord_index]->GetY() - centroid[1], this_lig_atom->GetCoordinates()[coord_index]->GetZ() - centroid[2]);

                //double angle_in_rad = std::acos(C_centroid.DotProduct(normal) / (normal.length() * C_centroid.length()) ); //Angle in radian
                double angle_in_rad = std::acos((C_centroid.GetX()*normal[0] + C_centroid.GetY()*normal[1] + C_centroid.GetZ()*normal[2]) / 
				                (std::sqrt(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2]) * C_centroid.length()) ); //Angle in radian

                double angle_converted = CHpiConvertAngle2FirstQuadrant(angle_in_rad); //Convert angle in any quadrant to their corresponding one in the 1st quadrant.
                if (std::isnan(angle_converted)){  //If cannot convert angle, skip.
                    continue;
                }
                double angular_dependency = std::pow(std::cos(chpi_freq * angle_converted + chpi_phase), chpi_cos_pow);

                double distance_only_chpi = 0.00;
                for (unsigned int k = 0; k < this_ring.size(); k++){
                    MolecularModeling::Atom* this_ring_atom = this_ring[k];
                    if (this_ring_atom->MolecularDynamicAtom::GetAtomType() == "A"){
                        double C_C_distance = this_lig_atom->GetCoordinates()[coord_index]->Distance(this_ring_atom->GetCoordinates()[0]);
                        //double chpi_miu = 4.02, chpi_sigma = 0.20, chpi_const = 0.11; //This reproduces Boltzmann
                        double chpi_miu = 3.82, chpi_sigma = 0.40, chpi_const = 0.14; //This reproduces Boltzmann
                        distance_only_chpi += chpi_const * std::pow(2.718, (-1) * (C_C_distance - chpi_miu) * (C_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) / std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
                    }
                }

                tot_ch_pi += (angular_dependency * distance_only_chpi);
            }
        }
    }*/

    //Return a vector of score, in the order of: total, gau1, gau2, repulsion, phobic, hbond.
    std::vector<double> scores;
    scores.push_back(wt_gau1 * tot_gau1 + wt_gau2 * tot_gau2 + wt_rep * tot_rep + wt_pho * tot_pho + wt_hb * tot_hb + wt_catpi * tot_catpi + wt_pi_pi * tot_pi_pi + wt_ch_pi * tot_ch_pi); //Total
    scores.push_back(wt_gau1 * tot_gau1); //Gauss 1
    scores.push_back(wt_gau2 * tot_gau2); //Gauss 2
    scores.push_back(wt_rep * tot_rep); //Repulsion
    scores.push_back(wt_pho * tot_pho); //Hydrophobic
    scores.push_back(wt_hb * tot_hb); //Hbond
    scores.push_back(wt_catpi * tot_catpi); //Catpi
    scores.push_back(wt_pi_pi * tot_pi_pi); //Pi pi
    scores.push_back(wt_ch_pi * tot_ch_pi); //CH pi

    //std::cout << "Total catpi term: " << wt_catpi * tot_catpi << std::endl;
    //std::cout << scores[0] <<  " " << scores[1] <<  " " << scores[2] <<  " " << scores[3] <<  " " << scores[4] <<  " " << scores[5] <<  " " << scores[6] <<  " " << scores[7] <<  " " << scores[8] <<  std::endl;
    return scores;
}

std::vector<double> VinaScoreInPlaceGS(VinaScorePrerequisites& prerequisites, double chpi_weight = wt_ch_pi, int coord_index = 0){
    //Return a vector of score, in the order of: total, gau1, gau2, repulsion, phobic, hbond.
    //std::cout << "CHpi weight: " << chpi_weight << std::endl;

    AtomVector& ligand_atoms = prerequisites.ligand_atoms_;
    AtomVector& receptor_atoms = prerequisites.receptor_atoms_;
    AtomVector& ligand_atoms_valid_types_no_H = prerequisites.ligand_atoms_valid_types_no_H_;
    AtomVector& receptor_atoms_valid_types_no_H = prerequisites.receptor_atoms_valid_types_no_H_;
    AtomVector& ligand_hydrogens = prerequisites.ligand_hydrogens_;
    AtomVector& receptor_hydrogens = prerequisites.receptor_hydrogens_;
    AtomVector& receptor_aliphatic_carbon_atoms = prerequisites.receptor_aliphatic_carbon_atoms_;
    AtomVector& ligand_aliphatic_carbon_atoms = prerequisites.ligand_aliphatic_carbon_atoms_;
    std::map<MolecularModeling::Atom*, int>& atom_xs_type_map = prerequisites.atom_xs_type_map_;
    std::vector<AtomVector>& ligand_aromatic_rings = prerequisites.ligand_aromatic_cycles_;
    std::vector<AtomVector>& receptor_aromatic_rings = prerequisites.receptor_aromatic_cycles_;
    double* receptor_ring_centroids = prerequisites.receptor_ring_centroids_;
    double* receptor_ring_normals = prerequisites.receptor_ring_normals_;
    bool* ligand_receptor_score_bools = prerequisites.ligand_receptor_score_bools_;

    std::map<MolecularModeling::Atom*, std::map<MolecularModeling::Atom*, std::vector<double> > >& receptor_CH_vectors = prerequisites.receptor_CH_vectors_;
    std::map<MolecularModeling::Atom*, AtomVector>& heavy_atom_H_neighbor_map = prerequisites.heavy_atom_H_neighbor_map_;

    double tot_gau1 = 0, tot_gau2 = 0, tot_rep = 0, tot_pho = 0, tot_hb = 0, tot_catpi = 0, tot_pi_pi = 0, tot_ch_pi = 0;

    int current_index = 0;
    int num_times_entered = 0;
    for (unsigned int lig_index = 0; lig_index < ligand_atoms_valid_types_no_H.size(); lig_index++){
        MolecularModeling::Atom* lig_atm = ligand_atoms_valid_types_no_H[lig_index];
	int lig_xs_type = atom_xs_type_map[lig_atm];
	AtomVector& lig_atm_H_neighbors = heavy_atom_H_neighbor_map[lig_atm];

        for (unsigned int rec_index = 0; rec_index < receptor_atoms_valid_types_no_H.size(); rec_index++){
            MolecularModeling::Atom* rec_atm = receptor_atoms_valid_types_no_H[rec_index];
	    int rec_xs_type = atom_xs_type_map[rec_atm];

            double distance = 0.000;
	    bool distance_within_cutoff = DistanceWithinCutoff(lig_atm, rec_atm, distance, cutoff, coord_index, coord_index);
	    if (distance_within_cutoff){
                double lig_atm_xs_radius = 0, rec_atm_xs_radius = 0;
                if (element_xs_vdw_radii.find(lig_xs_type) != element_xs_vdw_radii.end() && element_xs_vdw_radii.find(rec_xs_type) != element_xs_vdw_radii.end()){
                    lig_atm_xs_radius = element_xs_vdw_radii[lig_xs_type];
                    rec_atm_xs_radius = element_xs_vdw_radii[rec_xs_type];
                }
                else {
                    std::cout << "Some atom XS radius value doesn't exist" << std::endl;
                    std::cout << "Ligand atom name: " << lig_atm->GetName() << std::endl;
                    std::cout << "Receptor atom name: " << rec_atm->GetName() << std::endl;
                    std::cout << "Ligand ad type: " << lig_atm->MolecularDynamicAtom::GetAtomType() << std::endl;
                    std::cout << "Ligand xs type: " << lig_xs_type << " receptor xs type: " << rec_xs_type << std::endl;
                    std::exit(1);
                }
                double r_optimal = distance - lig_atm_xs_radius - rec_atm_xs_radius;

                double gau1_distance = r_optimal - gau1_ofs;
                tot_gau1 += std::exp(-std::pow(gau1_distance/gau1_wdh,2));
                double gau2_distance = r_optimal - gau2_ofs;
                tot_gau2 += std::exp(-std::pow(gau2_distance/gau2_wdh,2));
                double rep_distance = r_optimal - rep_ofs;
                if (rep_distance < 0){
                    tot_rep += rep_distance * rep_distance;
                }

	        if (ligand_receptor_score_bools[current_index]){ //Hydrophobic should be evaluated
                    tot_pho += slope_step(pho_bad, pho_good, r_optimal);
                }

	        if (ligand_receptor_score_bools[current_index+1]){ //Hbond should be evaluated
                    tot_hb += slope_step(hb_bad, hb_good, r_optimal);
                }
	        if (ligand_receptor_score_bools[current_index+2]){ //Catpi should be evaluated
                    tot_catpi += catpi_const * std::pow(2.718, (-1) * (distance - miu) * (distance - miu) / (2* sigma * sigma)) / std::pow(2* 3.1415* sigma * sigma, 0.5);
                }
	    }

	    //HH repulsion if heavy atom distance within cutoff  
            //double cutoff = 8, heavy_heavy_cutoff_for_H_repulsion = 6; HH_repulsion_cutoff = 2.5;
	    if (distance_within_cutoff && distance < heavy_heavy_cutoff_for_HH_repulsion){
	        AtomVector& rec_atm_H_neighbors = heavy_atom_H_neighbor_map[rec_atm];

		for (unsigned int lig_H_index = 0; lig_H_index < lig_atm_H_neighbors.size(); lig_H_index++){
		    MolecularModeling::Atom* lig_H = lig_atm_H_neighbors[lig_H_index];
		    int lig_H_xs_type = atom_xs_type_map[lig_H]; 
		    int lig_H_xs_vdw_radius = element_xs_vdw_radii[lig_H_xs_type];

		    for (unsigned int rec_H_index = 0; rec_H_index < rec_atm_H_neighbors.size(); rec_H_index++){
		        MolecularModeling::Atom* rec_H = rec_atm_H_neighbors[rec_H_index];

			double HH_distance = 0.000;
			if (DistanceWithinCutoff(lig_H, rec_H, HH_distance, HH_repulsion_cutoff, coord_index, coord_index)){
		            int rec_H_xs_type = atom_xs_type_map[rec_H]; 
		            int rec_H_xs_vdw_radius = element_xs_vdw_radii[rec_H_xs_type];

			    double HH_rep_distance = HH_distance - lig_H_xs_vdw_radius - rec_H_xs_vdw_radius - rep_ofs;
			    if (HH_rep_distance < 0){
				if (HH_rep_distance > -1){ //between 0 and -1, return repulsion distance raised to poewr 1.5, which is greater than quadratic. 
				    //tot_rep -= chpi_weight * 1.55 * std::pow(-HH_rep_distance, 0.333);
				    tot_rep -= chpi_weight * 1.55 * std::sqrt(-HH_rep_distance);
				    //tot_rep += chpi_weight * HH_rep_distance;
				}
				else{
			            tot_rep -= chpi_weight * 1.55 * HH_rep_distance * HH_rep_distance;
				}
			    }
			}
		    }
		}
	    }

	    current_index += 3;
	}
    }

    for (unsigned int i = 0; i < receptor_aliphatic_carbon_atoms.size(); i++){
        for (unsigned int j = 0; j < ligand_aromatic_rings.size(); j++){
            double chpi_1 = EvaluateCHpi(receptor_aliphatic_carbon_atoms[i], ligand_aromatic_rings[j], j, ligand_hydrogens, tot_gau1, tot_gau2, tot_rep, atom_xs_type_map, receptor_ring_centroids, 
			                 receptor_ring_normals, receptor_CH_vectors, false, 0, coord_index);
            tot_ch_pi += chpi_1;
        }
    }

    for (unsigned int i = 0; i < ligand_aliphatic_carbon_atoms.size(); i++){
        for (unsigned int j = 0;  j < receptor_aromatic_rings.size(); j++){
            double chpi_2 = EvaluateCHpi(ligand_aliphatic_carbon_atoms[i], receptor_aromatic_rings[j], j, receptor_hydrogens, tot_gau1, tot_gau2, tot_rep, atom_xs_type_map, receptor_ring_centroids, 
			                 receptor_ring_normals, receptor_CH_vectors, true, coord_index, 0);
            tot_ch_pi += chpi_2;
	}
    }

    //std::cout << "This ligand ring size: " << ligand_aromatic_rings.size() << std::endl;
    //std::cout << "This receptor ring size: " << receptor_aromatic_rings.size() << std::endl;

    //The below comments are the CHpi functon version based only on heavy atoms, and fitted to Boltzmann. 
    /*for (unsigned int i = 0; i < ligand_aromatic_rings.size(); i++){
        AtomVector& this_ring = ligand_aromatic_rings[i];
	double centroid[3];
	double normal[3];
        GetGeometricCenter(this_ring, centroid, 0, coord_index);
        GetPlaneNormal(this_ring[0], this_ring[1], this_ring[2], normal, 0, coord_index);

        for (unsigned int j = 0; j < receptor_atoms.size(); j++){
            MolecularModeling::Atom* this_rec_atom = receptor_atoms[j];
            std::string this_atm_ad_type = this_rec_atom->MolecularDynamicAtom::GetAtomType();
            if (this_atm_ad_type == "C"){
                //GeometryTopology::Coordinate C_centroid = GeometryTopology::Coordinate(this_rec_atom->GetCoordinates()[coord_index]->GetX() - centroid.GetX(),
                //this_rec_atom->GetCoordinates()[coord_index]->GetY() - centroid.GetY(), this_rec_atom->GetCoordinates()[coord_index]->GetZ() - centroid.GetZ());

                GeometryTopology::Coordinate C_centroid = GeometryTopology::Coordinate(this_rec_atom->GetCoordinates()[coord_index]->GetX() - centroid[0],
                this_rec_atom->GetCoordinates()[coord_index]->GetY() - centroid[1], this_rec_atom->GetCoordinates()[coord_index]->GetZ() - centroid[2]);

                //double angle_in_rad = std::acos(C_centroid.DotProduct(normal) / (normal.length() * C_centroid.length()) ); //Angle in radian

                double angle_in_rad = std::acos((C_centroid.GetX()*normal[0] + C_centroid.GetY()*normal[1] + C_centroid.GetZ()*normal[2]) / 
				                (std::sqrt(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2]) * C_centroid.length()) ); //Angle in radian


                double angle_converted = CHpiConvertAngle2FirstQuadrant(angle_in_rad); //Convert angle in any quadrant to their corresponding one in the 1st quadrant.
                if (std::isnan(angle_converted)){  //If cannot convert angle, skip.
                    continue;
                }
                double angular_dependency = std::pow(std::cos(chpi_freq * angle_converted + chpi_phase), chpi_cos_pow);

		//std::cout << "Angular: " << angular_dependency << std::endl;
                //std::cout << angle_in_rad /3.14 * 180 << " " << angle_converted /3.14 * 180 << " " << angular_dependency << std::endl;

                double distance_only_chpi = 0.00;
                for (unsigned int k = 0; k < this_ring.size(); k++){
                    MolecularModeling::Atom* this_ring_atom = this_ring[k];
                    if (this_ring_atom->MolecularDynamicAtom::GetAtomType() == "A"){
                        double C_C_distance = this_rec_atom->GetCoordinates()[coord_index]->Distance(this_ring_atom->GetCoordinates()[coord_index]);
                        //double chpi_miu = 4.02, chpi_sigma = 0.20, chpi_const = 0.11; //This reproduces Boltzmann
                        double chpi_miu = 3.82, chpi_sigma = 0.40, chpi_const = 0.14; //This reproduces Boltzmann
                        distance_only_chpi += chpi_const * std::pow(2.718, (-1) * (C_C_distance - chpi_miu) * (C_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) / std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
                    }
                }

                tot_ch_pi += (angular_dependency * distance_only_chpi);
            }
        }
    }

    for (unsigned int i = 0; i < receptor_aromatic_rings.size(); i++){
        AtomVector this_ring = receptor_aromatic_rings[i];
        double centroid [3];
	double normal [3];
        //GetGeometricCenter(centroid, 0, coord_index);
        //GetPlaneNormal(this_ring[0], this_ring[1], this_ring[2], normal, 0, coord_index);
	centroid[0] = receptor_ring_centroids[3*i];
	centroid[1] = receptor_ring_centroids[3*i +1];
	centroid[2] = receptor_ring_centroids[3*i +2];

	normal[0] = receptor_ring_normals[3*i];
	normal[1] = receptor_ring_normals[3*i +1];
	normal[2] = receptor_ring_normals[3*i +2];
        
        for (unsigned int j = 0; j < ligand_atoms.size(); j++){
            MolecularModeling::Atom* this_lig_atom = ligand_atoms[j];
            std::string this_atm_ad_type = this_lig_atom->MolecularDynamicAtom::GetAtomType();

            if (this_atm_ad_type == "C"){
                GeometryTopology::Coordinate C_centroid = GeometryTopology::Coordinate(this_lig_atom->GetCoordinates()[coord_index]->GetX() - centroid[0],
                this_lig_atom->GetCoordinates()[coord_index]->GetY() - centroid[1], this_lig_atom->GetCoordinates()[coord_index]->GetZ() - centroid[2]);

                //double angle_in_rad = std::acos(C_centroid.DotProduct(normal) / (normal.length() * C_centroid.length()) ); //Angle in radian
                double angle_in_rad = std::acos((C_centroid.GetX()*normal[0] + C_centroid.GetY()*normal[1] + C_centroid.GetZ()*normal[2]) / 
				                (std::sqrt(normal[0]*normal[0] + normal[1]*normal[1] + normal[2]*normal[2]) * C_centroid.length()) ); //Angle in radian

                double angle_converted = CHpiConvertAngle2FirstQuadrant(angle_in_rad); //Convert angle in any quadrant to their corresponding one in the 1st quadrant.
                if (std::isnan(angle_converted)){  //If cannot convert angle, skip.
                    continue;
                }
                double angular_dependency = std::pow(std::cos(chpi_freq * angle_converted + chpi_phase), chpi_cos_pow);

                double distance_only_chpi = 0.00;
                for (unsigned int k = 0; k < this_ring.size(); k++){
                    MolecularModeling::Atom* this_ring_atom = this_ring[k];
                    if (this_ring_atom->MolecularDynamicAtom::GetAtomType() == "A"){
                        double C_C_distance = this_lig_atom->GetCoordinates()[coord_index]->Distance(this_ring_atom->GetCoordinates()[coord_index]);
                        //double chpi_miu = 4.02, chpi_sigma = 0.20, chpi_const = 0.11; //This reproduces Boltzmann
                        double chpi_miu = 3.82, chpi_sigma = 0.40, chpi_const = 0.14; //This reproduces Boltzmann
                        distance_only_chpi += chpi_const * std::pow(2.718, (-1) * (C_C_distance - chpi_miu) * (C_C_distance - chpi_miu) / (2* chpi_sigma * chpi_sigma)) / std::pow(2* 3.1415* chpi_sigma * chpi_sigma, 0.5);
                    }
                }

                tot_ch_pi += (angular_dependency * distance_only_chpi);
            }
        }
    }*/

    //Return a vector of score, in the order of: total, gau1, gau2, repulsion, phobic, hbond.
    std::vector<double> scores;
    //scores.push_back(wt_gau1 * tot_gau1 + wt_gau2 * tot_gau2 + wt_rep * tot_rep + wt_pho * tot_pho + wt_hb * tot_hb + wt_catpi * tot_catpi + wt_pi_pi * tot_pi_pi + wt_ch_pi * tot_ch_pi); //Total
    scores.push_back(wt_gau1 * tot_gau1 + wt_gau2 * tot_gau2 + wt_rep * tot_rep + wt_pho * tot_pho + wt_hb * tot_hb + wt_catpi * tot_catpi + wt_pi_pi * tot_pi_pi + chpi_weight * tot_ch_pi); //Total
    scores.push_back(wt_gau1 * tot_gau1); //Gauss 1
    scores.push_back(wt_gau2 * tot_gau2); //Gauss 2
    scores.push_back(wt_rep * tot_rep); //Repulsion
    scores.push_back(wt_pho * tot_pho); //Hydrophobic
    scores.push_back(wt_hb * tot_hb); //Hbond
    scores.push_back(wt_catpi * tot_catpi); //Catpi
    scores.push_back(wt_pi_pi * tot_pi_pi); //Pi pi
    //scores.push_back(wt_ch_pi * tot_ch_pi); //CH pi
    scores.push_back(chpi_weight * tot_ch_pi); //CH pi

    //std::cout << "Total catpi term: " << wt_catpi * tot_catpi << std::endl;
    //std::cout << scores[0] <<  " " << scores[1] <<  " " << scores[2] <<  " " << scores[3] <<  " " << scores[4] <<  " " << scores[5] <<  " " << scores[6] <<  " " << scores[7] <<  " " << scores[8] <<  std::endl;
    return scores;
}

#endif // VINA_ATOM_DATA_HPP
