import os
import sys
import evaluate_pdb


pdb_file_path = os.path.join(os.path.dirname(__file__), "..", "1gya.pdb")

result = evaluate_pdb.evaluate_pdb(pdb_file_path)

print("Valid PDB:", result.is_valid)
print("PDB2GLYCAM Available:", result.pdb2glycam_available)
print("Sugars Detected:", result.sugars_detected)
print("Available Atoms:")
for atom in result.available_atoms:
    print(f"{atom.residue_index_str_}-{atom.resname_}-{atom.chain_id_}-{atom.atom_name_}-{atom.atom_to_replace_}")
