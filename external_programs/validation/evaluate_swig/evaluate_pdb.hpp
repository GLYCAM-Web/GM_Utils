#ifndef EVALUATE_PDB_HPP
#define EVALUATE_PDB_HPP

#include <vector>
#include <string>
#include <stdexcept>

struct available_atom {
    available_atom() = default; // Default constructor
    available_atom(const std::string& residue_index_str, const std::string& resname, const std::string& chain_id, const std::string& atom_name, const std::string& atom_to_replace)
        : residue_index_str_(residue_index_str), resname_(resname), chain_id_(chain_id), atom_name_(atom_name), atom_to_replace_(atom_to_replace) {}

    std::string residue_index_str_, resname_, chain_id_, atom_name_, atom_to_replace_;
};

struct PDBEvaluationResult {
    bool is_valid;
    bool pdb2glycam_available;
    bool sugars_detected;
    std::vector<available_atom> available_atoms;
};

PDBEvaluationResult evaluate_pdb(const std::string& pdb_file_path);

#endif