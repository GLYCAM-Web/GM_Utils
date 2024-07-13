
#include "evaluate_pdb.hpp"
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

#include "vina_bond_by_distance_for_pdb.hpp"
#include "pdb2glycam.hpp"

typedef std::vector<MolecularModeling::Atom*> AtomVector;

std::vector<available_atom> detect_available_atoms(std::vector<Glycan::Monosaccharide*> monos) {
    std::vector<available_atom> available_atoms;

    for (auto* mono : monos) {
        AtomVector cycle_atoms = mono->cycle_atoms_;
        MolecularModeling::Residue* this_residue = cycle_atoms[0]->GetResidue();

        std::string residue_id = this_residue->GetId();
        std::vector<std::string> underscore_split_token = gmml::Split(residue_id, "_");
        std::string residue_index = underscore_split_token[2];
        std::string chain_id = this_residue->GetChainID();
        std::string resname = this_residue->GetName(); 
        AtomVector this_residue_atoms = this_residue->GetAtoms();

        for (auto* cycle_atom : cycle_atoms) {
            AtomVector cycle_neighbors = cycle_atom->GetNode()->GetNodeNeighbors();

            for (auto* neighbor : cycle_neighbors) {
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

PDBEvaluationResult evaluate_pdb(const std::string& pdb_file_path) {
    std::string GEMSHOME = std::getenv("GEMSHOME");
    if (GEMSHOME.empty()) {
        throw std::runtime_error("GEMSHOME environment variable not set");
    }

    try {
        // Check if the file exists and is readable
        std::ifstream file(pdb_file_path);
        if (!file) {
            throw std::runtime_error("Unable to open or read file: " + pdb_file_path);
        }
        file.close();

        std::string lib1 = GEMSHOME + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/amino12.lib";
        std::string lib2 = GEMSHOME + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminoct12.lib";
        std::string lib3 = GEMSHOME + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminont12.lib";
        std::vector<std::string> amino_libs = {lib1, lib2, lib3};
        std::string prep = GEMSHOME + "/gmml/dat/prep/GLYCAM_06j-1.prep";

        // Check if all required files exist
        for (const auto& lib : amino_libs) {
            if (!std::ifstream(lib)) {
                throw std::runtime_error("Required library file not found: " + lib);
            }
        }
        if (!std::ifstream(prep)) {
            throw std::runtime_error("Required prep file not found: " + prep);
        }

        MolecularModeling::Assembly assemblyA(pdb_file_path, gmml::InputFileType::PDB); 
        VinaBondByDistanceForPDB(assemblyA, 0);

        bool is_valid = false, pdb2glycam_available = false, sugars_detected = false;

        std::vector<Glycan::Monosaccharide*> monos;
        std::vector<Glycan::Oligosaccharide*> oligos = assemblyA.ExtractSugars(amino_libs, monos, false, false);

        if (!oligos.empty()){
            sugars_detected = true;
        }

        std::map<MolecularModeling::Atom*, MolecularModeling::Atom*> actual_template_atom_match;
        AtomVector atoms = assemblyA.GetAllAtomsOfAssembly();
        pdb2glycam_available = pdb2glycam_matching(pdb_file_path, actual_template_atom_match, atoms, gmml::InputFileType::PDB, amino_libs, prep);

        std::vector<available_atom> available_atoms = detect_available_atoms(monos);
        is_valid = !available_atoms.empty() && sugars_detected;

        return {is_valid, pdb2glycam_available, sugars_detected, available_atoms};
    } catch (const std::ios_base::failure& e) {
        throw std::runtime_error("File I/O error: " + std::string(e.what()));
    } catch (const std::bad_alloc& e) {
        throw std::runtime_error("Memory allocation failed: " + std::string(e.what()));
    } catch (const std::exception& e) {
        throw std::runtime_error("Error in evaluate_pdb: " + std::string(e.what()));
    } catch (...) {
        throw std::runtime_error("Unknown error occurred in evaluate_pdb");
    }
}