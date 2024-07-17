#ifndef OPEN_VALENCE_DERIVATIVE_MOIETY_HPP 
#define OPEN_VALENCE_DERIVATIVE_MOIETY_HPP

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
#include "includes/InputSet/PdbqtFileSpace/pdbqtatomcard.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtatom.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtbranchcard.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtcompoundcard.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtmodelcard.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtmodelresidueset.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqtrootcard.hpp"
#include "includes/InputSet/PdbqtFileSpace/pdbqttorsionaldofcard.hpp"

#include "includes/utils.hpp"

#include "vina_atom_data.hpp"
#include "utility.hpp"
#include "amber_handling.hpp"
#include "pdb2glycam.hpp"

#include <vector>
#include <string>
#include <iostream>
#include <cmath>
#include <filesystem>

class CoComplex;
class OpenValence;
class DerivativeMoiety;

class DerivativeMoiety{
public:
    //CONSTRUCTOR
    DerivativeMoiety(std::string file_dir_path, std::string moiety_name, int num_threads);
    DerivativeMoiety();

    //ACCESSORS
    std::string GetFilePath();
    std::string GetMoietyName();
    MolecularModeling::Assembly* GetMoietyAssembly();
    AtomVector GetDummyAtoms();
    AtomVector GetRealAtoms();
    std::vector<AtomVector> GetIntraMoietyTorsions();
    MolecularModeling::Atom* GetDummyRingAtom();
    MolecularModeling::Atom* GetDummyOpenValenceAtom();
    MolecularModeling::Atom* GetRealHeadAtom();
    MolecularModeling::Atom* GetRealHeadNeighbor();
    std::map<MolecularModeling::Atom*, std::string> GetInputAtomTypeMap();
    std::map<MolecularModeling::Atom*, double> GetInputAtomChargeMap();
    std::map<MolecularModeling::Atom*, std::string> GetAmberAtomTypeMap();
    std::map<MolecularModeling::Atom*, double> GetAmberAtomChargeMap();
    double GetNetCharge();

    //FUNCTIONS
    void ProcessMoietyRemarks();

    //Free up some memory
    void Free();

private:
    std::string file_path_;
    std::string moiety_name_;
    PdbqtFileSpace::PdbqtFile* moiety_pdbqt_file_ = NULL;
    MolecularModeling::Assembly* moiety_assembly_ = NULL;
    AtomVector dummy_atoms_;
    AtomVector real_atoms_;
    std::vector<AtomVector> intra_moiety_torsions_;
    MolecularModeling::Atom* dummy_ring_atom_ = NULL;
    MolecularModeling::Atom* dummy_open_valence_atom_ = NULL;
    MolecularModeling::Atom* real_head_atom_ = NULL;
    MolecularModeling::Atom* real_head_neighbor_ = NULL;
    std::map<MolecularModeling::Atom*, std::string> atom_ad_type_map_;
    std::map<MolecularModeling::Atom*, double> atom_ad_charge_map_;
    std::map<MolecularModeling::Atom*, std::string> atom_amber_type_map_;
    std::map<MolecularModeling::Atom*, double> atom_amber_charge_map_;
    double net_charge_ = 0;
};

class CoComplex{
public:
    //CONSTRUCTOR
    CoComplex(std::string file_path, std::string gems_home, std::string output_pdb_path, int num_threads);

    //FUNCTIONS
    //void UpdateLigandAtoms();
    void WriteDerivatizedLigandAndReceptorPdbFile(std::string output_path);
    void WriteDerivatizedLigandOffFile();
    void RestoreReceptorPositions();
    void RestoreLigandPositions();
    void WriteDerivatizedLigandPdb2GlycamLogFile(MolecularModeling::Assembly& derivatized_ligand_assembly, std::string filename_no_extension, std::vector<std::string>& old_names);

    //ACCESSOR
    MolecularModeling::Assembly* GetReceptorAssembly();
    AtomVector GetReceptorAtoms();
    AtomVector GetLigandAtoms();
    std::vector<MolecularModeling::Residue*> GetLigandResidues();
    std::vector<Glycan::Monosaccharide*> GetMonosaccharides();
    std::vector<OpenValence*> GetOpenValences();
    MolecularModeling::Assembly* GetCoComplexAssembly();
    std::map<MolecularModeling::Atom*, std::string> GetInputAtomTypeMap();
    std::map<MolecularModeling::Atom*, double> GetInputAtomChargeMap();
    std::map<MolecularModeling::Atom*, std::string> GetAmberAtomTypeMap();
    std::map<MolecularModeling::Atom*, double> GetAmberAtomChargeMap();
    std::map<MolecularModeling::Atom*, AtomVector> GetInputHeavyAtomProtonsMap();
    std::map<MolecularModeling::Atom*, AtomVector> GetAmberHeavyAtomProtonsMap();

    //MUTATOR
    void RemoveLigandAtom(MolecularModeling::Atom* atom);
    void AddLigandAtom(MolecularModeling::Atom* atom);
    void AddLigandResidue(MolecularModeling::Residue* residue);
    void AddOpenValence(OpenValence* open_valence);
    void SetOpenValences(std::vector<OpenValence*> open_valences);

private:
    std::string file_path_;
    MolecularModeling::Assembly* cocomplex_assembly_ = NULL;
    AtomVector receptor_atoms_;
    std::vector<MolecularModeling::Residue*> ligand_residues_;
    std::vector<Glycan::Monosaccharide*> monos_;
    std::vector<OpenValence*> open_valences_;
    std::map<MolecularModeling::Atom*, std::string> atom_ad_type_map_;
    std::map<MolecularModeling::Atom*, double> atom_ad_charge_map_;
    std::map<MolecularModeling::Atom*, std::string> atom_amber_type_map_;
    std::map<MolecularModeling::Atom*, double> atom_amber_charge_map_;
    std::map<MolecularModeling::Atom*, AtomVector> input_heavy_atom_protons_map_;
    std::map<MolecularModeling::Atom*, AtomVector> amber_heavy_atom_protons_map_;
    MolecularModeling::Assembly* receptor_assembly_ = NULL;
    MolecularModeling::Assembly* ligand_assembly_ = NULL;
    std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*> receptor_atoms_initial_position_;
    std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*> ligand_atoms_initial_position_;
    int num_threads_ = 1; 
    std::map<MolecularModeling::Atom*, MolecularModeling::Atom*> pdb_glycam_atom_match_map_;

};

class OpenValence{
public:
    //TYPE_DEFINITION
    typedef std::vector<MolecularModeling::Atom*> AtomVector; 

    //CONSTRUCTOR
    OpenValence(CoComplex* cocomplex, MolecularModeling::Atom* atom, int num_threads, std::string linkage_torsion_atom1, std::string derivatize_type, bool linkage_torsion_rotatable, std::string linkage_torsion_value_str, std::vector<std::string>& explicit_torsion_str, std::vector<std::pair<std::string, std::string> >& explicit_torsion_str_preset, std::string moiety_path, std::string moiety_name_pattern);
    OpenValence();

    //ACCESSORS
    MolecularModeling::Atom* GetOpenValenceAtom();
    std::string GetHybridizationType();
    std::string GetDerivatizeType();
    MolecularModeling::Atom* GetLinkageTorsionAtom1();
    std::vector<AtomVector> GetDefaultTorsions();
    CoComplex* GetCoComplex();
    DerivativeMoiety* GetDerivativeMoiety();
    AtomVector GetLinkageTorsion();
    std::vector<AtomVector> GetRotatableBonds();
    std::vector<std::pair<AtomVector, double> > GetPresetTorsions();
    double GetEntropicPenalty();
    AtomVector GetAllMoietyAtoms();
    std::string GetMoietyPath();
    std::string GetMoietyNamePattern();

    //MUTATORS
    void SetCoComplex(CoComplex* cocomplex);

    //FUNCTIONS
    void ProfileOpenValenceAtomNeighbors(std::string& linkage_torsion_atom1, std::string& atom_to_replace_upon_derivatization);
    void ChangeElementSymbol(std::string new_element);
    void ModifyRingGeometryForSp2SideGroupAtom();
    void ChangeHybridizationType(std::string hybridization_type);
    void Derivatize(DerivativeMoiety* derivative_moiety);
    void RemoveDerivativeMoiety();
    void ProcessExplicitTorsionString(std::vector<std::string>& explicit_torsion_str);
    void ProcessPresetExplicitTorsionString(std::vector<std::pair<std::string, std::string> >& explicit_torsion_str);
    void RestoreMoietyAtomPositions();

private:
    int num_threads_ = 1;
    MolecularModeling::Atom* atom_ = NULL;
    std::string hybridization_type_ = "sp3";
    std::string derivatize_type_ = "hydrogen";
    MolecularModeling::Atom* linkage_torsion_atom1_ = NULL;
    MolecularModeling::Atom* atom_replaced_upon_derivatization_ = NULL;
    std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*> derivative_atoms_initial_coord_;
    DerivativeMoiety* derivative_moiety_ = NULL;
    std::vector<AtomVector> default_torsions_;
    AtomVector downstream_atoms_of_atom_replaced_;
    CoComplex* cocomplex_ = NULL;
    std::vector<AtomVector> explicit_torsions_;
    std::vector<std::pair<AtomVector, double> > explicit_torsions_preset_;
    AtomVector linkage_torsion_;
    //bool linkage_torsion_rotatable_ = true;
    bool linkage_torsion_preset_ = false;
    std::string linkage_torsion_value_str_;
    std::string moiety_path_;
    std::string moiety_name_pattern_;
};

//CONSTRUCTOR
DerivativeMoiety::DerivativeMoiety(std::string file_dir_path, std::string moiety_file_name, int num_threads){
    this->file_path_ = file_dir_path;
    std::cout << "Moiety file name: " << moiety_file_name << std::endl;
    std::string moiety_name = moiety_file_name;
    unsigned int erase_start_pos = moiety_name.find(".pdbqt");
    if (erase_start_pos != std::string::npos){
        moiety_name.erase(moiety_name.find(".pdbqt"), 6);
    }
    this->moiety_name_ = moiety_name;
    std::string full_path = file_dir_path + "/" + moiety_file_name;
    std::cout << "Deri full path: " << full_path << std::endl;

    this->moiety_pdbqt_file_ = new PdbqtFileSpace::PdbqtFile(full_path);
    this->moiety_assembly_ = new MolecularModeling::Assembly(full_path, gmml::InputFileType::PDBQT);

    std::string resp_charge_file_name = moiety_name;
    resp_charge_file_name += "_resp_charges.out";
    std::string resp_charge_full_path = file_dir_path + "/" + resp_charge_file_name; 
    std::cout << "Resp charge full path: " << resp_charge_full_path << std::endl;
    std::ifstream resp_file(resp_charge_full_path);
    bool resp_exists = true;

    if (resp_file.fail()){
        std::cout << "Failed to open " << resp_charge_full_path << std::endl;
        resp_exists = false;
        //std::exit(1);
    }


    //Save autodock type and charge
    AtomVector all_atoms = this->moiety_assembly_->GetAllAtomsOfAssembly();
    for (unsigned int i = 0; i < all_atoms.size(); i++){
        this->atom_ad_type_map_[all_atoms[i]] = all_atoms[i]->MolecularDynamicAtom::GetAtomType();
        this->atom_ad_charge_map_[all_atoms[i]] = all_atoms[i]->MolecularDynamicAtom::GetCharge();
    }

    //Apply RESP charge for R group atoms. 
    std::string charge_str;
    for (unsigned int i = 0; i < all_atoms.size(); i++){
        if (resp_exists){
            resp_file >> charge_str;
            all_atoms[i]->MolecularDynamicAtom::SetCharge(std::stod(charge_str));
        }
        else{
            all_atoms[i]->MolecularDynamicAtom::SetCharge(0.000);
        }
    }
    resp_file.close();

    VinaBondByDistance(*this->moiety_assembly_, vina_atom_data);
    AtomVector moiety_atoms = this->moiety_assembly_->GetAllAtomsOfAssembly();
    DuplicateAtomNodesAndCoordinates (moiety_atoms, num_threads);
    this->ProcessMoietyRemarks();

    //Add head atom for the moiety residue
    this->moiety_assembly_->GetResidues()[0]->AddHeadAtom(this->real_head_atom_);
    this->moiety_assembly_->GetResidues()[0]->AddTailAtom(this->real_head_atom_);

    /*std::string mol2_name = moiety_name + ".mol2";
    std::string mol2_full_path = "/home/yao/GLYCAM_Dev_Env/V_2/Web_Programs/gems/glycomimetics/moieties/mol2/done1/";
    mol2_full_path += mol2_name;
    LoadAmberGaffTypeAndChargeFromMol2(this->moiety_assembly_, mol2_full_path, this->atom_amber_type_map_, this->atom_amber_charge_map_);
    */
}

DerivativeMoiety::DerivativeMoiety(){}

//ACCESSORS
std::string DerivativeMoiety::GetFilePath(){
    return this->file_path_;
}
std::string DerivativeMoiety::GetMoietyName(){
    return this->moiety_name_;
}
double DerivativeMoiety::GetNetCharge(){
    return this->net_charge_;
}
MolecularModeling::Assembly* DerivativeMoiety::GetMoietyAssembly(){
    return this->moiety_assembly_;
}
AtomVector DerivativeMoiety::GetDummyAtoms(){
    return this->dummy_atoms_;
}
AtomVector DerivativeMoiety::GetRealAtoms(){
    return this->real_atoms_;
}
std::vector<AtomVector> DerivativeMoiety::GetIntraMoietyTorsions(){
    return this->intra_moiety_torsions_;
}
MolecularModeling::Atom* DerivativeMoiety::GetDummyRingAtom(){
    return this->dummy_ring_atom_;
}
MolecularModeling::Atom* DerivativeMoiety::GetDummyOpenValenceAtom(){
    return this->dummy_open_valence_atom_;
}
MolecularModeling::Atom* DerivativeMoiety::GetRealHeadAtom(){
    return this->real_head_atom_;
}
MolecularModeling::Atom* DerivativeMoiety::GetRealHeadNeighbor(){
    return this->real_head_neighbor_;
}
std::map<MolecularModeling::Atom*, std::string> DerivativeMoiety::GetInputAtomTypeMap(){
    return this->atom_ad_type_map_;
}
std::map<MolecularModeling::Atom*, double> DerivativeMoiety::GetInputAtomChargeMap(){
    return this->atom_ad_charge_map_;
}
std::map<MolecularModeling::Atom*, std::string> DerivativeMoiety::GetAmberAtomTypeMap(){
    return this->atom_amber_type_map_;
}
std::map<MolecularModeling::Atom*, double> DerivativeMoiety::GetAmberAtomChargeMap(){
    return this->atom_amber_charge_map_;
}

//FUNCTIONS
void DerivativeMoiety::ProcessMoietyRemarks(){
    std::vector<std::string> pdbqt_remark_strs;
    std::vector<std::pair<std::string, std::string> > moiety_remarks_key_value;
    PdbqtFileSpace::PdbqtModel::RemarkCardVector pdbqt_remarks = this->moiety_pdbqt_file_->GetModels()->GetModels().begin()->second->GetRemarks();
    for (unsigned int i = 0; i < pdbqt_remarks.size(); i++){
        pdbqt_remark_strs.push_back(pdbqt_remarks[i]->GetValue());
    }
    for (int i = 0; i < pdbqt_remark_strs.size(); i++){
        if (pdbqt_remark_strs[i].find("=") != std::string::npos){
            //pdbqt_remark_strs[i].erase(0, 6); //Remove "REMARK"
            gmml::Trim(pdbqt_remark_strs[i]);
            std::vector<std::string> equal_sign_split_tokens = gmml::Split(pdbqt_remark_strs[i], "=");
            moiety_remarks_key_value.push_back(std::make_pair(equal_sign_split_tokens[0], equal_sign_split_tokens[1]));
        }
    }

    AtomVector all_moiety_atoms  = this->moiety_assembly_->GetAllAtomsOfAssembly();
    for (int i = 0; i < moiety_remarks_key_value.size(); i++){
        if (moiety_remarks_key_value[i].first == "FAKE_HEAD_ATOM"){
            std::vector<std::string> head_and_neighbor_name = gmml::Split(moiety_remarks_key_value[i].second, "_");
            this->dummy_ring_atom_ = GetAtomByName(head_and_neighbor_name[0], all_moiety_atoms);
            this->dummy_open_valence_atom_ = GetAtomByName(head_and_neighbor_name[1], all_moiety_atoms);
        }
        else if (moiety_remarks_key_value[i].first == "TORSION"){
            std::vector<std::string> additional_torsion_atom_names = gmml::Split(moiety_remarks_key_value[i].second, "_");
            AtomVector torsion_atoms;
            if (additional_torsion_atom_names.size() != 4){
                std::cout << "Error: A torsion consists of exactly 4 atoms, you have " << additional_torsion_atom_names.size() << std::endl;
                std::cout << "Check moiety remarks section" << std::endl;
            }
            else{
                for (unsigned int i = 0; i < 4; i++){
                    torsion_atoms.push_back(GetAtomByName(additional_torsion_atom_names[i], all_moiety_atoms));
                }
                this->intra_moiety_torsions_.push_back(torsion_atoms);
            }
        }
        else if (moiety_remarks_key_value[i].first == "DUMMY_ATOM"){
            std::vector<std::string> dummy_atom_names = gmml::Split(moiety_remarks_key_value[i].second, "_");
            for (unsigned int i = 0; i < dummy_atom_names.size(); i++){
                this->dummy_atoms_.push_back(GetAtomByName(dummy_atom_names[i], all_moiety_atoms));
            }
        }
        else if (moiety_remarks_key_value[i].first == "REAL_HEAD_ATOM"){ //REAL_HEAD_ATOM=C2, for example
            std::vector<std::string> real_head_atom_names = gmml::Split(moiety_remarks_key_value[i].second, "_");
            this->real_head_atom_ = GetAtomByName(real_head_atom_names[0], all_moiety_atoms);
            this->real_head_neighbor_ = GetAtomByName(real_head_atom_names[1], all_moiety_atoms);
        }
	else if (moiety_remarks_key_value[i].first == "NET_CHARGE"){
	    //Right now no net charge entry in the database. Hopefully not needed.
	    this->net_charge_ =  std::stod(moiety_remarks_key_value[i].second);
	}
	else{
            std::cout << "Unknown key: " << moiety_remarks_key_value[i].first << std::endl;
            std::exit(1);
        }
    }

    for (unsigned int k = 0; k < all_moiety_atoms.size(); k++){
        if (std::find(this->dummy_atoms_.begin(), this->dummy_atoms_.end(), all_moiety_atoms[k]) == this->dummy_atoms_.end()){
            this->real_atoms_.push_back(all_moiety_atoms[k]);
        }
    }
	
}

void DerivativeMoiety::Free(){
	//Delete the assembly and all the dynamic object it houses
	std::cout << "Free gets called" << std::endl;
        AtomVector all_atoms = this->moiety_assembly_->GetAllAtomsOfAssembly();
        for (unsigned int i = 0; i < all_atoms.size(); i++){
            std::vector<GeometryTopology::Coordinate*> coords = all_atoms[i]->GetCoordinates();;
            for (unsigned int j = 0; j < coords.size(); j++){
                delete coords[j];
            }
            std::vector<MolecularModeling::AtomNode*> nodes = all_atoms[i]->GetNodes();
            for (unsigned int j = 0; j < nodes.size(); j++){
                delete nodes[j];
            }

            delete all_atoms[i];
        }

	std::vector<MolecularModeling::Residue*> assembly_residues = this->moiety_assembly_->GetResidues();
	for (unsigned int i = 0; i < assembly_residues.size(); i++){
	    delete assembly_residues[i];
	}

	delete this->moiety_assembly_;

        //Delete the pdbqt file object, and all the dynamic object it houses
	PdbqtFileSpace::PdbqtModelCard* model_cards = this->moiety_pdbqt_file_->GetModels();
	std::map<int, PdbqtFileSpace::PdbqtModel*> models = model_cards->GetModels();

	for (std::map<int, PdbqtFileSpace::PdbqtModel*>::iterator mapit = models.begin(); mapit != models.end(); mapit++){
	    PdbqtFileSpace::PdbqtModel* model = mapit->second;
	    PdbqtFileSpace::PdbqtCompoundCard* cmpd_card = model->GetModelCompoundCard();
	    delete cmpd_card;

	    PdbqtFileSpace::PdbqtModelResidueSet* residue_set = model->GetModelResidueSet();
	    PdbqtFileSpace::PdbqtRootCard* root = residue_set->GetRoots();
	    delete root;

	    PdbqtFileSpace::PdbqtModelResidueSet::BranchCardVector branches = residue_set->GetBranches();
	    for (unsigned int i = 0; i < branches.size(); i++){
	        delete branches[i];
	    }

	    PdbqtFileSpace::PdbqtAtomCard* atom_card = residue_set->GetAtoms();
	    //Map contains all atoms
	    PdbqtFileSpace::PdbqtAtomCard::PdbqtAtomMap atom_map = atom_card->GetAtoms();
	    for(PdbqtFileSpace::PdbqtAtomCard::PdbqtAtomMap::iterator mapit = atom_map.begin(); mapit != atom_map.end(); mapit++){
	        delete mapit->second;
	    }

	    delete atom_card;
	    delete residue_set;

            PdbqtFileSpace::PdbqtModel::RemarkCardVector remarks = model->GetRemarks();                           
	    for (unsigned int i = 0; i < remarks.size(); i++){
	        delete remarks[i];
	    }

            PdbqtFileSpace::PdbqtModel::TorsionalDoFCardVector torsdof = model->GetTorsionalDoFCards();                           
	    for (unsigned int i = 0; i < torsdof.size(); i++){
	        delete torsdof[i];
	    }

	    delete model;
	}

	delete model_cards;
	delete this->moiety_pdbqt_file_;
	delete this;
}

//CONSTRUCTOR
CoComplex::CoComplex(std::string file_path, std::string gems_home, std::string output_pdb_path, int num_threads){
    this->num_threads_ = num_threads;
    if (!std::filesystem::is_regular_file(file_path)){
        std::cout << "File " << file_path << "does not exist." << std::endl;
        std::exit(1);
    }
    if (!std::filesystem::is_directory(output_pdb_path)){
        std::cout << "Path " << output_pdb_path << " does not exist." << std::endl;
        std::exit(1);
    }
    this->cocomplex_assembly_ = new MolecularModeling::Assembly(file_path, gmml::InputFileType::PDBQT);

    VinaBondByDistance(*this->cocomplex_assembly_, vina_atom_data);

    AtomVector all_atoms = this->cocomplex_assembly_->GetAllAtomsOfAssembly();
    for (unsigned int i = 0; i < all_atoms.size(); i++){
        this->atom_ad_type_map_[all_atoms[i]] = all_atoms[i]->MolecularDynamicAtom::GetAtomType();
        this->atom_ad_charge_map_[all_atoms[i]] = all_atoms[i]->MolecularDynamicAtom::GetCharge();
    }

    //Initialize heavy atom proton maps
    AtomVector empty_atom_vector;
    for (unsigned int i = 0; i < all_atoms.size(); i++){
        if (all_atoms[i]->GetElementSymbol() != "H"){
            this->input_heavy_atom_protons_map_[all_atoms[i]] = empty_atom_vector;
            this->amber_heavy_atom_protons_map_[all_atoms[i]] = empty_atom_vector;           
        }
    }
    RecordProtonSet(all_atoms, this->input_heavy_atom_protons_map_);

    this->receptor_assembly_ = new MolecularModeling::Assembly();
    this->ligand_assembly_ = new MolecularModeling::Assembly();
    //For now find receptor by check if protein, other atoms are all considered ligand. 
    std::vector<std::string> other_receptor_residue_names = {"CA","HOH", "WAT"};
    std::vector<MolecularModeling::Residue*> assembly_residues = this->cocomplex_assembly_->GetResidues();
    for (unsigned int i = 0; i < assembly_residues.size(); i++){
	std::string resname = assembly_residues[i]->GetName();
        if (assembly_residues[i]->CheckIfProtein() || std::find(other_receptor_residue_names.begin(), other_receptor_residue_names.end(), resname) != other_receptor_residue_names.end()){
            this->receptor_assembly_->AddResidue(assembly_residues[i]);
	    AtomVector protein_residue_atoms = assembly_residues[i]->GetAtoms();
	    for(unsigned int j = 0; j < protein_residue_atoms.size(); j++){
	        this->receptor_atoms_.push_back(protein_residue_atoms[j]);
	    }
        }
	else{
	    this->ligand_residues_.push_back(assembly_residues[i]);
	    this->ligand_assembly_->AddResidue(assembly_residues[i]);
	}
    }

    //Write ligand pdb containing hydrogens
    std::string ligand_pdb_path = output_pdb_path + "/natural_ligand.pdb";
    WritePdbFromAssembly(this->ligand_assembly_, ligand_pdb_path);

    RenameDisulfideCYS2CYX(assembly_residues);

    //Perform pdb2glycam matching
    std::string amino12_lib = gems_home + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/amino12.lib";
    std::string aminoct12_lib = gems_home + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminoct12.lib";
    std::string aminont12_lib = gems_home + "/gmml/dat/CurrentParams/leaprc.ff12SB_2014-04-24/aminont12.lib";
    std::string prep = gems_home + "/gmml/dat/prep/GLYCAM_06j-1.prep";

    std::vector<std::string> amino_libs = {amino12_lib, aminoct12_lib, aminont12_lib};

    //The sugar identification code in monosaccharide.cc is written for non-hydrogenated structure. Must remove H before using pdb2glycam
    pdb2glycam_matching(file_path, this->pdb_glycam_atom_match_map_, all_atoms, gmml::InputFileType::PDBQT, amino_libs, prep);

    std::vector<std::string> old_names;
    AtomVector ligand_atoms = this->GetLigandAtoms();
    for (unsigned int i = 0; i < ligand_atoms.size(); i++){
        old_names.push_back(ligand_atoms[i]->GetName());
    }

    std::string pdb2glycam_log_path = output_pdb_path + "/natural_";

    WriteDerivatizedLigandPdb2GlycamLogFile(*(this->ligand_assembly_), pdb2glycam_log_path, old_names);

    //Write hydrogen-free receptor into a pdb file. Later tleap adds proton
    RemoveProtons(this->receptor_atoms_);
    std::string receptor_pdb_path = output_pdb_path + "/natural_receptor.pdb";
    WritePdbFromAssembly(this->receptor_assembly_, receptor_pdb_path);
    ApplyProtonSet(all_atoms, this->input_heavy_atom_protons_map_); //Need to add proton set back for CH-pi 

    DuplicateAtomNodesAndCoordinates (ligand_atoms, num_threads);
    //LoadAmberProteinTypeAndCharge(this->cocomplex_assembly_, this->atom_amber_type_map_, this->atom_amber_charge_map_, this->amber_heavy_atom_protons_map_);

    //Store the starting position of all atoms. After each grid searching, restore. 
    for (unsigned int i = 0; i < this->receptor_atoms_.size(); i++){
	MolecularModeling::Atom* receptor_atom = this->receptor_atoms_[i];
        GeometryTopology::Coordinate* new_coord = new GeometryTopology::Coordinate(receptor_atom->GetCoordinate());
	this->receptor_atoms_initial_position_[receptor_atom] = new_coord;
    }

    for (unsigned int i = 0; i < ligand_atoms.size(); i++){
	MolecularModeling::Atom* ligand_atom = ligand_atoms[i];
        GeometryTopology::Coordinate* new_coord = new GeometryTopology::Coordinate(ligand_atom->GetCoordinate());
	this->ligand_atoms_initial_position_[ligand_atom] = new_coord;
    }

}

void CoComplex::WriteDerivatizedLigandAndReceptorPdbFile(std::string output_path){

	//Rename all ligand residues to "LIG" and set them into a single residue number. So they appear to be a single residue
    MolecularModeling::Assembly derivatized_ligand_assembly;
    AtomVector ligand_atoms_with_old_protons = this->GetLigandAtoms();
    AtomVector ligand_atoms = this->GetLigandAtoms();

    derivatized_ligand_assembly.SetResidues(this->ligand_residues_);

    std::string pdb_file_name = output_path + "/";
    std::string receptor_pdb_file_name = output_path + "/";

    //Make sure all derivative moieties apply Amber charge and type for writing derivatized ligand pdb file.

    for(unsigned int i = 0; i < this->open_valences_.size(); i++){
        DerivativeMoiety* derivative_moiety = this->open_valences_[i]->GetDerivativeMoiety();
        if (derivative_moiety != NULL){
            pdb_file_name += derivative_moiety->GetMoietyName();
	    	pdb_file_name += "_";
	    	receptor_pdb_file_name += derivative_moiety->GetMoietyName();
	    	receptor_pdb_file_name += "_";
            MolecularModeling::Residue* moiety_residue = derivative_moiety->GetMoietyAssembly()->GetResidues()[0];
            derivatized_ligand_assembly.AddResidue(moiety_residue);
	    	std::cout << "Derivatized ligand residue added residue " << moiety_residue->GetName() << std::endl; 
        }
    }

    ReorderAtomsForZMatrix(derivatized_ligand_assembly);

    //Store old atom names
    std::vector<std::string> old_names;
    //Rename ligand atoms to element symbol plus index
    AtomVector ligand_assembly_atoms = derivatized_ligand_assembly.GetAllAtomsOfAssembly();

    for (unsigned int i = 0; i < ligand_assembly_atoms.size(); i++){
		old_names.push_back(ligand_assembly_atoms[i]->GetName());
        std::stringstream new_name;
        new_name << ligand_assembly_atoms[i]->GetElementSymbol() << i+1;
        ligand_assembly_atoms[i]->SetName(new_name.str());
    }

    this->WriteDerivatizedLigandPdb2GlycamLogFile(derivatized_ligand_assembly, pdb_file_name, old_names);

    //pdb_file_name.erase(pdb_file_name.size()-1); //Remove last "_"
    pdb_file_name+="ligand.pdb";
    receptor_pdb_file_name+="receptor.pdb";

    PdbFileSpace::PdbFile *outputPdbFile = derivatized_ligand_assembly.BuildPdbFileStructureFromAssembly();
    outputPdbFile->Write(pdb_file_name);

    //Restore old names
    for (unsigned int i = 0; i < ligand_assembly_atoms.size(); i++){
        ligand_assembly_atoms[i]->SetName(old_names[i]);
    }

    AtomVector receptor_assembly_atoms = this->receptor_assembly_->GetAllAtomsOfAssembly();

    //Write hydrogen-free receptor protein. Let tleap protonate. 
    RemoveProtons(receptor_assembly_atoms);

    this->receptor_assembly_->BuildPdbFileStructureFromAssembly()->Write(receptor_pdb_file_name);

    ApplyProtonSet(receptor_assembly_atoms, this->input_heavy_atom_protons_map_);

    std::cout << "exit writing" << std::endl;
}

void CoComplex::WriteDerivatizedLigandPdb2GlycamLogFile(MolecularModeling::Assembly& derivatized_ligand_assembly, std::string filename_no_extension, std::vector<std::string>& old_names){
    filename_no_extension += "pdb2glycam.log";
    std::ofstream pdb2glycam_log(filename_no_extension);
    pdb2glycam_log << std::left << std::setw(10) << "OLDNAME" << std::setw(10) << "RENAMED" << std::setw(10) << "IFGLYCAM" << std::setw(10) << "G_TYPE" << std::setw(10) << "G_CHARGE" << std::endl;

    AtomVector analog_atoms = derivatized_ligand_assembly.GetAllAtomsOfAssembly();
    for (unsigned int i = 0; i < analog_atoms.size(); i++){
        MolecularModeling::Atom* this_atom = analog_atoms[i];
	    pdb2glycam_log << std::left << std::setw(10) << old_names[i] << std::setw(10) << this_atom->GetName(); 

	    //If this atom is among the natural sugar that's successfully matched by pdb2glycam, apply pdb2glycam parameters
        if (this->pdb_glycam_atom_match_map_.find(this_atom) != this->pdb_glycam_atom_match_map_.end()){
	    MolecularModeling::Atom* glycam_atom = this->pdb_glycam_atom_match_map_[this_atom];
	    std::string type = glycam_atom->MolecularDynamicAtom::GetAtomType();
	    double charge = glycam_atom->MolecularDynamicAtom::GetCharge();

            pdb2glycam_log << std::left << std::setw(10) << "YES" << std::setw(10) << type << std::setw(10) << std::fixed << std::setprecision(4) << charge << std::endl;
	}
        else {  //If not, write NONE to the parameters
            double charge = this_atom->MolecularDynamicAtom::GetCharge();
            pdb2glycam_log << std::left << std::setw(10) << "NO" << std::setw(10) << "NONE" << std::setw(10) << std::fixed << std::setprecision(4) << charge << std::endl;
	}	
    }

    pdb2glycam_log.close();
}

void CoComplex::WriteDerivatizedLigandOffFile(){
    /*MolecularModeling::Assembly derivatized_ligand_assembly;
    derivatized_ligand_assembly.SetName("CORONA");

    AtomVector ligand_atoms_with_old_protons = this->GetLigandAtoms();
    //RemoveProtons(ligand_atoms_with_old_protons);

    //Make sure the natural ligand apply Amber proton set, charge and type for writing derivatized ligand off file.
    //ApplyProtonSet(ligand_atoms_with_old_protons, this->amber_heavy_atom_protons_map_);
    //ApplyAtomTypeAndChargeSet(this->atom_amber_type_map_, this->atom_amber_charge_map_);

    AtomVector ligand_atoms = this->GetLigandAtoms();

    derivatized_ligand_assembly.SetResidues(this->ligand_residues_);
    //double natural_ligand_net_charge = GetNetChargeOfResidues(this->ligand_residues_);
    //std::cout << "Natural ligand net charge: " << natural_ligand_net_charge << std::endl;

    std::string offfile_name; 
    //Make sure all derivative moieties apply Amber charge and type for writing derivatized ligand off file.
    for(unsigned int i = 0; i < this->open_valences_.size(); i++){
        DerivativeMoiety* derivative_moiety = this->open_valences_[i]->GetDerivativeMoiety();
	offfile_name += derivative_moiety->GetMoietyName();
        MolecularModeling::Residue* moiety_residue = derivative_moiety->GetMoietyAssembly()->GetResidues()[0];
        derivatized_ligand_assembly.AddResidue(moiety_residue);

	double moiety_net_charge = derivative_moiety->GetNetCharge();
	std::cout << "Moiety net charge is: " << moiety_net_charge << std::endl;

	std::map<MolecularModeling::Atom*, std::string> moiety_amber_atom_type_map = derivative_moiety->GetAmberAtomTypeMap();
	std::map<MolecularModeling::Atom*, double> moiety_amber_atom_charge_map = derivative_moiety->GetAmberAtomChargeMap();

	//ApplyAtomTypeAndChargeSet(moiety_amber_atom_type_map, moiety_amber_atom_charge_map);

	//Adjust charges
	AtomVector ligand_and_derivative_atoms = ligand_atoms;
	AtomVector moiety_real_atoms = derivative_moiety->GetRealAtoms();
	ligand_and_derivative_atoms.insert(ligand_and_derivative_atoms.end(), moiety_real_atoms.begin(), moiety_real_atoms.end());

	double total_charge = 0; 
	for (unsigned int j = 0; j < ligand_and_derivative_atoms.size(); j++){
	    MolecularModeling::Atom* atom = ligand_and_derivative_atoms[j];
	    total_charge+=atom->MolecularDynamicAtom::GetCharge();
	}
	double open_valence_charge = this->open_valences_[i]->GetOpenValenceAtom()->MolecularDynamicAtom::GetCharge();
	std::cout << "Ligand moiety total net charge: " << moiety_net_charge + natural_ligand_net_charge  << " and total real atoms charge " << total_charge << " and open valence charge " << open_valence_charge << std::endl;

	open_valence_charge += (moiety_net_charge + natural_ligand_net_charge - total_charge);
	this->open_valences_[i]->GetOpenValenceAtom()->MolecularDynamicAtom::SetCharge(open_valence_charge);

    }

    offfile_name += ".off";
    derivatized_ligand_assembly.CreateOffFileFromAssembly(offfile_name, 0);

    //Write tleap input file
    std::string tleap_input_name = "tleap_";
    for(unsigned int i = 0; i < this->open_valences_.size(); i++){
        DerivativeMoiety* derivative_moiety = this->open_valences_[i]->GetDerivativeMoiety();
	tleap_input_name += derivative_moiety->GetMoietyName();
    }
    tleap_input_name += ".in";
    std::ofstream tleap_input(tleap_input_name);

    tleap_input << "source leaprc.GLYCAM_06j-1" << std::endl;
    tleap_input << "source leaprc.protein.ff14SB" << std::endl;
    tleap_input << "source leaprc.gaff" << std::endl << std::endl;

    tleap_input << "receptor = loadpdb receptor.pdb" << std::endl;
    tleap_input << "derivatized_ligand = loadOff " << offfile_name << std::endl;
    tleap_input << "cocomplex = combine {receptor derivatized_ligand}" << std::endl << std::endl;

    tleap_input << "addIons cocomplex Na+ 0" << std::endl;
    tleap_input << "addIons cocomplex Cl- 0" << std::endl << std::endl;

    tleap_input << "solvateoct cocomplex TIP3PBOX 10.0 iso" << std::endl;
    tleap_input << "saveamberparm cocomplex cocomplex.prmtop cocomplex.rst7" << std::endl;
    tleap_input << "quit" << std::endl;  

    tleap_input.close();*/
}

void CoComplex::RestoreLigandPositions(){
    for (std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*>::iterator mapit = this->ligand_atoms_initial_position_.begin(); mapit != this->ligand_atoms_initial_position_.end(); mapit++){
	MolecularModeling::Atom* this_atom = mapit->first;
	GeometryTopology::Coordinate* old_coord = mapit->second;

        for (unsigned int j = 0; j < this->num_threads_; j++){
            this_atom->GetCoordinates()[j]->SetX(old_coord->GetX());	
            this_atom->GetCoordinates()[j]->SetY(old_coord->GetY());	
            this_atom->GetCoordinates()[j]->SetZ(old_coord->GetZ());	
	}
    }
}

void CoComplex::RestoreReceptorPositions(){
    for (std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*>::iterator mapit = this->receptor_atoms_initial_position_.begin(); mapit != this->receptor_atoms_initial_position_.end(); mapit++){
        MolecularModeling::Atom* this_atom = mapit->first;
        GeometryTopology::Coordinate* old_coord = mapit->second;

        this_atom->GetCoordinate()->SetX(old_coord->GetX());
        this_atom->GetCoordinate()->SetY(old_coord->GetY());
        this_atom->GetCoordinate()->SetZ(old_coord->GetZ());
    }
}

//ACCESSOR
MolecularModeling::Assembly* CoComplex::GetReceptorAssembly(){
    return this->receptor_assembly_;
}
AtomVector CoComplex::GetReceptorAtoms(){
    return this->receptor_atoms_;
}
AtomVector CoComplex::GetLigandAtoms(){
    AtomVector ligand_atoms;
    for(unsigned int i = 0 ; i < this->ligand_residues_.size(); i++){
        AtomVector residue_atoms = this->ligand_residues_[i]->GetAtoms();
	ligand_atoms.insert(ligand_atoms.end(), residue_atoms.begin(), residue_atoms.end());
    }
    return ligand_atoms;
    //return this->ligand_atoms_;
}
std::vector<MolecularModeling::Residue*> CoComplex::GetLigandResidues(){
    return this->ligand_residues_;
}
std::vector<Glycan::Monosaccharide*> CoComplex::GetMonosaccharides(){
    return this->monos_;
}
std::vector<OpenValence*> CoComplex::GetOpenValences(){
    return this->open_valences_;
}
MolecularModeling::Assembly* CoComplex::GetCoComplexAssembly(){
    return this->cocomplex_assembly_;
}
std::map<MolecularModeling::Atom*, std::string> CoComplex::GetInputAtomTypeMap(){
    return this->atom_ad_type_map_;
}
std::map<MolecularModeling::Atom*, double> CoComplex::GetInputAtomChargeMap(){
    return this->atom_ad_charge_map_;
}
std::map<MolecularModeling::Atom*, std::string> CoComplex::GetAmberAtomTypeMap(){
    return this->atom_amber_type_map_;
}
std::map<MolecularModeling::Atom*, double> CoComplex::GetAmberAtomChargeMap(){
    return this->atom_amber_charge_map_;
}
std::map<MolecularModeling::Atom*, AtomVector> CoComplex::GetInputHeavyAtomProtonsMap(){
    return this->input_heavy_atom_protons_map_;
}
std::map<MolecularModeling::Atom*, AtomVector> CoComplex::GetAmberHeavyAtomProtonsMap(){
    return this->amber_heavy_atom_protons_map_;
}
//MUTATOR
/*void CoComplex::RemoveLigandAtom(MolecularModeling::Atom* atom){
    AtomVector::iterator atom_position = std::find(this->ligand_atoms_.begin(), this->ligand_atoms_.end(), atom);
    if (atom_position != this->ligand_atoms_.end()){
        this->ligand_atoms_.erase(atom_position);
    }
}*/
/*void CoComplex::AddLigandAtom(MolecularModeling::Atom* atom){
    if (std::find(this->ligand_atoms_.begin(), this->ligand_atoms_.end(), atom) == this->ligand_atoms_.end()){
        this->ligand_atoms_.push_back(atom);
    }
}*/
void CoComplex::AddLigandResidue(MolecularModeling::Residue* residue){
    this->ligand_residues_.push_back(residue);
}
void CoComplex::AddOpenValence(OpenValence* open_valence){
    this->open_valences_.push_back(open_valence);
}
void CoComplex::SetOpenValences(std::vector<OpenValence*> open_valences){
    this->open_valences_ = open_valences;
}


//CONSTRUCTOR
OpenValence::OpenValence(CoComplex* cocomplex, MolecularModeling::Atom* atom, int num_threads, std::string linkage_torsion_atom1, std::string derivatize_type, bool linkage_torsion_preset, std::string linkage_torsion_value_str, std::vector<std::string>& explicit_torsion_str, std::vector<std::pair<std::string, std::string> >& explicit_torsion_str_preset, std::string moiety_path, std::string moiety_name_pattern){
    this->cocomplex_ = cocomplex;
    cocomplex->AddOpenValence(this);
    this->num_threads_ = num_threads;
    this->atom_ = atom;
    this->derivatize_type_ = derivatize_type;
    this->moiety_path_ = moiety_path;
    this->moiety_name_pattern_ = moiety_name_pattern;
    this->ProfileOpenValenceAtomNeighbors(linkage_torsion_atom1, derivatize_type);

    this->linkage_torsion_preset_ = linkage_torsion_preset;
    if (linkage_torsion_preset){
	this->linkage_torsion_value_str_ = linkage_torsion_value_str;
    }

    ProcessExplicitTorsionString(explicit_torsion_str);
    ProcessPresetExplicitTorsionString(explicit_torsion_str_preset);
}

OpenValence::OpenValence(){}

//ACCESSORS
MolecularModeling::Atom* OpenValence::GetOpenValenceAtom(){
    return this->atom_;
}
std::string OpenValence::GetHybridizationType(){
    return this->hybridization_type_;
}
std::string OpenValence::GetDerivatizeType(){
    return this->derivatize_type_;
}
MolecularModeling::Atom* OpenValence::GetLinkageTorsionAtom1(){
    return this->linkage_torsion_atom1_;
}
std::vector<AtomVector> OpenValence::GetDefaultTorsions(){
    return this->default_torsions_;
}
CoComplex* OpenValence::GetCoComplex(){
    return this->cocomplex_;
}
DerivativeMoiety* OpenValence::GetDerivativeMoiety(){
    return this->derivative_moiety_;
}
AtomVector OpenValence::GetLinkageTorsion(){
    return this->linkage_torsion_;
}
std::vector<AtomVector> OpenValence::GetRotatableBonds(){
    std::vector<AtomVector> rotatable_bonds;

    //First insert user-assigned explicit torsion
    rotatable_bonds.insert(rotatable_bonds.end(), this->explicit_torsions_.begin(), this->explicit_torsions_.end());
    //Second insert linkage torsion associated with this open valence, if user specifies it as rotatable
    if (this->linkage_torsion_.size() == 4 && !this->linkage_torsion_preset_){
        rotatable_bonds.push_back(this->linkage_torsion_);
    }

    //Finally, insert intra-secondary moiety torsions. 
    if (this->derivative_moiety_ != NULL){
        std::vector<AtomVector> intra_2nd_moiety_torsions = this->derivative_moiety_->GetIntraMoietyTorsions();
        rotatable_bonds.insert(rotatable_bonds.end(), intra_2nd_moiety_torsions.begin(), intra_2nd_moiety_torsions.end());
    }

    return rotatable_bonds;
}
std::vector<std::pair<AtomVector, double> > OpenValence::GetPresetTorsions(){
    return this->explicit_torsions_preset_;
}
double OpenValence::GetEntropicPenalty(){
    std::vector<AtomVector> rotatable_bonds = this->GetRotatableBonds();
    int num_states_fold_reduction = std::pow(3, rotatable_bonds.size());
    double inverse_fold_reduction = (double) 1 / num_states_fold_reduction;
    //S=k*lnW, T=298k(25degs), k = 0.0019872041(kcal/mol), penalty = -TdS
    return (double) (-1) * 298 * 0.0019872041 * std::log(inverse_fold_reduction);
}

AtomVector OpenValence::GetAllMoietyAtoms(){
    AtomVector all_moiety_atoms;

    DerivativeMoiety* secondary_moiety = this->derivative_moiety_;
    if (secondary_moiety != NULL){
        AtomVector secondary_moiety_atoms = secondary_moiety->GetRealAtoms();
	all_moiety_atoms.insert(all_moiety_atoms.end(), secondary_moiety_atoms.begin(), secondary_moiety_atoms.end());
    }
    return all_moiety_atoms;
}

std::string OpenValence::GetMoietyPath(){
    return this->moiety_path_;
}
std::string OpenValence::GetMoietyNamePattern(){
    return this->moiety_name_pattern_;
}

//MUTATORS
void OpenValence::SetCoComplex(CoComplex* cocomplex){
    this->cocomplex_ = cocomplex;
}

//FUNCTIONS
void OpenValence::ProfileOpenValenceAtomNeighbors(std::string& linkage_torsion_atom1, std::string& atom_to_replace_upon_derivatization){
    AtomVector open_valence_atom_intra_residue_neighbor = this->atom_->GetNode()->GetNodeNeighbors();
    this->linkage_torsion_atom1_ = GetAtomByName(linkage_torsion_atom1, open_valence_atom_intra_residue_neighbor);
    this->atom_replaced_upon_derivatization_ = GetAtomByName(atom_to_replace_upon_derivatization, open_valence_atom_intra_residue_neighbor);

    this->downstream_atoms_of_atom_replaced_.push_back(this->atom_); //Temporarily add to prevent backward recursion.Remove after function call.
    this->atom_replaced_upon_derivatization_->FindConnectedAtoms(this->downstream_atoms_of_atom_replaced_, 0);
    this->downstream_atoms_of_atom_replaced_.erase(this->downstream_atoms_of_atom_replaced_.begin()); //Remove open valence atom since we're not actually going to remove it.

    return;
}

void OpenValence::RestoreMoietyAtomPositions(){
    for(std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*>::iterator mapit = this->derivative_atoms_initial_coord_.begin(); mapit != this->derivative_atoms_initial_coord_.end(); mapit++){
        MolecularModeling::Atom* moiety_atom = mapit->first;
	GeometryTopology::Coordinate* initial_coordinate = mapit->second;
	for (unsigned int j = 0; j < this->num_threads_; j++){
	    moiety_atom->GetCoordinates()[j]->SetX(initial_coordinate->GetX());
	    moiety_atom->GetCoordinates()[j]->SetY(initial_coordinate->GetY());
	    moiety_atom->GetCoordinates()[j]->SetZ(initial_coordinate->GetZ());
	}
    }
}

void OpenValence::ChangeElementSymbol(std::string new_element){
    //Change atom element symbol
    this->atom_->SetElementSymbol(new_element);
    //Replace the 1st character of atom name with the new element type
    std::string new_name = this->atom_->GetName();
    new_name.replace(0, 1, new_element);
    this->atom_->SetName(new_name);
}

void OpenValence::ModifyRingGeometryForSp2SideGroupAtom(){}

void OpenValence::ChangeHybridizationType(std::string hybridization_type){
    this->hybridization_type_ = hybridization_type;
    if (hybridization_type == "sp2"){
        this->ModifyRingGeometryForSp2SideGroupAtom();
    }
}

void OpenValence::Derivatize(DerivativeMoiety* derivative_moiety){

    if (this->atom_replaced_upon_derivatization_ == NULL){
        std::cout << "Cannot find atom " << this->derivatize_type_ << " within the neighbors of open valence atom to replace. Exiting" << std::endl;
        std::exit(1);
    }

    //Make sure the natural ligand and the receptor applies Autodock proton set, charge and type for virtual screening.
    AtomVector ligand_atoms =  this->cocomplex_->GetLigandAtoms();
    AtomVector receptor_atoms =  this->cocomplex_->GetReceptorAtoms();
    std::map<MolecularModeling::Atom*, std::string> ad_type_map = this->cocomplex_->GetInputAtomTypeMap();
    std::map<MolecularModeling::Atom*, double> ad_charge_map = this->cocomplex_->GetInputAtomChargeMap();
    std::map<MolecularModeling::Atom*, AtomVector> ad_proton_map = this->cocomplex_->GetInputHeavyAtomProtonsMap();

    AtomVector residue_tail_atoms = this->atom_->GetResidue()->GetTailAtoms();
    if (std::find(residue_tail_atoms.begin(), residue_tail_atoms.end(), this->atom_) == residue_tail_atoms.end()){
        this->atom_->GetResidue()->AddTailAtom(this->atom_);
    }

    this->derivative_moiety_ = derivative_moiety;
    MolecularModeling::Atom* dummy_ring_atom = derivative_moiety->GetDummyRingAtom();
    MolecularModeling::Atom* dummy_open_valence = derivative_moiety->GetDummyOpenValenceAtom();
    MolecularModeling::Atom* moiety_head_atom = derivative_moiety->GetRealHeadAtom();
    MolecularModeling::Atom* moiety_head_atom_neighbor = derivative_moiety->GetRealHeadNeighbor();
    AtomVector dummy_atoms = derivative_moiety->GetDummyAtoms();

    //std::vector<AtomVector> intra_moiety_torsions = derivative_moiety->GetIntraMoietyTorsions();
    AtomVector linkage_torsion;
    linkage_torsion.push_back(this->linkage_torsion_atom1_);
    linkage_torsion.push_back(this->atom_);
    linkage_torsion.push_back(moiety_head_atom);
    linkage_torsion.push_back(moiety_head_atom_neighbor);

    this->linkage_torsion_ = linkage_torsion;

    if (this->linkage_torsion_preset_){
        double preset_val = std::stod(this->linkage_torsion_value_str_);
        this->explicit_torsions_preset_.emplace_back(std::make_pair(linkage_torsion, preset_val));
    }


    MolecularModeling::Assembly moiety_assembly = *(derivative_moiety->GetMoietyAssembly());
    for (unsigned int j = 0; j < this->num_threads_; j++){
        GraftMoietyAndRemoveDummyAtoms(this->linkage_torsion_atom1_, dummy_ring_atom, this->atom_, dummy_open_valence, moiety_head_atom, moiety_assembly, j);
    }

    //Make sure the newly formed bond aligns with the bond that's replaced, to avoid weird geometry.
    for (unsigned int i = 0; i < this->num_threads_; i++){
        SetAngle(this->atom_replaced_upon_derivatization_, this->atom_, moiety_head_atom, 0, i);
    }

    //Adjust all torsions fixed manually by user to the target value
    for (unsigned int i = 0; i < this->explicit_torsions_preset_.size(); i++){
        AtomVector& this_torsion = this->explicit_torsions_preset_[i].first;
        double& this_prset_value = this->explicit_torsions_preset_[i].second;

        std::cout << "Preset tors " << this_torsion[0]->GetName() << "-" << this_torsion[1]->GetName() << "-" << this_torsion[2]->GetName() << "-" << this_torsion[3]->GetName() << " set to " << this_prset_value << std::endl;
        for (unsigned int j = 0; j < this->num_threads_; j++){
            SetDihedral(this_torsion[0], this_torsion[1], this_torsion[2], this_torsion[3], this_prset_value, j);
        }
    }


    //Save the coordinates of the moiety atoms right after grafting for restoring later if necessary.
    AtomVector all_moiety_atoms = moiety_assembly.GetAllAtomsOfAssembly();
    for (unsigned int i = 0; i < all_moiety_atoms.size(); i++){
        this->derivative_atoms_initial_coord_[all_moiety_atoms[i]] = new GeometryTopology::Coordinate(all_moiety_atoms[i]->GetCoordinate());
    }

    MolecularModeling::Residue* moiety_residue = moiety_assembly.GetResidues()[0];
    this->cocomplex_->GetCoComplexAssembly()->InsertResidue(this->atom_->GetResidue(),moiety_residue);

    //Now remove dummy atoms in the moiety
    for (unsigned int k = 0; k < dummy_atoms.size(); k++){
        moiety_residue->RemoveAtom(dummy_atoms[k], false);
    }

    //Finally, temporarily remove the atom, as well as its downstream atoms, that's replaced by derivatization
    for (unsigned int i = 0; i < this->downstream_atoms_of_atom_replaced_.size(); i++){
        this->atom_->GetResidue()->RemoveAtom(this->downstream_atoms_of_atom_replaced_[i], false);
    }


}

void OpenValence::RemoveDerivativeMoiety(){

    this->atom_->GetResidue()->RemoveTailAtom(this->atom_);

    //Remove Derivative residue from the cocomplex assembly.
    MolecularModeling::Assembly* moiety_assembly = this->derivative_moiety_->GetMoietyAssembly();
    MolecularModeling::Residue* moiety_residue = moiety_assembly->GetResidues()[0];
    this->cocomplex_->GetCoComplexAssembly()->RemoveResidue(moiety_residue);

    //Remove the bond between open valence atom on the cocomplex and the head atom of the moiety.
    MolecularModeling::Atom* moiety_head_atom = this->derivative_moiety_->GetRealHeadAtom();
    std::vector<MolecularModeling::AtomNode*> open_valence_nodes = this->atom_->GetNodes();
    std::vector<MolecularModeling::AtomNode*> moiety_head_nodes = moiety_head_atom->GetNodes();
    for (unsigned int i = 0; i < this->num_threads_; i++){
        open_valence_nodes[i]->RemoveNodeNeighbor(moiety_head_atom);
        moiety_head_nodes[i]->RemoveNodeNeighbor(this->atom_);
    }
        

    //Next, restore the derivatized atoms. 
    if (this->atom_replaced_upon_derivatization_ != NULL){
        AtomVector existing_atoms_in_ligand_residue = this->atom_->GetResidue()->GetAtoms();

        for (unsigned int i = 0; i < this->downstream_atoms_of_atom_replaced_.size(); i++){
            this->atom_->GetResidue()->AddAtom(this->downstream_atoms_of_atom_replaced_[i]);
        }

    }

    //For now, do not restore. Need the changes in the final best complex sturcture. 
    this->cocomplex_->RestoreReceptorPositions();
    this->cocomplex_->RestoreLigandPositions();

    //Remove the saved initial coordinates of the moiety atoms and free up the corresponding memory.
    for(std::map<MolecularModeling::Atom*, GeometryTopology::Coordinate*>::iterator mapit = this->derivative_atoms_initial_coord_.begin(); mapit != this->derivative_atoms_initial_coord_.end(); mapit++){
        delete mapit->second;
    }
    this->derivative_atoms_initial_coord_.clear();

    //Empty the default torsions, since that's related to the head atoms of the moiety.Also remove linkage torsion from explicit torsions preset, if exists.
    AtomVector moiety_atoms = this->derivative_moiety_->GetRealAtoms();
    if (this->linkage_torsion_preset_){
	//Check if this preset torsion contains moiety atoms. If so, must be linkage torsion, remove.
        for (std::vector<std::pair<AtomVector, double> >::iterator it = this->explicit_torsions_preset_.begin(); it != this->explicit_torsions_preset_.end(); it++){
            AtomVector& preset_tor = it->first;
	    bool is_linkage = false;
	    for (unsigned int i = 0; i < preset_tor.size(); i++){
	        if (std::find(moiety_atoms.begin(), moiety_atoms.end(), preset_tor[i]) != moiety_atoms.end()){
		    this->explicit_torsions_preset_.erase(it);
		    is_linkage = true;
                    break;
		}
	    }

	    if (is_linkage){
	        break;
	    }
        }
    }
    this->linkage_torsion_.clear();

    //Now restore the dummy atoms of the moiety. They need to be reused for alignment next time.     
    AtomVector moiety_dummy_atoms = this->derivative_moiety_->GetDummyAtoms();
    //Add all dummy atoms back to moiety residue
    for (unsigned int i = 0; i < moiety_dummy_atoms.size(); i++){
        moiety_residue->AddAtom(moiety_dummy_atoms[i]);
    }

    //Free up some memory of the derivative class
    this->derivative_moiety_->Free();
    //Finally, set this->derivative_moiety_ to NULL
    this->derivative_moiety_ = NULL;
    //this->atom_replaced_upon_derivatization_ = NULL;
}

void OpenValence::ProcessExplicitTorsionString(std::vector<std::string>& explicit_torsion_str){
    //AtomVector open_valence_residue_atoms = this->atom_->GetResidue()->GetAtoms();
    ResidueVector natural_ligand_residues = this->GetCoComplex()->GetLigandResidues();
    for (unsigned int i = 0; i < explicit_torsion_str.size(); i++){
        std::vector<std::string> underscore_split_tokens = gmml::Split(explicit_torsion_str[i], "_");
        std::string& residue_index = underscore_split_tokens[0];
	    AtomVector torsion;

	    for (unsigned int j = 1; j < 5; j++){
	        std::string& atom_name = underscore_split_tokens[j];
	        torsion.push_back(GetAtomByResidueIndexAndAtomName(residue_index, atom_name, natural_ligand_residues)); 
	    }
	    this->explicit_torsions_.push_back(torsion);
    }
    return;

}

void OpenValence::ProcessPresetExplicitTorsionString(std::vector<std::pair<std::string, std::string> >& explicit_torsion_str_preset){
    //AtomVector open_valence_residue_atoms = this->atom_->GetResidue()->GetAtoms();
    ResidueVector natural_ligand_residues = this->GetCoComplex()->GetLigandResidues();
    for (unsigned int i = 0; i < explicit_torsion_str_preset.size(); i++){
        std::pair<std::string, std::string>& preset_torsion_value_pair = explicit_torsion_str_preset[i];

        if (preset_torsion_value_pair.first == "link"){
            this->linkage_torsion_preset_ = true;
            this->linkage_torsion_value_str_ = preset_torsion_value_pair.second;
        }

        else{
            std::vector<std::string> torsion_underscore_split_tokens = gmml::Split(preset_torsion_value_pair.first, "_");
	        std::string& residue_index = torsion_underscore_split_tokens[0];
            AtomVector torsion;

            for (unsigned int j = 1; j < 5; j++){
	            std::string& atom_name = torsion_underscore_split_tokens[j];
                torsion.push_back(GetAtomByResidueIndexAndAtomName(residue_index, atom_name, natural_ligand_residues));
            }
            double preset_value = std::stod(preset_torsion_value_pair.second);
            this->explicit_torsions_preset_.emplace_back(std::make_pair(torsion, preset_value));
        }
    }
    return;
}

#endif //OPEN_VALENCE_DERIVATIVE_MOIETY_HPP
