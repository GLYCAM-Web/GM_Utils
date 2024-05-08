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

#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <sstream>
typedef std::vector<MolecularModeling::Atom*> AtomVector;

void WriteWaterRestraintSection(std::ofstream& input_file, std::vector<int>& water_oxygen_indices){
    input_file << "Restrain binding site water oxygens\n100.0" << std::endl;

    for (unsigned int i = 0; i < water_oxygen_indices.size(); i++){
        int& this_water_oxygen_index = water_oxygen_indices[i];
        input_file << "ATOM " << this_water_oxygen_index << " " << this_water_oxygen_index << std::endl;
    }

    input_file << "END" << std::endl;

    return;
}

void WriteStrandBreakRestraintSection(std::ofstream& input_file, std::vector<std::pair<int, int> >& strand_breaks){
    input_file << "Restrain strand breaks\n500.0" << std::endl;

    for (unsigned int i = 0; i < strand_breaks.size(); i++){
        std::pair<int, int>& this_break = strand_breaks[i];
        int& this_c_index = this_break.first;
        int& next_n_index = this_break.second;
        input_file << "ATOM " << this_c_index << " " << this_c_index << std::endl;
        input_file << "ATOM " << next_n_index << " " << next_n_index << std::endl;
    }

    input_file << "END" << std::endl;

    return;
}

void WriteTruncatedEndRestraintSection(std::ofstream& heating_input_file, std::pair<int, int>& head_n_tail_c_indices){
    int& head_n_index = head_n_tail_c_indices.first;
    int& tail_c_index = head_n_tail_c_indices.second;
    heating_input_file << "Restrain truncated end\n500.0" << std::endl;
    heating_input_file << "ATOM " << head_n_index << " " << head_n_index << std::endl;
    heating_input_file << "ATOM " << tail_c_index << " " << tail_c_index << std::endl;
    heating_input_file << "END" << std::endl;
}

void WriteAlphaCarbonRestraintSection(std::ofstream& input_file, int num_receptor_residues){
    std::string c_alpha_restraint_constant_part = R"(Restrain all protein C-alpha atoms
10.0
FIND
CA * * *
SEARCH)";
    input_file << c_alpha_restraint_constant_part << std::endl;
    input_file << "RES 1 " << num_receptor_residues << std::endl;
    input_file << "END" << std::endl;

    return;
}

void WriteSolventMinimizationInputFile(std::string file_path, int num_complex_residues){
    std::ofstream solvent_min_in(file_path);
    if (solvent_min_in.fail()){
        std::cout << "Cannot open " << file_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_part = R"(Constant Pressure Minimization
# Control section
&cntrl
 ntwe = 1, ntwx = 1, ntpr = 500,
 dielc = 1, cut = 12.0,
 ntb = 2, pres0 = 1.0, ntp = 1,
 maxcyc = 15000, ntmin = 1, ncyc = 5000, dx0 = 0.01, drms = 0.001,
 ibelly = 0, ntr = 1,
 imin = 1,
/
Hold the solute fixed
500.0)";

    solvent_min_in << constant_part << std::endl;
    solvent_min_in << "RES 1 " << num_complex_residues << std::endl;
    solvent_min_in << "END\nEND" << std::endl;

    solvent_min_in.close();
    return;
}

std::pair<int, int> FindHeadNTailC(MolecularModeling::Assembly& receptor_pdb){
    std::pair<int, int> head_n_tail_c_indices;
    ResidueVector receptor_residues = receptor_pdb.GetResidues();
    ResidueVector protein_residues;
    for (unsigned int i = 0; i < receptor_residues.size(); i++){
        MolecularModeling::Residue* residue = receptor_residues[i];
        if (residue->CheckIfProtein()){
            protein_residues.push_back(residue);
        }
    }

    AtomVector all_receptor_atoms = receptor_pdb.GetAllAtomsOfAssembly();
    AtomVector first_protein_residue_atoms = protein_residues[0]->GetAtoms();
    AtomVector last_protein_residue_atoms = protein_residues.back()->GetAtoms();

    for (unsigned int i = 0; i < first_protein_residue_atoms.size(); i++){
        MolecularModeling::Atom* atom = first_protein_residue_atoms[i];
        if (atom->GetName() == "N"){
            AtomVector::iterator it = std::find(all_receptor_atoms.begin(), all_receptor_atoms.end(), atom);
            int head_n_index = std::distance(all_receptor_atoms.begin(), it) + 1;
            head_n_tail_c_indices.first = head_n_index;
            break;
        }
    }

    for (unsigned int i = 0; i < last_protein_residue_atoms.size(); i++){
        MolecularModeling::Atom* atom = last_protein_residue_atoms[i];
        if (atom->GetName() == "C"){
            AtomVector::iterator it = std::find(all_receptor_atoms.begin(), all_receptor_atoms.end(), atom);
            int tail_c_index = std::distance(all_receptor_atoms.begin(), it) + 1;
            head_n_tail_c_indices.second = tail_c_index;
            break;
        }
    }

    return head_n_tail_c_indices;
}

void WriteAllMinimizationInputFile(std::string min_all_in_path, std::pair<int, int>& head_n_tail_c_indices, std::vector<std::pair<int, int>>& strand_breaks, std::vector<int>& water_oxygens){
    std::ofstream min_all_in(min_all_in_path);
    if (min_all_in.fail()){
        std::cout << "Cannot open " << min_all_in_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_part = R"(Constant Pressure Minimization
# Control section
&cntrl
 ntwe = 1, ntwx = 1, ntpr = 500,
 dielc = 1, cut = 12.0,
 ntb = 2, pres0 = 1.0, ntp = 1,
 maxcyc = 15000, ntmin = 1, ncyc = 5000, dx0 = 0.01, drms = 0.001,
 ibelly = 0, ntr = 1,
 imin = 1,
/)";

    min_all_in << constant_part << std::endl;

    if (!strand_breaks.empty()){
        WriteStrandBreakRestraintSection(min_all_in, strand_breaks);
    }
    WriteTruncatedEndRestraintSection(min_all_in, head_n_tail_c_indices);

    if (!water_oxygens.empty()){
        WriteWaterRestraintSection(min_all_in, water_oxygens);
    }

    min_all_in << "END" << std::endl;
    min_all_in.close();

    return;
}

void WriteHeatingInputFile(std::string heating_input_path, int num_receptor_residues, std::pair<int, int>& head_n_tail_c_indices, std::vector<std::pair<int, int>>& strand_breaks, std::vector<int>& water_oxygens){
    std::ofstream heating_input_file(heating_input_path);
    if (heating_input_file.fail()){
        std::cout << "Failed to open " << heating_input_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_part = R"(MD heating run at NPT
# control section
 &cntrl
 irest = 0,
 ntx = 1, ntb = 2, pres0 = 1.0, ntp = 1,
 cut = 12.0, ntt = 3, gamma_ln = 2,
 dielc = 1.0, ntc = 2, ntf = 2,
 tempi = 5.0, temp0 = 300.0,
 nstlim = 25000, dt = 0.002,
 ioutfm = 1,
 ntpr = 1000, ntwx = 1000, ntwv = 0, ntwe = 0,
 nmropt = 1, ntr = 1,
 /
 &wt
  type = 'TEMP0', istep1 = 1, istep2 = 25000, value1 = 5.0, value2 = 300.0,
 /
 &wt
  type='END'
 /)";
    heating_input_file << constant_part << std::endl;

    WriteAlphaCarbonRestraintSection(heating_input_file, num_receptor_residues);

    WriteTruncatedEndRestraintSection(heating_input_file, head_n_tail_c_indices);

    if (!strand_breaks.empty()){
        WriteStrandBreakRestraintSection(heating_input_file, strand_breaks);    
    }
    if (!water_oxygens.empty()){
        WriteWaterRestraintSection(heating_input_file, water_oxygens);
    }

    heating_input_file << "END" << std::endl;
}

void WriteEquilibrationInputFile(std::string equi_input_file_path, int num_receptor_residues, MolecularModeling::Assembly& complex_pdb, std::pair<int, int> head_n_tail_c_indices, std::vector<std::string> ligand_heavy_atom_restraint_section, std::vector<std::pair<int, int>>& strand_breaks, std::vector<int>& water_oxygens, bool restraint = false){
    std::ofstream equi_input_file(equi_input_file_path);
    if (equi_input_file.fail()){
        std::cout << "Failed to open " << equi_input_file_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string control_section = R"(MD production run at NPT
# control section
 &cntrl
 irest = 1,
 ntx = 5, ntb = 2, pres0 = 1.0, ntp = 1,
 cut = 12.0, ntt = 3, gamma_ln = 2,
 ntc = 2, ntf = 2,
 tempi = 300.0, temp0 = 300.0, tautp = 1.0,
 nstlim = 500000, dt = 0.002,
 ntpr = 5000, ntwx = 500, ntwv = 0, ntwe = 0,
 nmropt = 0, ntr = 1, ioutfm =1,iwrap=1,
 &end)";
    equi_input_file << control_section << std::endl;

    if (restraint){
        WriteAlphaCarbonRestraintSection(equi_input_file, num_receptor_residues);
        equi_input_file << "Restrain ligand heavy atoms\n10.0" << std::endl;
        for (unsigned int i = 0; i < ligand_heavy_atom_restraint_section.size(); i++){
            equi_input_file << ligand_heavy_atom_restraint_section[i] << std::endl;
        }
        equi_input_file << "END" << std::endl;
    }

    WriteTruncatedEndRestraintSection(equi_input_file, head_n_tail_c_indices);

    if (!strand_breaks.empty()){
        WriteStrandBreakRestraintSection(equi_input_file, strand_breaks);
    }
    if (!water_oxygens.empty()){
        WriteWaterRestraintSection(equi_input_file, water_oxygens);
    }

    equi_input_file << "END" << std::endl;

    return;

}

std::vector<std::string> ObtainLigandHeavyAtomRestraintSection(int num_receptor_atoms, AtomVector& complex_atoms){
    std::vector<std::string> restraint_section;
    for (unsigned int i = num_receptor_atoms; i < complex_atoms.size(); i++){
        MolecularModeling::Atom* atom =  complex_atoms[i];
        if (atom->GetElementSymbol() != "H"){
            std::stringstream restraint;
            //std::cout << "This ligand atom " << atom->GetResidue()->GetName() << "-" << atom->GetName() << std::endl;
            //int index = num_receptor_atoms + i;
            restraint << "ATOM " << i + 1 << " " << i + 1;
            restraint_section.push_back(restraint.str());
        }
    }

    return restraint_section;
}

void WriteMDInputFile(std::string md_input_file_path, int num_complex_atoms, std::pair<int, int>& head_n_tail_c_indices, std::vector<std::pair<int, int>>& strand_breaks, std::vector<int>& water_oxygens){
    std::ofstream md_input_file(md_input_file_path);
    if (md_input_file.fail()){
        std::cout << "Failed to open " << md_input_file_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string control_section1 = R"(MD production run at NPT
# control section
 &cntrl
 irest = 1,)";
    md_input_file << control_section1 << std::endl;
    md_input_file << " ntx = 5, ntb = 2, pres0 = 1.0, ntp = 1, ntwprt=" << num_complex_atoms << std::endl;

    std::string control_section2 = R"( cut = 12.0, ntt = 3, gamma_ln = 2,
 ntc = 2, ntf = 2,
 tempi = 300.0, temp0 = 300.0, tautp = 2.0,
 nstlim = 50000000, dt = 0.002,
 ntpr = 5000, ntwx = 5000, ntwv = 0, ntwe = 0,
 nmropt = 0, ntr = 1, ioutfm =1, iwrap=1,
 /)";
    md_input_file << control_section2 << std::endl;

    WriteTruncatedEndRestraintSection(md_input_file, head_n_tail_c_indices);
    if (!strand_breaks.empty()){
        WriteStrandBreakRestraintSection(md_input_file, strand_breaks);
    }
    if (!water_oxygens.empty()){
        WriteWaterRestraintSection(md_input_file, water_oxygens);
    }

    md_input_file << "END" << std::endl;
}

void WriteGBSAComplexInputFile(std::string gbsa_complex_input_file_path, int num_complex_residues, int num_receptor_residues){
    std::ofstream gbsa_complex_input_file(gbsa_complex_input_file_path);
    if (gbsa_complex_input_file.fail()){
        std::cout << "Failed to open " << gbsa_complex_input_file_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_section = R"(File generated by C++
&cntrl
 dec_verbose=0, ntb=0,
 surften=0.0072, extdiel=80.0, ncyc=0,
 cut=999.0, gbsa=2, imin=5, idecomp=1,
 igb=2, intdiel=3,
/)";

    gbsa_complex_input_file << constant_section << std::endl;

    gbsa_complex_input_file << "Residues considered as REC" << std::endl;
    gbsa_complex_input_file << "RRES 1 " << num_receptor_residues << std::endl;
    gbsa_complex_input_file << "END" << std::endl;

    gbsa_complex_input_file << "Residues considered as LIG" << std::endl;
    gbsa_complex_input_file << "LRES " << num_receptor_residues + 1 << " " << num_complex_residues << std::endl;
    gbsa_complex_input_file << "END" << std::endl;

    gbsa_complex_input_file << "Residues to print" << std::endl;
    gbsa_complex_input_file << "RES 1 " << num_complex_residues << std::endl;
    gbsa_complex_input_file << "END" << std::endl;

    gbsa_complex_input_file << "END" << std::endl;

    gbsa_complex_input_file.close();
}

void WriteGBSALigandInputFile(std::string gbsa_ligand_input_file_path, int num_complex_residues, int num_receptor_residues){
    std::ofstream gbsa_ligand_input_file(gbsa_ligand_input_file_path);
    if (gbsa_ligand_input_file.fail()){
        std::cout << "Failed to open " << gbsa_ligand_input_file_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_section = R"(File generated by C++
&cntrl
 nsnb=99999, dec_verbose=0, ntb=0,
 surften=0.0072, extdiel=80.0, ncyc=0,
 cut=999.0, gbsa=2, imin=5, idecomp=1,
 igb=2, intdiel=3,
/)";

    gbsa_ligand_input_file << constant_section << std::endl;

    gbsa_ligand_input_file << "Residues considered as LIG" << std::endl;
    gbsa_ligand_input_file << "LRES 1 " << num_complex_residues - num_receptor_residues << std::endl;
    gbsa_ligand_input_file << "END" << std::endl;

    gbsa_ligand_input_file << "Residues to print" << std::endl;
    gbsa_ligand_input_file << "RES 1 " << num_complex_residues - num_receptor_residues << std::endl;
    gbsa_ligand_input_file << "END" << std::endl;

    gbsa_ligand_input_file << "END" << std::endl;

    gbsa_ligand_input_file.close();
}

void WriteGBSAReceptorInputFile(std::string gbsa_receptor_input_file_path, int num_receptor_residues){
    std::ofstream gbsa_receptor_input_file(gbsa_receptor_input_file_path);
    if (gbsa_receptor_input_file.fail()){
        std::cout << "Failed to open " << gbsa_receptor_input_file_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_section = R"(File generated by C++
&cntrl
 nsnb=99999, dec_verbose=0, ntb=0,
 surften=0.0072, extdiel=80.0, ncyc=0,
 cut=999.0, gbsa=2, imin=5, idecomp=1,
 igb=2, intdiel=3,
/)";

    gbsa_receptor_input_file << constant_section << std::endl;

    gbsa_receptor_input_file << "Residues considered as REC" << std::endl;
    gbsa_receptor_input_file << "RRES 1 " << num_receptor_residues << std::endl;
    gbsa_receptor_input_file << "END" << std::endl;

    gbsa_receptor_input_file << "Residues to print" << std::endl;
    gbsa_receptor_input_file << "RES 1 " << num_receptor_residues << std::endl;
    gbsa_receptor_input_file << "END" << std::endl;

    gbsa_receptor_input_file << "END" << std::endl;

    gbsa_receptor_input_file.close();
}

void WriteGBSAGeneralInputFile(std::string gbsa_general_input_file_path){
    std::ofstream gbsa_general_input_file(gbsa_general_input_file_path);
    if (gbsa_general_input_file.fail()){
        std::cout << "Failed to open " << gbsa_general_input_file_path << " for writing." << std::endl;        
        std::exit(1);
    }
    std::string constant_part = R"(File generated by C++
&general
startframe=1, endframe=10000, interval=1,
verbose=2,
/
&gb
igb=2
/
&decomp
idecomp=1
dec_verbose=0
/)"; 

    gbsa_general_input_file << constant_part << std::endl;
    gbsa_general_input_file.close();
}

std::vector<int> DetectBindingSiteWaterOxygens(AtomVector& complex_atoms){
    std::vector<int> water_oxygen_indices;
    
    for (unsigned int i = 0; i < complex_atoms.size(); i++){
        MolecularModeling::Atom* this_atom = complex_atoms[i];
        std::string element = this_atom->GetElementSymbol();
        std::string residue_name = this_atom->GetResidue()->GetName();

        if ((residue_name == "HOH" || residue_name == "WAT") && element == "O"){
            water_oxygen_indices.push_back(i + 1);
        }
    }

    return water_oxygen_indices; 
}

std::vector<std::pair<int, int> > DetectStrandBreaks(ResidueVector& receptor_residues, AtomVector& receptor_atoms){
    std::vector<std::pair<int, int> > strand_breaks;
    int last_residue_index = receptor_residues.size() -1;

    for(unsigned int i = 0; i < last_residue_index; i++){
        MolecularModeling::Residue* this_residue = receptor_residues[i];
        MolecularModeling::Residue* next_residue = receptor_residues[i+1];
        AtomVector this_residue_atoms = this_residue->GetAtoms();
        AtomVector next_residue_atoms = next_residue->GetAtoms();

        for (unsigned int j = 0; j < this_residue_atoms.size(); j++){
            MolecularModeling::Atom* atom = this_residue_atoms[j];

            if (atom->GetName() == "C"){
                for (unsigned int k = 0; k < next_residue_atoms.size(); k++){
                    MolecularModeling::Atom* next_atom = next_residue_atoms[k];

                    if (next_atom->GetName() == "N"){
                        double distance = atom->GetCoordinate()->Distance(next_atom->GetCoordinate());

                        if (distance > 2.0){
                            AtomVector::iterator it1 = std::find(receptor_atoms.begin(), receptor_atoms.end(), atom);
                            int atom_index1 = std::distance(receptor_atoms.begin(), it1) + 1;

                            AtomVector::iterator it2 = std::find(receptor_atoms.begin(), receptor_atoms.end(), next_atom);
                            int atom_index2 = std::distance(receptor_atoms.begin(), it2) + 1;
                            strand_breaks.emplace_back(std::pair<int, int>(atom_index1, atom_index2));
                        }
                    }
                }    
            }
        }
    }
    return strand_breaks;
}

void WriteHydrogenMinimizationInputFile(std::string min_H_in_path){
    std::ofstream hydrogen_minimization_input_file(min_H_in_path);
    if (hydrogen_minimization_input_file.fail()){
        std::cout << "Failed to open " << min_H_in_path << " for writing." << std::endl;
        std::exit(1);
    }

    std::string constant_section = R"(File generated by C++
Constant Pressure Minimization
# Control section
&cntrl
 ntwe = 500, ntwx = 5000, ntpr = 1000,
 dielc = 80, cut = 12.0,
 ntb = 2, pres0 = 1.0, ntp = 1,
 maxcyc = 15000, ntmin = 1, ncyc = 5000, dx0 = 0.01, drms = 0.001,
 ibelly = 0, ntr = 1,
 imin = 1,
 restraint_wt=500.0,
 restraintmask='!@H='
/)";

    hydrogen_minimization_input_file << constant_section << std::endl;
    hydrogen_minimization_input_file.close();

    return;
}

//argv:1, tleap_receptor_pdb; 2, tleap_cocomplex_pdb ; 3, hydrogen min input file 4, min solvent input file ; 5, min all input file ; 6, heating input file ; 7, equilibration restraint input file ; 8. equi unstrained input ; 9 md input
//argv:10, GBSA general input file; 11, GBSA complex input file; 12, GBSA ligand input file; 13, GBSA receptor input file
int main(int argc, char* argv[])
{
    std::string receptor_pdb_path(argv[1]);
    std::string complex_pdb_path(argv[2]);

    MolecularModeling::Assembly receptor_pdb(receptor_pdb_path, gmml::InputFileType::PDB);
    MolecularModeling::Assembly complex_pdb(complex_pdb_path, gmml::InputFileType::PDB);

    AtomVector receptor_atoms = receptor_pdb.GetAllAtomsOfAssembly();
    AtomVector complex_atoms = complex_pdb.GetAllAtomsOfAssembly();

    ResidueVector complex_residues = complex_pdb.GetResidues();
    ResidueVector receptor_residues = receptor_pdb.GetResidues();
    int num_complex_residues = complex_residues.size(); 
    int num_receptor_residues = receptor_residues.size();

    std::pair<int, int> head_n_tail_c_indices = FindHeadNTailC(receptor_pdb);
    std::string min_H_in_path(argv[3]);
    WriteHydrogenMinimizationInputFile(min_H_in_path);

    std::string min_solvent_in_path(argv[4]);
    WriteSolventMinimizationInputFile(min_solvent_in_path, num_complex_residues);

    std::vector<std::pair<int, int> > strand_breaks = DetectStrandBreaks(receptor_residues, receptor_atoms);
    std::vector<int> binding_site_water_oxygen_indices = DetectBindingSiteWaterOxygens(complex_atoms);

    std::string min_all_in_path(argv[5]);
    WriteAllMinimizationInputFile(min_all_in_path, head_n_tail_c_indices, strand_breaks, binding_site_water_oxygen_indices);

    std::string heat_in_path(argv[6]);
    WriteHeatingInputFile(heat_in_path, num_receptor_residues, head_n_tail_c_indices, strand_breaks, binding_site_water_oxygen_indices);

    int num_receptor_atoms = receptor_atoms.size();
    std::vector<std::string> ligand_heavy_atom_restraint_section = ObtainLigandHeavyAtomRestraintSection(num_receptor_atoms, complex_atoms);
    std::string equi_restraint_in_path(argv[7]);
    WriteEquilibrationInputFile(equi_restraint_in_path, num_receptor_residues, complex_pdb, head_n_tail_c_indices, ligand_heavy_atom_restraint_section, strand_breaks, binding_site_water_oxygen_indices, true);

    std::string equi_no_restraint_in_path(argv[8]);
    WriteEquilibrationInputFile(equi_no_restraint_in_path, num_receptor_residues, complex_pdb, head_n_tail_c_indices, ligand_heavy_atom_restraint_section, strand_breaks, binding_site_water_oxygen_indices, false);

    std::string md_input_file_path(argv[9]);
    int num_complex_atoms = complex_atoms.size();
    WriteMDInputFile(md_input_file_path, num_complex_atoms, head_n_tail_c_indices, strand_breaks, binding_site_water_oxygen_indices);

//argv:9, GBSA complex input file; 10, GBSA ligand input file; 11, GBSA receptor input file
    std::string gbsa_general_input_file_path(argv[10]);
    WriteGBSAGeneralInputFile(gbsa_general_input_file_path);
    std::string gbsa_complex_input_file_path(argv[11]);
    WriteGBSAComplexInputFile(gbsa_complex_input_file_path, num_complex_residues, num_receptor_residues);
    std::string gbsa_ligand_input_file_path(argv[12]);
    WriteGBSALigandInputFile(gbsa_ligand_input_file_path, num_complex_residues, num_receptor_residues);
    std::string gbsa_receptor_input_file_path(argv[13]);
    WriteGBSAReceptorInputFile(gbsa_receptor_input_file_path, num_receptor_residues);

}
