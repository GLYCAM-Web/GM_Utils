#ifndef UTILITY_HPP
#define UTILITY_HPP

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

#include <vector>
#include <cstdlib>

#include <glob.h> // glob(), globfree()
#include <string.h> // memset()
#include <stdexcept>
#include <string>
#include <sstream>
#include <filesystem>

typedef std::vector<MolecularModeling::Atom*> AtomVector;

void TraverseGraphAndReorderAtoms(MolecularModeling::Atom* atom, std::map<MolecularModeling::Residue*, AtomVector>& residue_reordered_atoms_map, AtomVector& visited_atoms, AtomVector& atoms_to_search){
    MolecularModeling::Residue* residue = atom->GetResidue();
    residue_reordered_atoms_map[residue].push_back(atom);
    visited_atoms.push_back(atom);

    AtomVector neighbors = atom->GetNode()->GetNodeNeighbors();
    std::multimap<double, MolecularModeling::Atom* > distance_neighbor_map;

    for (unsigned int i = 0; i < neighbors.size(); i++){
        MolecularModeling::Atom* neighbor = neighbors[i];
        double distance = atom->GetCoordinate()->Distance(neighbor->GetCoordinate());
        distance_neighbor_map.insert(std::pair<double, MolecularModeling::Atom*>(distance, neighbor));
    }

    for (std::map<double, MolecularModeling::Atom* >::iterator mapit = distance_neighbor_map.begin(); mapit != distance_neighbor_map.end(); mapit++){
        double distance = mapit->first;
        MolecularModeling::Atom* bonded_atom = mapit->second;

        if (std::find(visited_atoms.begin(), visited_atoms.end(), bonded_atom) == visited_atoms.end()){
            if (std::find(atoms_to_search.begin(), atoms_to_search.end(), bonded_atom) != atoms_to_search.end()){
                TraverseGraphAndReorderAtoms(bonded_atom, residue_reordered_atoms_map, visited_atoms, atoms_to_search);
            }
        }
    }
}

void ReorderAtomsForZMatrix(MolecularModeling::Assembly& assembly){
    ResidueVector residues = assembly.GetResidues();
    std::map<MolecularModeling::Residue*, AtomVector> residue_reordered_atoms_map;

    for (unsigned int i = 0; i < residues.size(); i++){
        MolecularModeling::Residue* residue = residues[i];
        AtomVector residue_atoms = residue->GetAtoms();
	std::cout << "Residue name: " << residue->GetName() << " Num residue atoms: " << residue_atoms.size() << std::endl;
        MolecularModeling::Atom* atom1 = residue_atoms[0];
        AtomVector visited_atoms;
        TraverseGraphAndReorderAtoms(atom1, residue_reordered_atoms_map, visited_atoms, residue_atoms);
    }

    for (unsigned int i = 0; i < residues.size(); i++){
        MolecularModeling::Residue* residue = residues[i];
        residue->SetAtoms(residue_reordered_atoms_map[residue]);
    }
}

bool InternalClashesExist(AtomVector& atom_set_1, AtomVector& atom_set_2, int coord_index){
    //Exhaustively compare two different atoms in assembly, using two nested for loops
    for (gmml::AtomVector::iterator it = atom_set_1.begin(); it != atom_set_1.end(); it++){
        MolecularModeling::Atom* current_atom = *it;
        AtomVector bond_by_distance_neighbors;

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
                                        bond_by_distance_neighbors.push_back(another_atom);
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
                /*for (unsigned int k = 0; k < bond_by_distance_neighbors.size(); k++){
                    MolecularModeling::Atom* bond_by_distance_atom = bond_by_distance_neighbors[k];

                    if (std::find(neighbors.begin(), neighbors.end(), bond_by_distance_atom) == neighbors.end()){
                        std::cout << "Atom with clash: " << current_atom->GetResidue()->GetName() << "-" << current_atom->GetName() << " has clash with "
                                  << bond_by_distance_atom->GetResidue()->GetName() << "-" << bond_by_distance_atom->GetName() << std::endl;
                        std::cout << "Distance: " << current_atom->GetCoordinates().at(coord_index)->Distance(bond_by_distance_atom->GetCoordinates().at(coord_index)) << std::endl;
                    }
                }*/
                return true;
            }
        }
    }

    return false;
}

bool DistanceWithinCutoff(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, double& distance, double cutoff, int coord_index1, int coord_index2){
    GeometryTopology::Coordinate* coord_1 = atom1->GetCoordinates()[coord_index1];
    GeometryTopology::Coordinate* coord_2 = atom2->GetCoordinates()[coord_index2];
    double delta_x = std::abs(coord_1->GetX() - coord_2->GetX());

    if (delta_x < cutoff){
        double delta_y = std::abs(coord_1->GetY() - coord_2->GetY());

        if (delta_y < cutoff){
            double delta_z = std::abs(coord_1->GetZ() - coord_2->GetZ());

            if (delta_z < cutoff){
                distance = std::pow(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z, 0.5);
		if (distance < cutoff){
		    return true;
		}
            }
        }
    }
    return false;
}

std::vector<std::string> glob(std::string& moiety_path, std::string& ext) {
    std::string full_glob_pattern = moiety_path;
    full_glob_pattern += "/*";
    full_glob_pattern += ext;
    // glob struct resides on the stack
    glob_t glob_result;
    memset(&glob_result, 0, sizeof(glob_result));

    // do the glob operation
    int return_value = glob(full_glob_pattern.c_str(), GLOB_TILDE, NULL, &glob_result);
    if(return_value != 0) {
        globfree(&glob_result);
	std::stringstream ss;
        if (return_value == 1){
            ss << "glob() failed with return value GLOB_NOSPACE" << std::endl;
        }
        if (return_value == 2){
            ss << "glob() failed with return value GLOB_ABORTED" << std::endl;
        }
        if (return_value == 3){
            ss << "glob() failed with return value GLOB_NOMATCH" << std::endl;
        }
        else{
            ss << "glob() failed with unknown return value" << return_value << std::endl;
        }
        throw std::runtime_error(ss.str());
    }

    // collect all the filenames into a std::list<std::string>
    std::vector<std::string> filenames;

    for(size_t i = 0; i < glob_result.gl_pathc; ++i) {
	std::string globbed_full_path = std::string(glob_result.gl_pathv[i]);
        int last_dash_index = globbed_full_path.find_last_of("/");
	std::string moiety_filename = globbed_full_path.erase(0, last_dash_index + 1 );
        filenames.push_back(moiety_filename);
    }

    // cleanup
    globfree(&glob_result);

    // done
    return filenames;
}

void GetGeometricCenter(AtomVector& atoms, double* ring_centroid_array, int starting_index, int coord_index = 0){
    ring_centroid_array[starting_index] = 0; 
    ring_centroid_array[starting_index + 1] = 0; 
    ring_centroid_array[starting_index + 2] = 0; 
    for (unsigned int j = 0; j < atoms.size(); j++){
        MolecularModeling::Atom* this_atom = atoms[j];
        ring_centroid_array[starting_index] += this_atom->GetCoordinates()[coord_index]->GetX();
        ring_centroid_array[starting_index + 1] += this_atom->GetCoordinates()[coord_index]->GetY();
        ring_centroid_array[starting_index + 2] += this_atom->GetCoordinates()[coord_index]->GetZ();
    }
    ring_centroid_array[starting_index] /= atoms.size();
    ring_centroid_array[starting_index + 1] /= atoms.size();
    ring_centroid_array[starting_index + 2] /= atoms.size();
}

void GetGeometricCenter(std::vector<AtomVector>& rings, double** ring_centroid_array, int coord_index = 0){

    (*ring_centroid_array) = (double*) malloc(rings.size() * 3 * sizeof(double));
    for (unsigned int i = 0; i < rings.size(); i++){
        AtomVector& this_ring = rings[i];
	GetGeometricCenter(this_ring, (*ring_centroid_array), 3*i, coord_index);
    }
}

void GetPlaneNormal(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, double* ring_normal_array, int starting_index, int coord_index = 0){

    GeometryTopology::Coordinate* a1_coord = atom1->GetCoordinates()[coord_index];
    GeometryTopology::Coordinate* a2_coord = atom2->GetCoordinates()[coord_index];
    GeometryTopology::Coordinate* a3_coord = atom3->GetCoordinates()[coord_index];
    double V1x = a2_coord->GetX() - a1_coord->GetX(), V1y = a2_coord->GetY() - a1_coord->GetY(), V1z = a2_coord->GetZ() - a1_coord->GetZ();
    double V2x = a3_coord->GetX() - a2_coord->GetX(), V2y = a3_coord->GetY() - a2_coord->GetY(), V2z = a3_coord->GetZ() - a2_coord->GetZ();
    ring_normal_array[starting_index] = V1y*V2z - V1z*V2y;
    ring_normal_array[starting_index+1] = V1z*V2x - V1x*V2z; 
    ring_normal_array[starting_index+2] = V1x*V2y - V1y*V2x;
}

void GetPlaneNormal(std::vector<AtomVector>& rings, double** ring_normal_array, int coord_index = 0){
    (*ring_normal_array) = (double*) malloc(rings.size() * 3 * sizeof(double));
    for (unsigned int i = 0; i < rings.size(); i++){
        AtomVector& this_ring = rings[i];
	GetPlaneNormal(this_ring[0], this_ring[1], this_ring[2], (*ring_normal_array), 3*i, coord_index);
    }
}

MolecularModeling::Atom* GetAtomByName(std::string atom_name, AtomVector atoms_to_search){
    int count = 0;
    MolecularModeling::Atom* atom = NULL;
    for (unsigned int i = 0; i < atoms_to_search.size(); i++){
        if (atoms_to_search[i]->GetName() == atom_name){
            atom = atoms_to_search[i];	
	        count++;
	    }
    }
    if (count == 1){
        return atom;
    }
    else if (count == 0){
        std::cout << "Cannot find atom with name " << atom_name << std::endl;
    }
    else if (count > 1){
        std::cout << "Multiple atoms with name " << atom_name << std::endl;
    }
    std::cout << "Problem with atom name " << atom_name << std::endl;
    std::exit(1);
    return NULL;
}

void DuplicateAtomNodesAndCoordinates(AtomVector& atoms, int& num_threads){
    if (num_threads > 1){
        for (unsigned int i = 0; i < atoms.size(); i++){
            MolecularModeling::AtomNode* first_node = atoms[i]->GetNode();
            AtomVector node_neighbors = first_node->GetNodeNeighbors();
            GeometryTopology::Coordinate* first_coord = atoms[i]->GetCoordinate();
            for (unsigned int j = 1; j < num_threads; j++){
                MolecularModeling::AtomNode* new_node = new MolecularModeling::AtomNode();
                new_node->SetNodeNeighbors(node_neighbors);
                atoms[i]->AddNode(new_node);
                new_node->SetAtom(atoms[i]);
                GeometryTopology::Coordinate* new_coord = new GeometryTopology::Coordinate(first_coord);
                atoms[i]->AddCoordinate(new_coord);
            }
        }
    }
}

double GetAngle(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, int coord_index)
{
    double current_angle = 0.0;
    GeometryTopology::Coordinate* a1 = atom1->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a2 = atom2->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a3 = atom3->GetCoordinates().at(coord_index);

    GeometryTopology::Coordinate* b1 = new GeometryTopology::Coordinate(*a1);
    b1->operator -(*a2);
    GeometryTopology::Coordinate* b2 = new GeometryTopology::Coordinate(*a3);
    b2->operator -(*a2);

    current_angle = acos((b1->DotProduct(*b2)) / (b1->length() * b2->length() + gmml::DIST_EPSILON));

    delete b1;
    delete b2;
    return current_angle;
}

void SetAngle(MolecularModeling::Atom* atom1, MolecularModeling::Atom* atom2, MolecularModeling::Atom* atom3, double angle, int coord_index)
{
    double current_angle = 0.0;
    GeometryTopology::Coordinate* a1 = atom1->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a2 = atom2->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a3 = atom3->GetCoordinates().at(coord_index);

    GeometryTopology::Coordinate* b1 = new GeometryTopology::Coordinate(*a1);
    b1->operator -(*a2);
    GeometryTopology::Coordinate* b2 = new GeometryTopology::Coordinate(*a3);
    b2->operator -(*a2);

    current_angle = acos((b1->DotProduct(*b2)) / (b1->length() * b2->length() + gmml::DIST_EPSILON));
    double rotation_angle = gmml::ConvertDegree2Radian(angle) - current_angle;

    GeometryTopology::Coordinate* direction = new GeometryTopology::Coordinate(*b1);
    direction->CrossProduct(*b2);
    direction->Normalize();
    double** rotation_matrix = gmml::GenerateRotationMatrix(direction, a2, rotation_angle);

    AtomVector atomsToRotate = AtomVector();
    atomsToRotate.push_back(atom2);
    atom3->FindConnectedAtoms(atomsToRotate, coord_index);

    for(AtomVector::iterator it = atomsToRotate.begin() + 1; it != atomsToRotate.end(); it++)
    {
        GeometryTopology::Coordinate* atom_coordinate = (*it)->GetCoordinates().at(coord_index);
        GeometryTopology::Coordinate* result = new GeometryTopology::Coordinate();
        result->SetX(rotation_matrix[0][0] * atom_coordinate->GetX() + rotation_matrix[0][1] * atom_coordinate->GetY() +
                rotation_matrix[0][2] * atom_coordinate->GetZ() + rotation_matrix[0][3]);
        result->SetY(rotation_matrix[1][0] * atom_coordinate->GetX() + rotation_matrix[1][1] * atom_coordinate->GetY() +
                rotation_matrix[1][2] * atom_coordinate->GetZ() + rotation_matrix[1][3]);
        result->SetZ(rotation_matrix[2][0] * atom_coordinate->GetX() + rotation_matrix[2][1] * atom_coordinate->GetY() +
                rotation_matrix[2][2] * atom_coordinate->GetZ() + rotation_matrix[2][3]);

        (*it)->GetCoordinates().at(coord_index)->SetX(result->GetX());
        (*it)->GetCoordinates().at(coord_index)->SetY(result->GetY());
        (*it)->GetCoordinates().at(coord_index)->SetZ(result->GetZ());

	delete result;
    }

    delete b1;
    delete b2;
    delete direction;
}

void GraftMoietyAndRemoveDummyAtoms(MolecularModeling::Atom* ligand_ring_atom, MolecularModeling::Atom* dummy_ring_atom, MolecularModeling::Atom* open_atom, MolecularModeling::Atom* dummy_open_valence_atom, MolecularModeling::Atom* moiety_head_atom, MolecularModeling::Assembly& moiety_assembly, int coord_index){
    /*This is done is two steps. First, compute translation vector by arg1-arg2.Perform translation to superpose arg2 to arg1. Second, set angle arg4-arg1/arg2-arg3 to zero degrees. This superimposes arg4      to arg3. The end result is arg2-arg4 being superimposed onto arg1-arg3
    */
    //Obtain translation vector
    GeometryTopology::Coordinate* ring_coord = ligand_ring_atom->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* fake_head_coord = dummy_ring_atom->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate translation_vector;
    translation_vector.SetX(ring_coord->GetX() - fake_head_coord->GetX());
    translation_vector.SetY(ring_coord->GetY() - fake_head_coord->GetY());
    translation_vector.SetZ(ring_coord->GetZ() - fake_head_coord->GetZ());

    //Translate all moiety_atoms by this tranlation vector.
    AtomVector moiety_atoms = moiety_assembly.GetAllAtomsOfAssembly();

    for (unsigned int i = 0; i < moiety_atoms.size(); i++){
        GeometryTopology::Coordinate* moiety_atom_coord = moiety_atoms[i]->GetCoordinates().at(coord_index);
        moiety_atom_coord->SetX(moiety_atom_coord->GetX() + translation_vector.GetX());
        moiety_atom_coord->SetY(moiety_atom_coord->GetY() + translation_vector.GetY());
        moiety_atom_coord->SetZ(moiety_atom_coord->GetZ() + translation_vector.GetZ());
    }

    //Set that angle to zero
    SetAngle(open_atom, dummy_ring_atom, dummy_open_valence_atom, 0, coord_index);

    //Add a bond
    AtomVector open_atom_neighbors = open_atom->GetNode(coord_index)->GetNodeNeighbors();
    if (std::find(open_atom_neighbors.begin(), open_atom_neighbors.end(), moiety_head_atom) == open_atom_neighbors.end()){
        open_atom->GetNodes().at(coord_index)->AddNodeNeighbor(moiety_head_atom);
    }
    AtomVector real_moiety_head_neighbors = moiety_head_atom->GetNode(coord_index)->GetNodeNeighbors();
    if (std::find(real_moiety_head_neighbors.begin(), real_moiety_head_neighbors.end(), open_atom) == real_moiety_head_neighbors.end()){
        moiety_head_atom->GetNodes().at(coord_index)->AddNodeNeighbor(open_atom);
    }
    //std::cout << "Added bond between " << open_atom->GetName() << " and " << moiety_head_atom->GetName() << std::endl;
    /*AtomVector open_atom_neighbors2 = open_atom->GetNode(coord_index)->GetNodeNeighbors();
    std::cout << "Coord index is " << coord_index << std::endl;
    for (unsigned int i = 0; i < open_atom_neighbors2.size(); i++){
        std::cout << "open atom neighbor: " << open_atom_neighbors2[i]->GetName() << std::endl;
    }*/


    return;
}

void GraftMoietyAndRemoveDummyAtomsForPrimaryMoiety(MolecularModeling::Atom* fake_tail_inner, MolecularModeling::Atom* moiety_fake_head_inner, MolecularModeling::Atom* fake_tail_outer, MolecularModeling::Atom* moiety_real_head_atom, MolecularModeling::Assembly& moiety_assembly, int coord_index){
    //Fake tail inner is the actual open valence atom
    /*This is done is two steps. First, compute translation vector by arg1-arg2.Perform translation to superpose arg2 to arg1. Second, set angle arg4-arg1/arg2-arg3 to zero degrees. This superimposes arg4      to arg3. The end result is arg2-arg4 being superimposed onto arg1-arg3
    */
    //Obtain translation vector
    GeometryTopology::Coordinate* ring_coord = fake_tail_inner->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* fake_head_coord = moiety_fake_head_inner->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate translation_vector;
    translation_vector.SetX(ring_coord->GetX() - fake_head_coord->GetX());
    translation_vector.SetY(ring_coord->GetY() - fake_head_coord->GetY());
    translation_vector.SetZ(ring_coord->GetZ() - fake_head_coord->GetZ());

    //Translate all moiety_atoms by this tranlation vector.
    AtomVector moiety_atoms = moiety_assembly.GetAllAtomsOfAssembly();

    for (unsigned int i = 0; i < moiety_atoms.size(); i++){
        GeometryTopology::Coordinate* moiety_atom_coord = moiety_atoms[i]->GetCoordinates().at(coord_index);
        moiety_atom_coord->SetX(moiety_atom_coord->GetX() + translation_vector.GetX());
        moiety_atom_coord->SetY(moiety_atom_coord->GetY() + translation_vector.GetY());
        moiety_atom_coord->SetZ(moiety_atom_coord->GetZ() + translation_vector.GetZ());
    }

    //Set that angle to zero
    SetAngle(fake_tail_outer, moiety_fake_head_inner, moiety_real_head_atom, 0, coord_index);

    //Add a bond
    AtomVector fake_tail_inner_neighbors = fake_tail_inner->GetNode(coord_index)->GetNodeNeighbors();
    if (std::find(fake_tail_inner_neighbors.begin(), fake_tail_inner_neighbors.end(), moiety_real_head_atom) == fake_tail_inner_neighbors.end()){
        fake_tail_inner->GetNodes().at(coord_index)->AddNodeNeighbor(moiety_real_head_atom);
    }
    AtomVector real_moiety_head_neighbors = moiety_real_head_atom->GetNode(coord_index)->GetNodeNeighbors();
    if (std::find(real_moiety_head_neighbors.begin(), real_moiety_head_neighbors.end(), fake_tail_inner) == real_moiety_head_neighbors.end()){
        moiety_real_head_atom->GetNodes().at(coord_index)->AddNodeNeighbor(fake_tail_inner);
    }

    /*AtomVector fake_tail_inner_neighbors2 = fake_tail_inner->GetNode(coord_index)->GetNodeNeighbors();
    std::cout << "Primary moiety open valence atom neighbors after grafting: ";
    for (unsigned int i = 0; i < fake_tail_inner_neighbors2.size(); i++){
        std::cout << fake_tail_inner_neighbors2[i]->GetName() << ",";
    }
    std::cout << std::endl;*/

    return;
}

void RecordProtonSet(AtomVector& atoms_to_search, std::map<Atom*, AtomVector>& atom_protons_map){
    //atom_protons_map.clear();
    std::vector<std::string> residue_name_blacklist = {"CA","NA"}; //These ions sometimes are bonded to protons of its chelated part. Prevent actually adding the "bonded" protons to the set.

    for (unsigned int i = 0; i < atoms_to_search.size(); i++){
        MolecularModeling::Atom* heavy_atom = atoms_to_search[i];

	    std::string heavy_atom_residue_name = heavy_atom->GetResidue()->GetName();
	    AtomVector heavy_atom_neighbors = heavy_atom->GetNode()->GetNodeNeighbors();
	    AtomVector heavy_atom_hydrogen_neighbors;

	    if (std::find(residue_name_blacklist.begin(), residue_name_blacklist.end(), heavy_atom_residue_name) == residue_name_blacklist.end()){
	        for (unsigned int j = 0; j < heavy_atom_neighbors.size(); j++){
	            if (heavy_atom_neighbors[j]->GetElementSymbol() == "H"){
	                heavy_atom_hydrogen_neighbors.push_back(heavy_atom_neighbors[j]);
	            }
	        }
	    }
	    atom_protons_map[heavy_atom] = heavy_atom_hydrogen_neighbors;
    }
}

void RemoveProtons(AtomVector& atoms_to_search){
    AtomVector all_H_atoms;
    std::vector<MolecularModeling::Residue*> all_residues;
    for (unsigned int i = 0; i < atoms_to_search.size(); i++){
	    MolecularModeling::Atom* atom = atoms_to_search[i];
        if (atom->GetElementSymbol() == "H"){
            all_H_atoms.push_back(atom);
	    }
	    MolecularModeling::Residue* residue = atom->GetResidue();
	    if (std::find(all_residues.begin(), all_residues.end(), residue) == all_residues.end()){
	        //std::cout << "Remove protons residue " << residue->GetName() << std::endl;
	        all_residues.push_back(residue);
	    }
    }

    for (unsigned int i = 0; i < all_residues.size(); i++){
        for (unsigned int j = 0; j < all_H_atoms.size(); j++){	
	        if (all_H_atoms[j]->GetResidue() == all_residues[i]){
                all_residues[i]->RemoveAtom(all_H_atoms[j]);
	        }
	    }
    }
}

void ApplyProtonSet(AtomVector& atoms_to_search, std::map<Atom*, AtomVector>& atom_protons_map){
    RemoveProtons(atoms_to_search);
    for (unsigned int i = 0; i < atoms_to_search.size(); i++){
        if (atoms_to_search[i]->GetElementSymbol() != "H"){
	        MolecularModeling::Atom* heavy_atom = atoms_to_search[i];
	        if (atom_protons_map.find(heavy_atom) == atom_protons_map.end()){
		        std::cout << "ApplyProtonSet cannot find heavy atom " << heavy_atom->GetResidue()->GetName() << "-" << heavy_atom->GetName() << std::endl;
		        std::exit(1);
	        }
	        else{
	            AtomVector& protons = atom_protons_map[heavy_atom];
		        AtomVector heavy_atom_neighbors = heavy_atom->GetNode()->GetNodeNeighbors();

		        for (unsigned int j = 0; j < protons.size(); j++){
		            MolecularModeling::Atom* proton = protons[j];
		            heavy_atom->GetResidue()->AddAtom(proton);
		            AtomVector proton_neighbors = proton->GetNode()->GetNodeNeighbors();

                    if (std::find(heavy_atom_neighbors.begin(), heavy_atom_neighbors.end(), proton) == heavy_atom_neighbors.end()){
		                heavy_atom->GetNode()->AddNodeNeighbor(proton);
		            }
		            if (std::find(proton_neighbors.begin(), proton_neighbors.end(), heavy_atom) == proton_neighbors.end()){
		                proton->GetNode()->AddNodeNeighbor(heavy_atom);
		            }
		        }
	        }
        }
    }
}

double GetDihedral(MolecularModeling::Atom *atom1, MolecularModeling::Atom *atom2, MolecularModeling::Atom *atom3, MolecularModeling::Atom *atom4, int coord_index)
{
    double current_dihedral = 0.0;
    GeometryTopology::Coordinate* a1 = atom1->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a2 = atom2->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a3 = atom3->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a4 = atom4->GetCoordinates().at(coord_index);

    GeometryTopology::Coordinate b1 = a2;
    b1.operator -(*a1);
    GeometryTopology::Coordinate b2 = a3;
    b2.operator -(*a2);
    GeometryTopology::Coordinate b3 = a4;
    b3.operator -(*a3);
    GeometryTopology::Coordinate b4 = b2;
    b4.operator *(-1);

    GeometryTopology::Coordinate b2xb3 = b2;
    b2xb3.CrossProduct(b3);

    GeometryTopology::Coordinate b1_m_b2n = b1;
    b1_m_b2n.operator *(b2.length());

    GeometryTopology::Coordinate b1xb2 = b1;
    b1xb2.CrossProduct(b2);

    current_dihedral = atan2(b1_m_b2n.DotProduct(b2xb3), b1xb2.DotProduct(b2xb3));
    return current_dihedral/3.14159*180;
}


void SetDihedral(MolecularModeling::Atom *atom1, MolecularModeling::Atom *atom2, MolecularModeling::Atom *atom3, MolecularModeling::Atom *atom4, double torsion, int coord_index)
{
    double current_dihedral = 0.0;
    GeometryTopology::Coordinate* a1 = atom1->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a2 = atom2->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a3 = atom3->GetCoordinates().at(coord_index);
    GeometryTopology::Coordinate* a4 = atom4->GetCoordinates().at(coord_index);

    GeometryTopology::Coordinate b1 = a2;
    b1.operator -(*a1);
    GeometryTopology::Coordinate b2 = a3;
    b2.operator -(*a2);
    GeometryTopology::Coordinate b3 = a4;
    b3.operator -(*a3);
    GeometryTopology::Coordinate b4 = b2;
    b4.operator *(-1);

    GeometryTopology::Coordinate b2xb3 = b2;
    b2xb3.CrossProduct(b3);

    GeometryTopology::Coordinate b1_m_b2n = b1;
    b1_m_b2n.operator *(b2.length());

    GeometryTopology::Coordinate b1xb2 = b1;
    b1xb2.CrossProduct(b2);

    current_dihedral = atan2(b1_m_b2n.DotProduct(b2xb3), b1xb2.DotProduct(b2xb3));

    double** torsion_matrix = gmml::GenerateRotationMatrix(&b4, a2, current_dihedral - gmml::ConvertDegree2Radian(torsion));

    AtomVector atomsToRotate = AtomVector();
    atomsToRotate.push_back(atom2);
    atom3->FindConnectedAtoms(atomsToRotate);

    for(AtomVector::iterator it = atomsToRotate.begin(); it != atomsToRotate.end(); it++)
    {
   //     std::cout << (*it)->GetName() << ", ";
        GeometryTopology::Coordinate* atom_coordinate = (*it)->GetCoordinates().at(coord_index);
        GeometryTopology::Coordinate result;
        result.SetX(torsion_matrix[0][0] * atom_coordinate->GetX() + torsion_matrix[0][1] * atom_coordinate->GetY() +
                torsion_matrix[0][2] * atom_coordinate->GetZ() + torsion_matrix[0][3]);
        result.SetY(torsion_matrix[1][0] * atom_coordinate->GetX() + torsion_matrix[1][1] * atom_coordinate->GetY() +
                torsion_matrix[1][2] * atom_coordinate->GetZ() + torsion_matrix[1][3]);
        result.SetZ(torsion_matrix[2][0] * atom_coordinate->GetX() + torsion_matrix[2][1] * atom_coordinate->GetY() +
                torsion_matrix[2][2] * atom_coordinate->GetZ() + torsion_matrix[2][3]);
        (*it)->GetCoordinates().at(coord_index)->SetX(result.GetX());
        (*it)->GetCoordinates().at(coord_index)->SetY(result.GetY());
        (*it)->GetCoordinates().at(coord_index)->SetZ(result.GetZ());
    }

    //Delelete dynamically allocated 3x4 rotation matrix
    for (int i = 0 ; i < 3; i++){
        delete[] torsion_matrix[i];
    }
    delete[] torsion_matrix;

    return;
}

void FilterForIntraResidueAtoms(gmml::AtomVector& atoms_to_search, MolecularModeling::Residue* residue){
    AtomVector extra_residue_atoms;
    for (unsigned int i = 0; i < atoms_to_search.size(); i++){
        if (atoms_to_search[i]->GetResidue() != residue){
            extra_residue_atoms.push_back(atoms_to_search[i]);
        }
    }
    for (unsigned int i = 0; i < extra_residue_atoms.size(); i++){
        atoms_to_search.erase(std::find(atoms_to_search.begin(), atoms_to_search.end(), extra_residue_atoms[i]));
    }

}

void WritePdbFromAssembly(MolecularModeling::Assembly* assembly, std::string pdb_file_name){
    PdbFileSpace::PdbFile *outputPdbFile = assembly->BuildPdbFileStructureFromAssembly();
    outputPdbFile->Write(pdb_file_name);
}

void ApplyAtomTypeAndChargeSet(std::map<MolecularModeling::Atom*, std::string>& atom_type_map, std::map<MolecularModeling::Atom*, double>& atom_charge_map){
    for(std::map<MolecularModeling::Atom*, std::string>::iterator mapit = atom_type_map.begin(); mapit != atom_type_map.end(); mapit++){
        mapit->first->MolecularDynamicAtom::SetAtomType(mapit->second);
	//std::cout << "ApplyAtomTypeAndChargeSet type" << mapit->first->GetName() << "-" << mapit->second << std::endl;
    }
    for (std::map<MolecularModeling::Atom*, double>::iterator mapit = atom_charge_map.begin(); mapit != atom_charge_map.end(); mapit++){
	//std::cout << "ApplyAtomTypeAndChargeSet charge" << mapit->first->GetName() << "-" << mapit->second << std::endl;
        mapit->first->MolecularDynamicAtom::SetCharge(mapit->second);
    }
}


//Make some typedefs specific for cycle detection
typedef std::map<std::string, AtomVector> CycleMap;
typedef std::map<std::string, gmml::GraphSearchNodeStatus> AtomStatusMap;
typedef std::map<std::string, Atom*> AtomIdAtomMap;

void DFSVisit(MolecularModeling::AtomVector atoms, AtomStatusMap& atom_status_map, AtomIdAtomMap& atom_parent_map, Atom *atom, int& counter, AtomIdAtomMap& src_dest_map)
{
    atom_status_map[atom->GetId()] = gmml::VISITED;
    MolecularModeling::AtomNode* node = atom->GetNode();
    MolecularModeling::AtomVector neighbors = node->GetNodeNeighbors();

    for(MolecularModeling::AtomVector::iterator it = neighbors.begin(); it != neighbors.end(); it++)
    {
        Atom* neighbor = (*it);
	if (std::find(atoms.begin(), atoms.end(), neighbor) != atoms.end()){
            MolecularModeling::Residue* residue = neighbor->GetResidue();
            // if(neighbor->GetDescription().find("Het;") != std::string::npos)
            //if((residue->GetName().compare("HOH") != 0) && (residue->CheckIfProtein() != true))
	    //This function will be used on protein residues.
            if(residue->GetName().compare("HOH") != 0)
            {
                if(atom_status_map[neighbor->GetId()] == gmml::UNVISITED)
                {
                    atom_parent_map[neighbor->GetId()] = atom;
                    DFSVisit(atoms, atom_status_map, atom_parent_map, neighbor, counter, src_dest_map);
                }
                if(atom_status_map[neighbor->GetId()] == gmml::VISITED)
                {
                    Atom* parent = atom_parent_map[atom->GetId()];
                    if(neighbor->GetId().compare(parent->GetId()) != 0)///making sure we are not tracking back to the previous atom which is the parent of neigbor (current atom)
                    {
                        counter++;
                        std::stringstream key;
                        key << neighbor->GetId() << "-" << atom->GetId();
                        src_dest_map[key.str()] = atom;
                    }
                }
            }
        }
    }
    atom_status_map[atom->GetId()] = gmml::DONE;
}

void ReturnCycleAtoms(std::string src_id, MolecularModeling::Atom *current_atom, AtomIdAtomMap &atom_parent_map, MolecularModeling::AtomVector &cycle, std::stringstream &cycle_stream)
{
    cycle.push_back(current_atom);
    cycle_stream << current_atom->GetId() << "-";
    MolecularModeling::Atom* parent = atom_parent_map[current_atom->GetId()];
    if(src_id.compare(parent->GetId()) == 0)
    {
        cycle.push_back(parent);
        cycle_stream << parent->GetId();
        return;
    }
    ReturnCycleAtoms(src_id, parent, atom_parent_map, cycle, cycle_stream);
}

std::vector<AtomVector> DetectCyclesByDFS(AtomVector& atoms)
{

    int local_debug = 0;
    int counter = 0;

    std::vector<AtomVector> all_cycles_detected;
    AtomStatusMap atom_status_map = AtomStatusMap();
    AtomIdAtomMap atom_parent_map = AtomIdAtomMap();
    AtomIdAtomMap src_dest_map = AtomIdAtomMap();

    MolecularModeling::AtomVector cycle = MolecularModeling::AtomVector();
    CycleMap cycles = CycleMap();

    //Atom* parent = new Atom();
    Atom parent;
    parent.SetId("null");
    //No longer use the atoms from below. Provide as argument. 
    //MolecularModeling::AtomVector atoms = GetAllAtomsOfAssemblyExceptProteinWaterResiduesAtoms();
    for(MolecularModeling::AtomVector::iterator it = atoms.begin(); it != atoms.end(); it++)
    {
        Atom* atom = (*it);
        atom_status_map[atom->GetId()] = gmml::UNVISITED;
        //Atom* parent = new Atom();
        //parent->SetId("null");
        atom_parent_map[atom->GetId()] = &parent;
    }
    for(MolecularModeling::AtomVector::iterator it = atoms.begin(); it != atoms.end(); it++)
    {
        Atom* atom = (*it);
        if(atom_status_map[atom->GetId()] == gmml::UNVISITED)
        {
            DFSVisit(atoms, atom_status_map, atom_parent_map, atom, counter, src_dest_map);
        }
    }

    std::stringstream n_of_cycle;
    n_of_cycle << "Number of cycles found: " << counter;
//    std::cout << n_of_cycle.str() << std::endl;
//
    for(AtomIdAtomMap::iterator it = src_dest_map.begin(); it != src_dest_map.end(); it++)
    {
        std::string src_dest = (*it).first;
        Atom* destination = (*it).second;
        cycle.clear();
        std::stringstream cycle_stream;
        std::vector<std::string> key = gmml::Split(src_dest, "-");
        ReturnCycleAtoms(key.at(0), destination, atom_parent_map, cycle, cycle_stream);
        cycles[cycle_stream.str()] = cycle;
    }

    for (CycleMap::iterator mapit = cycles.begin(); mapit != cycles.end(); mapit++){
        all_cycles_detected.push_back(mapit->second);
    }
    //return cycles;
    return all_cycles_detected;
}

std::vector<AtomVector> DetectAromaticCycles(std::vector<MolecularModeling::Residue*>& residues){
    std::vector<AtomVector> aromatic_cycles; 
    for (unsigned int i = 0; i < residues.size(); i++){
        AtomVector residue_atoms = residues[i]->GetAtoms();
	std::vector<AtomVector> cycles_this_residue = DetectCyclesByDFS(residue_atoms); 
	for (unsigned int j = 0; j < cycles_this_residue.size(); j++){
	    AtomVector& this_cycle = cycles_this_residue[j];
	    AtomVector  this_cycle_armomatic_carbons;

	    for (unsigned int k = 0; k < this_cycle.size(); k++){
	        if (this_cycle[k]->MolecularDynamicAtom::GetAtomType() == "A"){
		    aromatic_cycles.push_back(this_cycle);
		    break;
		}
	    }
	}
    }

    std::vector<AtomVector> aromatic_cycles_non_duplicate; //Check if a cycle is a subset of another cycle.
    for (unsigned int i = 0; i < aromatic_cycles.size(); i++){
        AtomVector& this_cycle = aromatic_cycles[i];
	bool this_cycle_is_subset = false;
	for (unsigned int j = 0; j < aromatic_cycles.size(); j++){
	    if (j != i){
	        AtomVector& another_cycle = aromatic_cycles[j];
		bool another_cycle_contains_this_cycle = true;
		for (unsigned int k = 0; k < this_cycle.size(); k++){
		    MolecularModeling::Atom* this_cycle_atom = this_cycle[k];
		    if (std::find(another_cycle.begin(), another_cycle.end(), this_cycle_atom) == another_cycle.end()){
		        another_cycle_contains_this_cycle = false;
			break;
		    }
		}

		if (another_cycle_contains_this_cycle){
		    this_cycle_is_subset = true;
		    break;
		}
	    }
	}

	if (!this_cycle_is_subset){
	    aromatic_cycles_non_duplicate.push_back(this_cycle);
	}
    }
    return aromatic_cycles_non_duplicate;
}

std::vector<AtomVector> DetectAromaticCycles(AtomVector& atoms){
    std::vector<AtomVector> aromatic_cycles;
    std::vector<AtomVector> cycles_this_residue = DetectCyclesByDFS(atoms);
    for (unsigned int j = 0; j < cycles_this_residue.size(); j++){
        AtomVector& this_cycle = cycles_this_residue[j];

        for (unsigned int k = 0; k < this_cycle.size(); k++){
            if (this_cycle[k]->MolecularDynamicAtom::GetAtomType() == "A"){
                aromatic_cycles.push_back(this_cycle);
                break;
            }
        }
    }

    return aromatic_cycles;
}

MolecularModeling::Residue* GetResidueByIndex(std::string residue_index_str, ResidueVector& residues_to_search){
    int count = 0;
    MolecularModeling::Residue* residue = NULL;

    for (unsigned int i = 0; i < residues_to_search.size(); i++){
	std::string this_ligand_residue_id = residues_to_search[i]->GetId();
        std::vector<std::string> underscore_split_token = gmml::Split(this_ligand_residue_id, "_");

        std::string& this_residue_index_str = underscore_split_token[2];
	if (residue_index_str == this_residue_index_str){
	     residue = residues_to_search[i];
	     count++;
	}
    }

    if (count == 1){
        return residue;
    }
    else if (count == 0){
        std::cout << "Cannot find residue with index " << residue_index_str  << std::endl;
    }
    else if (count > 1){
        std::cout << "Multiple residues with index " << residue_index_str << std::endl;
    }
    std::cout << "Problem with residue index " << residue_index_str << std::endl;
    std::exit(1);
    return NULL;
}

MolecularModeling::Atom* GetAtomByResidueIndexAndAtomName(std::string residue_index_str, std::string atom_name, ResidueVector& residues_to_search){
    MolecularModeling::Residue* residue = GetResidueByIndex(residue_index_str, residues_to_search);
    AtomVector residue_atoms = residue->GetAtoms();
    MolecularModeling::Atom* atom = GetAtomByName(atom_name, residue_atoms);
    return atom;
}
#endif // UTILITY_HPP
