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

#include "../glycomimeticTool/vina_bond_by_distance_for_pdb.hpp"
#include "mainparm.cpp"
#include "frcmod.cpp"
#include "mapping.cpp"

#include <fstream>
#include <string>
#include <vector>
#include <map>
typedef std::vector<MolecularModeling::Atom*> AtomVector;

//argv:1, mol2 file; 2, ligand pdb file; 3, ligand pdb2glycam log file; 4,AMBER gaff dat file. 5, Input frcmod from antechamber. 6, RESP charge output file (none if doens't exist)
//7, output frcmod file. 8. Output off file. 9. net charge 
int main(int argc, char* argv[])
{
    std::vector<mol2_atom> mol2_atoms;
    std::vector<std::pair<int, int>> mol2_bonding_indices;
    ParseMol2File(argv[1], mol2_atoms, mol2_bonding_indices);
    
    //Since my surface scanning sometimes puts hydrogens close enough within bonding distance, can't bond by distance again from the predicted ligand structure. Instead, read bonding from 
    MolecularModeling::Assembly ligand_pdb(std::string(argv[2]), gmml::InputFileType::PDB);
    ligand_pdb.SetName("corona");

    std::string resp_charge_output_file_path(argv[6]);
    std::vector<double> resp_charges;
    bool resp_charges_given = ParseRespChargeFile(resp_charge_output_file_path, resp_charges);

    BuildBondFromMol2(ligand_pdb, mol2_bonding_indices, resp_charge_output_file_path);
    AtomVector pdb_atoms = ligand_pdb.GetAllAtomsOfAssembly();

    std::vector<pdb2glycam_entry> pdb2glycam_info;
    bool pdb2glycam_file_given = ParsePdb2GlycamLogFile(argv[3], pdb2glycam_info);

    ApplyGAFFParametersAndCharges(pdb_atoms, mol2_atoms, pdb2glycam_info, resp_charges_given, resp_charges);

    if (pdb2glycam_file_given){
        if (mol2_atoms.size() != pdb2glycam_info.size() || pdb2glycam_info.size() != pdb_atoms.size() || mol2_atoms.size() != pdb2glycam_info.size()){
            std::cout << "Error. Number of atoms in mol2, pdb2glycam log, and pdb file are not equal." << std::endl;
	    std::exit(1);
        }
    }

    std::cout << "Pdb2glycam file given: " << pdb2glycam_file_given << std::endl;
    if (pdb2glycam_file_given){
        std::vector<std::pair<MolecularModeling::Atom*, MolecularModeling::Atom*>> glycam_gaff_bonds = GetGlycamGaffBonds(pdb_atoms, pdb2glycam_info);
        std::map<MolecularModeling::Atom*, double> atom_charge_diff_map;
        OverWriteGAFFParametersWithGLYCAM(pdb_atoms, mol2_atoms, pdb2glycam_info, atom_charge_diff_map, glycam_gaff_bonds, resp_charges_given, resp_charges);

        std::string net_charge_str(argv[9]);
        ChargeAdjustment(net_charge_str, mol2_atoms, pdb_atoms, glycam_gaff_bonds, atom_charge_diff_map, resp_charges_given, resp_charges);

        std::vector<angle> glycam_gaff_angles;
        std::vector<torsion> glycam_gaff_torsions; 
        ProfileGlycamGaffAnglesAndTorsions(glycam_gaff_bonds, glycam_gaff_angles, glycam_gaff_torsions);
        std::vector<torsion> glycam_gaff_improper_torsions = DetectImproperTorsions(pdb_atoms, pdb2glycam_info);

        for (unsigned int i = 0; i < glycam_gaff_improper_torsions.size(); i++){
            std::cout << "Improper: " << glycam_gaff_improper_torsions[i].atom1_->GetName() << "-" << glycam_gaff_improper_torsions[i].atom2_->GetName() << "-" << glycam_gaff_improper_torsions[i].atom3_->GetName() << "-" << glycam_gaff_improper_torsions[i].atom4_->GetName() << std::endl;
        }

        MainParm amber_gaff_dat(argv[4]);
        Frcmod   antechamber_frcmod(argv[5]);

        std::vector<MassLine*> interface_masses;//Leave empty, should be irrelevant
        std::vector<BondLine*> interface_bond_lines;
        std::vector<AngleLine*> interface_angle_lines;
        std::vector<TorsionBlock*> interface_torsions;
        std::vector<TorsionBlock*> interface_improper_torsions;
        SixTwelvePotential* interface_nonbon = NULL;

        MapInterface2GaffParm(glycam_gaff_bonds, glycam_gaff_angles, glycam_gaff_torsions, glycam_gaff_improper_torsions, interface_bond_lines, interface_angle_lines, interface_torsions, 
		              interface_improper_torsions, interface_nonbon, amber_gaff_dat, antechamber_frcmod, pdb_atoms, mol2_atoms);
        Frcmod glycam_gaff_frcmod("Interfacing glycam and gaff", interface_masses, interface_bond_lines, interface_angle_lines, interface_torsions, interface_improper_torsions, interface_nonbon);
        std::string output_frcmod_file = std::string(argv[7]);
        glycam_gaff_frcmod.Write(output_frcmod_file);
    }
    //if pdb2glycam file doesn't exist, just apply RESP charges to each atom.
    else{
        if (pdb_atoms.size() != resp_charges.size()){
            std::cout << "Number of atoms in pdb " << pdb_atoms.size() << " does not match number of resp charges " << resp_charges.size() << std::endl;
            std::exit(1);
        }

        for (unsigned int i = 0; i < pdb_atoms.size(); i++){
            pdb_atoms[i]->MolecularDynamicAtom::SetCharge(resp_charges[i]);
        }
    }


    std::string output_off_file = std::string(argv[8]);
    ligand_pdb.CreateOffFileFromAssembly(output_off_file, 0);
    return 0;
}
