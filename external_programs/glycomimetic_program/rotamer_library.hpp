#ifndef ROTAMER_LIBRARY_HPP
#define ROTAMER_LIBRARY_HPP

#include<map>
#include<vector>
#include<string>
#include<utility> //std::pair

//Dynameomics backbone-independent library
std::map<std::string, std::pair<std::vector<std::string>, std::vector<std::vector<double> > > > amino_acid_rotamer_library_map = {
    {"ARG",{{"N-CA-CB-CG","CA-CB-CG-CD","CB-CG-CD-NE","CG-CD-NE-NH1"},{ {-70.3,179.7,67.7,-173.9},{-68.5,-177.8,-177.1,176.5},{-68.4,-168.2,-63.3,-88.6},{-66.4,-171.9,-66.3,175.7} }}},
    {"ASN",{{"N-CA-CB-CG","CA-CB-CG-OD1"},{ {-179.8,-106.8},{178.8,54.0},{-171.7,-71.4},{-173.2,7.5},{-70.3,-58.8} }}},
    {"ASP",{{"N-CA-CB-CG","CA-CB-CG-OD1"},{ {-178.1,62.8},{-166.3,107.8},{-172.6,-169.6},{-75.6,116.8} }}},
    {"CYS",{{"N-CA-CB-SG"},{ {-61.0},{-175.9},{51.9} }}},
    {"GLN",{{"N-CA-CB-CG","CA-CB-CG-CD","CB-CG-CD-OE1"},{ {-70.9,-179.9,65.1},{-68.0,-174.7,-63.2},{-69.0,-173.1,110.8},{-69.9,178.2,-110.7},{-69.5,-178.7,-0.3} }}},
    {"GLU",{{"N-CA-CB-CG","CA-CB-CG-CD","CB-CG-CD-OE1"},{ {-67.2,-172.1,114.6},{-69.4,-175.8,66.7},{-69.7,-176.0,179.1},{-71.3,-70.8,120.1},{-168.6,-177.1,112.6},{-169.5,177.9,67.8} }}},
    {"HIS",{{"N-CA-CB-CG","CA-CB-CG-ND1"},{ {-64.3,-60.7},{-62.2,113.7},{-178.3,63.2},{-176.4,-113.1},{-75.1,71.3},{-164.7,-69.3},{-70.9,-9.6} }}},
    {"ILE",{{"N-CA-CB-CG1","CA-CB-CG1-CD1"},{ {53.9,167.6},{-60.4,175.8},{-59.2,-61.6} }}},
    {"LEU",{{"N-CA-CB-CG","CA-CB-CG-CD1"},{ {-69.0,168.5},{-177.1,67.2} }}},
    {"LYS",{{"N-CA-CB-CG","CA-CB-CG-CD","CB-CG-CD-CE","CG-CD-CE-NZ"},{ {-68.4,-176.1,-171.6,-61.7},{-68.0,-176.3,172.5,61.6},{-67.7,-68.9,-171.7,-63.1},{-67.5,-71.3,178.2,64.4},{-64.9,-169.3,-69.4,-65.2} }}},
    {"MET",{{"N-CA-CB-CG","CA-CB-CG-SD","CB-CG-SD-CE"},{ {-67.5,-167.2,-67.5},{-70.2,179.4,70.7},{-68.9,-175.5,179.8},{-70.1,-59.8,-69.7},{-69.3,-62.7,177.4} }}},
    {"PHE",{{"N-CA-CB-CG","CA-CB-CG-CD1"},{ {-70.0,101.9},{-175.2,78.1},{55.4,87.9},{-67.4,157.8} }}},
    {"SER",{{"N-CA-CB-OG"},{ {-49.7},{40.7} }}},
    {"THR",{{"N-CA-CB-OG1"},{ {-42.4},{36.5} }}},
    {"TRP",{{"N-CA-CB-CG","CA-CB-CG-CD1"},{ {-66.8,99.9},{-177.1,-100.7},{-69.1,-14.7},{-175.8,78.1},{-174.9,29.5},{-67.1,-79.8},{52.8,-88.9} }}},
    {"TYR",{{"N-CA-CB-CG","CA-CB-CG-CD1"},{ {-68.9,102.3},{-175.8,77.5},{57.0,88.6},{-66.2,156.2} }}},
    {"VAL",{{"N-CA-CB-CG1"},{ {179.8},{-72.1} }}}
};

    //{"CYX",{{"N-CA-CB-SG"},{ {-61.0},{-176.5},{55.6} }}},  CYX is bonded to another aa residue, cannot rotate

std::map<double, MolecularModeling::Residue*, std::greater<double> > SortClashingResiduesInDescendingOrder(AtomVector& moiety_atoms, AtomVector& receptor_atoms){
    std::map<double, MolecularModeling::Residue*, std::greater<double> > score_clashing_residue_map;
    std::vector<MolecularModeling::Residue*> receptor_residues;

    for (unsigned int i = 0; i < receptor_atoms.size(); i++){
        MolecularModeling::Residue* this_atom_residue = receptor_atoms[i]->GetResidue();
        if (this_atom_residue->CheckIfProtein() && std::find(receptor_residues.begin(), receptor_residues.end(), this_atom_residue) == receptor_residues.end()){
            receptor_residues.push_back(this_atom_residue);
        }
    }

    for (unsigned int i = 0; i < receptor_residues.size(); i++){
        MolecularModeling::Residue* this_residue = receptor_residues[i];
        AtomVector residue_atoms = this_residue->GetAtoms();

        VinaScorePrerequisites prerequisite(moiety_atoms, residue_atoms);
        double score = VinaScoreInPlace(prerequisite, 0)[0];
        if (score > 0.1){
            score_clashing_residue_map[score] = this_residue;
        }
    }

    return score_clashing_residue_map;
}

void ResolveClashesUsingRotamerLibrary(std::map<double, MolecularModeling::Residue*, std::greater<double> >& score_clashing_residue_map, AtomVector& moiety_atoms, AtomVector& receptor_atoms){

    std::vector<MolecularModeling::Residue*> receptor_residues;
    for (unsigned int i = 0; i < receptor_atoms.size(); i++){
        MolecularModeling::Residue* this_atom_residue = receptor_atoms[i]->GetResidue();
        if (this_atom_residue->CheckIfProtein() && std::find(receptor_residues.begin(), receptor_residues.end(), this_atom_residue) == receptor_residues.end()){
            receptor_residues.push_back(this_atom_residue);
        }
    }

    for (std::map<double, MolecularModeling::Residue*>::iterator mapit = score_clashing_residue_map.begin(); mapit != score_clashing_residue_map.end(); mapit++){
        double this_residue_current_score = mapit->first;
        MolecularModeling::Residue* this_clashing_residue = mapit->second;
        std::string residue_name = this_clashing_residue->GetName();
        std::cout << "Resolving residue " << residue_name << std::endl;
        if (amino_acid_rotamer_library_map.find(residue_name) == amino_acid_rotamer_library_map.end()){
            std::cout << "No rule for resolving residue " << residue_name << ". Skipping" << std::endl;
            continue;
        }

        AtomVector this_residue_atoms = this_clashing_residue->GetAtoms();

        std::pair<std::vector<std::string>, std::vector<std::vector<double> > >& chi_token_rotamer_pair = amino_acid_rotamer_library_map[residue_name];
        std::vector<std::string>& chi_tokens = chi_token_rotamer_pair.first;
        std::vector<std::vector<double> >& rotamers = chi_token_rotamer_pair.second;

        std::vector<AtomVector> chi_torsions;
        for (unsigned int i = 0; i < chi_tokens.size(); i++){
            std::vector<std::string> dash_split_token = gmml::Split(chi_tokens[i], "-");
            AtomVector chi;
            for(unsigned int j = 0; j < dash_split_token.size(); j++){
                MolecularModeling::Atom* chi_atom = GetAtomByName(dash_split_token[j], this_residue_atoms);
                chi.push_back(chi_atom);
            }
            chi_torsions.push_back(chi);
        }

        //Save input torsion values;
	std::vector<double> input_torsion_values;
        for (unsigned int i = 0; i < chi_torsions.size(); i++){
            input_torsion_values.push_back(GetDihedral(chi_torsions[i][0], chi_torsions[i][1], chi_torsions[i][2], chi_torsions[i][3], 0));
        }

        AtomVector other_residue_atoms;
        std::vector<MolecularModeling::Residue*> other_residues = receptor_residues;
        other_residues.erase(std::find(other_residues.begin(), other_residues.end(), this_clashing_residue));

        for (unsigned int i = 0; i < other_residues.size(); i++){
            AtomVector other_res_atoms = receptor_residues[i]->GetAtoms();
            other_residue_atoms.insert(other_residue_atoms.end(), other_res_atoms.begin(), other_res_atoms.end());
        }

        VinaScorePrerequisites prerequisite_3(this_residue_atoms, other_residue_atoms);
        double intra_receptor_score_before_searching = VinaScoreInPlace(prerequisite_3, 0)[0];

        bool better_rotamer_found = false;
        int best_rotamer_index = 9999;

	for (unsigned int i = 0; i < rotamers.size(); i++){
            std::vector<double>& this_rotamer = rotamers[i];
            for (unsigned int j = 0; j < chi_torsions.size(); j++){
                SetDihedral(chi_torsions[j][0], chi_torsions[j][1], chi_torsions[j][2], chi_torsions[j][3], this_rotamer[j], 0);
            }

            VinaScorePrerequisites prerequisite(moiety_atoms, this_residue_atoms);
            double new_score = VinaScoreInPlace(prerequisite, 0)[0];


            VinaScorePrerequisites prerequisite_2(this_residue_atoms, other_residue_atoms);
            double new_intra_receptor_score = VinaScoreInPlace(prerequisite_2, 0)[0];

            //if (new_intra_receptor_score - intra_receptor_score_before_searching < 0.5 && new_score < this_residue_current_score)
            if (new_intra_receptor_score + new_score < intra_receptor_score_before_searching + this_residue_current_score){
                //Accept this rotamer, so leave the torsion set this way
                std::cout << "Old intra score " << intra_receptor_score_before_searching << " New intra score " << new_intra_receptor_score << std::endl;
                std::cout << "This residue current score: " << this_residue_current_score << " New score: " << new_score << std::endl;
                intra_receptor_score_before_searching = new_intra_receptor_score;
                this_residue_current_score = new_score;
                best_rotamer_index = i;
                better_rotamer_found = true;
            }
        }

	if (better_rotamer_found){
            //Apply the best rotamer for this receptor residue
            std::cout << "Better rotamer found" << std::endl;
            for (unsigned int i = 0; i < chi_torsions.size(); i++){
                SetDihedral(chi_torsions[i][0], chi_torsions[i][1], chi_torsions[i][2], chi_torsions[i][3], rotamers[best_rotamer_index][i], 0);
            }
        }
        else{
            //Restore input torsion values;
            std::cout << "No better rotamer found, restoring initial" << std::endl;
            for (unsigned int i = 0; i < chi_torsions.size(); i++){
                SetDihedral(chi_torsions[i][0], chi_torsions[i][1], chi_torsions[i][2], chi_torsions[i][3], input_torsion_values[i], 0);
            }
        }

    }
}
#endif
