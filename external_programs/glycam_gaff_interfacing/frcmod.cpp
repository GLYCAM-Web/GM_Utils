#ifndef FRCMOD_CPP
#define FRCMOD_CPP

#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <cctype>
#include <algorithm>

#include "mainparm.cpp"

struct Frcmod{
    Frcmod(char* file_path){
        std::ifstream mainparm(file_path);
	//Title
	std::getline(mainparm, this->title_);
	std::vector<std::string> acceptable_cards = {"MASS", "BOND", "ANGLE", "ANGL", "DIHE", "IMPROPER", "IMPR", "NONBON", "NONB"};

	//Rest of file
	std::string line;
	std::string reading_section;
	while (std::getline(mainparm, line)){

	    //White space lines anywhere in the file will be ignored.
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
		reading_section.clear();
                continue;
            }

	    if (std::find(acceptable_cards.begin(), acceptable_cards.end(), line) != acceptable_cards.end()){
	        reading_section = line;

		if (line == "NONBON" || line == "NONB"){
	            this->six_twelve_potential_ = new SixTwelvePotential("", "");
		}
		std::getline(mainparm, line);
	    }
	    else if (reading_section.empty()){
	        std::cout << "Illegal frcmod card: " << line << std::endl;
		std::exit(1);
	    }

	    std::string line_no_whitespace2 = line;
            gmml::Trim(line_no_whitespace2);

            if (line_no_whitespace2.empty()){ //If you are already reading a section but sees a blank line, quit reading the current section.
                reading_section.clear();
                continue;
            }

	    //MASS
	    if(reading_section == "MASS"){
		std::string line_no_whitespace2 = line;
		gmml::Trim(line_no_whitespace2);
	        std::string kndsym = line.substr(0,2);
	        std::string amass = line.substr(3,14);
	        std::string atpol = line.substr(17,7);
	        std::string comment = line.substr(24);
                this->mass_lines_.emplace_back(new MassLine(kndsym, amass, atpol, comment));
	    }
	    //BONDS
	    else if(reading_section == "BOND"){
		//std::getline(mainparm, line);
		std::string line_no_whitespace2 = line;
                gmml::Trim(line_no_whitespace2);
	        std::string ibt = line.substr(0,2);
	        std::string jbt = line.substr(3,2);
	        std::string rk  = line.substr(5,10);
	        std::string req = line.substr(15,10);
	        std::string comment = (line.size() >= 25) ? line.substr(24) : "" ;
	        this->bond_lines_.emplace_back(new BondLine(ibt, jbt, rk, req, comment));
	    }

	    //ANGLES
	    else if (reading_section == "ANGLE" || reading_section == "ANGL"){
		//std::getline(mainparm, line);
		std::string line_no_whitespace2 = line;
                gmml::Trim(line_no_whitespace2);
	        std::string itt = line.substr(0,2);
	        std::string jtt = line.substr(3,2);
	        std::string ktt = line.substr(6,2);
	        std::string tk  = line.substr(8,10);
	        std::string teq = line.substr(18,10);
	        std::string comment = (line.size() >= 29) ? line.substr(28) : "" ;
	        this->angle_lines_.emplace_back(new AngleLine(itt, jtt, ktt, tk, teq, comment));
	    }

	    //TORSIONS
	    else if (reading_section == "DIHE"){
		reading_section = "DIHE";
		//std::getline(mainparm, line);
                std::string ipt = line.substr(0,2);
	        std::string jpt = line.substr(3,2);
	        std::string kpt = line.substr(6,2);
	        std::string lpt = line.substr(9,2);
	        std::string idivf = line.substr(11,4);
	        std::string pk = line.substr(15,15);
	        std::string phase = line.substr(30,15);
	        std::string pn = line.substr(45,15);
	        std::string comment = (line.size() >= 61) ? line.substr(60) : "" ;

	        //If the first character is not space, it must be atom type. Then start a new torsion object and parse the 1st line.
		if (!std::isspace(ipt[0])){
                    bool already_exists = false;
                    for (unsigned int i = 0; i < this->torsion_blocks_.size(); i++){
                        TorsionBlock* this_torsion = torsion_blocks_[i];
                        if (this_torsion->is_identical(ipt, jpt, kpt, lpt)){
                            this_torsion->AddTerm(new TorsionTerm(idivf, pk, phase, pn, comment));
                            already_exists = true;
                            break;
                        }
                    }

                    if (!already_exists){
                        this->torsion_blocks_.emplace_back(new TorsionBlock(ipt, jpt, kpt, lpt, idivf, pk, phase, pn, comment));
                    }
                }
	        //Otherwise if it is indeed a space, simply Append a term to the last torsion
	        else{
	            this->torsion_blocks_.back()->AddTerm(new TorsionTerm(idivf, pk, phase, pn, comment));
	        } 
	    }

	    //IMPROPER TORSIONS
            else if (reading_section == "IMPROPER" || reading_section == "IMPR"){
                std::string ipt = line.substr(0,2);
                std::string jpt = line.substr(3,2);
                std::string kpt = line.substr(6,2);
                std::string lpt = line.substr(9,2);
                std::string idivf = line.substr(11,4);
                std::string pk = line.substr(15,15);
                std::string phase = line.substr(30,15);
                std::string pn = line.substr(45,15);
                std::string comment = (line.size() >= 61) ? line.substr(60) : "" ;

                //If the first character is not space, it must be atom type. Then start a new torsion object and parse the 1st line.
		if (!std::isspace(ipt[0])){
                    bool already_exists = false;
                    for (unsigned int i = 0; i < this->improper_torsion_blocks_.size(); i++){
                        TorsionBlock* this_improper_torsion = this->improper_torsion_blocks_[i];
                        if (this_improper_torsion->is_identical(ipt, jpt, kpt, lpt)){
                            this_improper_torsion->AddTerm(new TorsionTerm(idivf, pk, phase, pn, comment));
                            already_exists = true;
                            break;
                        }
                    }

                    if (!already_exists){
                        this->improper_torsion_blocks_.emplace_back(new TorsionBlock(ipt, jpt, kpt, lpt, idivf, pk, phase, pn, comment));
                    }
                }
                //Otherwise if it is indeed a space, simply Append a term to the last torsion
                else{
                    this->improper_torsion_blocks_.back()->AddTerm(new TorsionTerm(idivf, pk, phase, pn, comment));
                }
            }

	    //6-12 POTENTIAL (This section contains exactly one line, and has no space between next section
	    else if (reading_section == "NONBON" || reading_section == "NONB"){
	        std::string line_no_whitespace = line;
                gmml::Trim(line_no_whitespace);
                if (line_no_whitespace.empty() || line == "END"){
                    break;
                }

	        std::string ltynb        = line.substr(2,2);
                std::string pol_r_a      = line.substr(10,10);
                std::string xneff_edep_c = line.substr(20,10);
                std::string rmin         = line.substr(30,10);
                std::string comment      = (line.size() >=  41) ? line.substr(40) : "";

	        SixTwelvePotentialEntry* entry = new SixTwelvePotentialEntry(ltynb, pol_r_a, xneff_edep_c, rmin, comment);
	        this->six_twelve_potential_->AddSixTwelvePotentialEntry(entry);
	    }
	}

    }

    Frcmod(std::string title, std::vector<MassLine*>& masses, std::vector<BondLine*>& bonds, std::vector<AngleLine*>& angles, std::vector<TorsionBlock*>& torsions, std::vector<TorsionBlock*> improper_torsions,
	   SixTwelvePotential* six_twelve_potential){
        this->title_ = title;
	this->mass_lines_ = masses;
	this->bond_lines_ = bonds;
	this->angle_lines_ = angles;
	this->torsion_blocks_ = torsions;
	this->improper_torsion_blocks_ = improper_torsions;
	this->six_twelve_potential_ = six_twelve_potential;
    }

    void Write(std::string filepath){
        std::ofstream output_frcmod(filepath);
	if (output_frcmod.fail()){
	    std::cout << "Could not open " << filepath << " for writing." << std::endl;
	    std::exit(1);
	}
        
	output_frcmod << this->title_ << std::endl;

	output_frcmod << "MASS" << std::endl;
        for (unsigned int i = 0; i < this->mass_lines_.size(); i++){
	    MassLine* mass = this->mass_lines_[i];
	    std::vector<std::string> s = {mass->KNDSYM, mass->AMASS, mass->ATPOL, mass->COMMENT};

	    output_frcmod << std::setw(2) << std::left << s[0] << " " << s[1] << s[2] << s[3] << std::endl;

	}
	output_frcmod << std::endl;

	output_frcmod << "BOND" << std::endl;
	for (unsigned int i = 0; i < this->bond_lines_.size(); i++){
	    BondLine* bond = this->bond_lines_[i];
	    std::vector<std::string> s = {bond->IBT, bond->JBT, bond->RK, bond->REQ, bond->COMMENT};

	    output_frcmod << std::setw(2) << std::left << s[0] << "-" << std::setw(2) << std::left << s[1] << s[2] << s[3] << s[4] << std::endl;
	}

	output_frcmod << std::endl;

	output_frcmod << "ANGLE" << std::endl;
	for (unsigned int i = 0; i < this->angle_lines_.size(); i++){
	    AngleLine* angle = this->angle_lines_[i];
	    std::vector<std::string> s = {angle->ITT, angle->JTT, angle->KTT, angle->TK, angle->TEQ, angle->COMMENT};

	    output_frcmod <<  std::setw(2) << std::left << s[0] << "-" << std::setw(2) << std::left << s[1] << "-" << std::setw(2) << std::left << s[2] << s[3] << s[4] << s[5] << std::endl;
	}

	output_frcmod << std::endl;

	output_frcmod << "DIHE" << std::endl;
	for (unsigned int i = 0; i < this->torsion_blocks_.size(); i++){
	    TorsionBlock* torsion = this->torsion_blocks_[i];
	    std::vector<TorsionTerm*>& terms = torsion->terms;

	    for (unsigned int j = 0; j < terms.size(); j++){
		TorsionTerm* term = terms[j];
	        std::vector<std::string> s = {torsion->IPT, torsion->JPT, torsion->KPT, torsion->LPT, term->IDIVF, term->PK, term->PHASE, term->PN, term->COMMENT};

		output_frcmod << std::setw(2) << std::left << s[0] << "-" << std::setw(2) << std::left << s[1] << "-" << std::setw(2) << std::left << s[2] << "-" << std::setw(2) << std::left << s[3]
		              << s[4] << s[5] << s[6] << s[7] << s[8] << std::endl;
	    }
	}
	output_frcmod << std::endl;

	output_frcmod << "IMPROPER" << std::endl;
	for (unsigned int i = 0; i < this->improper_torsion_blocks_.size(); i++){
            TorsionBlock* torsion = this->improper_torsion_blocks_[i];
            std::vector<TorsionTerm*>& terms = torsion->terms;

            for (unsigned int j = 0; j < terms.size(); j++){
                TorsionTerm* term = terms[j];
                std::vector<std::string> s = {torsion->IPT, torsion->JPT, torsion->KPT, torsion->LPT, term->IDIVF, term->PK, term->PHASE, term->PN, term->COMMENT};

		output_frcmod << std::setw(2) << std::left <<  s[0] << "-" << std::setw(2) << std::left << s[1] << "-" << std::setw(2) << std::left << s[2] << "-" << std::setw(2) << std::left << s[3]
                              << s[4] << s[5] << s[6] << s[7] << s[8] << std::endl;
            }
        }
	output_frcmod << std::endl;

	output_frcmod << "NONBON" << std::endl;
	if (this->six_twelve_potential_ != NULL){
	    std::vector<SixTwelvePotentialEntry*>& entries = this->six_twelve_potential_->entries_;

	    for (unsigned int i = 0; i < entries.size(); i++){
	        SixTwelvePotentialEntry* entry = entries[i];
		std::vector<std::string> s = {entry->LTYNB, entry->POL_R_A, entry->XNEFF_EDEP_C, entry->RMIN, entry->COMMENT};

		output_frcmod << "  " << std::setw(2) << std::left << s[0] 
			      << "      " << s[1] << s[2] << s[3] << s[4] << std::endl;
	    }
	}
	output_frcmod << std::endl;

	output_frcmod.close();
    }

    std::string title_;
    std::vector<MassLine*> mass_lines_;
    //std::string hydrophilic_atom_types_;
    std::vector<BondLine*> bond_lines_;
    std::vector<AngleLine*> angle_lines_;
    std::vector<TorsionBlock*> torsion_blocks_;
    std::vector<TorsionBlock*> improper_torsion_blocks_;
    //std::vector<HbondLine*> hbond_lines_;
    //std::vector<EquiValencingAtom*> equivalencing_atoms_;
    SixTwelvePotential* six_twelve_potential_ = NULL;
};
#endif
