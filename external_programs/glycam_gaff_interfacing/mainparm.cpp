#ifndef MAINPARM_CPP
#define MAINPARM_CPP

#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <cctype>
#include <algorithm>

struct MassLine{
    MassLine(std::string kndsym, std::string amass, std::string atpol, std::string comment){
	this->KNDSYM = kndsym;
	this->AMASS = amass;
	this->ATPOL = atpol;
	this->COMMENT = comment;
    }
    std::string KNDSYM,AMASS,ATPOL,COMMENT;
};

struct BondLine{
    BondLine(std::string ibt, std::string jbt, std::string rk, std::string req, std::string comment){
        this->IBT = ibt;
	this->JBT = jbt;
	this->RK  = rk;
	this->REQ = req;
	this->COMMENT = comment;
    }
    std::string IBT,JBT,RK,REQ,COMMENT;
};

struct AngleLine{
    AngleLine(std::string itt, std::string jtt, std::string ktt, std::string tk, std::string teq, std::string comment){
        this->ITT = itt;
	this->JTT = jtt;
	this->KTT = ktt;
	this->TK  = tk;
	this->TEQ = teq;
	this->COMMENT = comment;
    }
    std::string ITT,JTT,KTT,TK,TEQ,COMMENT;
};

struct TorsionTerm{
    TorsionTerm(std::string idivf, std::string pk, std::string phase, std::string pn, std::string comment){
        this->IDIVF = idivf;
        this->PK  = pk;
        this->PHASE = phase;
        this->PN = pn;
	this->COMMENT = comment;
    }
    std::string IDIVF,PK,PHASE,PN,COMMENT;
};

struct TorsionBlock{
    TorsionBlock(std::string ipt, std::string jpt, std::string kpt, std::string lpt, std::string idivf, std::string pk, std::string phase, std::string pn, std::string comment){
        this->IPT = ipt;
	this->JPT = jpt;
	this->KPT = kpt;
	this->LPT = lpt;
	this->AddTerm(new TorsionTerm(idivf, pk, phase, pn, comment));
    }

    void AddTerm(TorsionTerm* term){
        this->terms.push_back(term);
    }

    bool is_identical(std::string ipt, std::string jpt, std::string kpt, std::string lpt){
        if (this->IPT == ipt && this->JPT == jpt && this->KPT == kpt && this->LPT == lpt){
	    return true;
	}
	return false;
    }

    std::string IPT,JPT,KPT,LPT,COMMENT;
    std::vector<TorsionTerm*> terms;
    
};

struct HbondLine{
    HbondLine(std::string kt1, std::string kt2, std::string a, std::string b, std::string asoln, std::string bsoln, std::string hcut, std::string ic, std::string comment){
        this->KT1 = kt1;
        this->KT2 = kt2;
	this->A   = a;
	this->B   = b;
	this->ASOLN = asoln;
	this->BSOLN = bsoln;
	this->HCUT = hcut;
	this->IC = ic;
	this->COMMENT = comment;
    }
    std::string KT1,KT2,A,B,ASOLN,BSOLN,HCUT,IC,COMMENT;
};

struct EquiValencingAtom{
    EquiValencingAtom(std::string iorg, std::vector<std::string>& ieqv){
        this->IORG = iorg;
	this->IEQV = ieqv;
    }

    std::string IORG;
    std::vector<std::string> IEQV;

};

struct SixTwelvePotentialEntry{
    SixTwelvePotentialEntry(std::string ltynb, std::string pol_r_a, std::string xneff_edep_c, std::string rmin, std::string comment){
        this->LTYNB     = ltynb;
	this->POL_R_A   = pol_r_a;
	this->XNEFF_EDEP_C = xneff_edep_c;
	this->RMIN  = rmin;
	this->COMMENT = comment;
    }
    std::string LTYNB, POL_R_A, XNEFF_EDEP_C, RMIN, COMMENT;
};

struct SixTwelvePotential{
    SixTwelvePotential(std::string label, std::string kindnb){
        this->LABEL = label;
        this->KINDNB = kindnb;	
    }

    void AddSixTwelvePotentialEntry(SixTwelvePotentialEntry* entry){
        this->entries_.push_back(entry);
    }
    std::string LABEL,KINDNB;
    std::vector<SixTwelvePotentialEntry*> entries_;
};

struct MainParm{
    MainParm(char* file_path){
        std::ifstream mainparm(file_path);
	//Title
	std::getline(mainparm, this->title_);

	//Rest of file
	std::string line;
	//MASS
	while (std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

	    std::string kndsym = line.substr(0,2);
	    std::string amass = line.substr(3,14);
	    std::string atpol = line.substr(17,7);
	    std::string comment = line.substr(24);
            this->mass_lines_.emplace_back(new MassLine(kndsym, amass, atpol, comment));
	}

	//Hydrophilic atom types: read but not used
        std::getline(mainparm, this->hydrophilic_atom_types_);

	//BONDS
	while (std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

	    std::string ibt = line.substr(0,2);
	    std::string jbt = line.substr(3,2);
	    std::string rk  = line.substr(5,10);
	    std::string req = line.substr(15,10);
	    std::string comment = (line.size() >= 25) ? line.substr(24) : "" ;
	    this->bond_lines_.emplace_back(new BondLine(ibt, jbt, rk, req, comment));
	}

	//ANGLES
	while(std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

	    std::string itt = line.substr(0,2);
	    std::string jtt = line.substr(3,2);
	    std::string ktt = line.substr(6,2);
	    std::string tk  = line.substr(8,10);
	    std::string teq = line.substr(18,10);
	    std::string comment = (line.size() >= 29) ? line.substr(28) : "" ;

	    this->angle_lines_.emplace_back(new AngleLine(itt, jtt, ktt, tk, teq, comment));

	}

	//TORSIONS
	while(std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

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
        while(std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

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

	//HBOND POTENTIAL
        while(std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
	    gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

	    std::string kt1 = line.substr(2,2);
	    std::string kt2 = line.substr(6,2);
	    std::string a   = line.substr(10,10);
	    std::string b   = line.substr(20,10);
	    std::string asoln = line.substr(30,10);
	    std::string bsoln = line.substr(40,10);
	    std::string hcut = line.substr(50,10);
	    std::string ic = line.substr(60,2);
            std::string comment = (line.size() >= 62) ? line.substr(61) : "" ;

	    this->hbond_lines_.emplace_back(new HbondLine(kt1, kt2, a, b, asoln, bsoln, hcut, ic, comment));
        }

	//EQUIVALENCING ATOM (May or may not be present, need to make judgment)
	while(std::getline(mainparm, line)){
	    //If The first line of this section is empty. This section does not exist. Get the next empty line then break;
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty()){
                break;
            }

	    std::string iorg = line.substr(0,2);
	    std::vector<std::string> ieqv;
	    int char_index = 4;
	    while(char_index + 1 < line.size()){
	        ieqv.push_back(line.substr(char_index, 2));
		char_index += 4;
	    }

	    this->equivalencing_atoms_.emplace_back(new EquiValencingAtom(iorg, ieqv));
	}

	//6-12 POTENTIAL (This section contains exactly one line, and has no space between next section
	std::getline(mainparm, line);
	std::string label = line.substr(0,4);
        std::string kindnb = line.substr(10,2); 	
	this->six_twelve_potential_ = new SixTwelvePotential(label, kindnb);

	while(std::getline(mainparm, line)){
	    std::string line_no_whitespace = line;
            gmml::Trim(line_no_whitespace);
            if (line_no_whitespace.empty() || line == "END"){
                break;
            }

	    std::string ltynb        = line.substr(2,2);
            std::string pol_r_a      = line.substr(10,10);
            std::string xneff_edep_c = line.substr(20,8);
            std::string rmin         = (line.size() >=  29) ? line.substr(28,12) : "";
            std::string comment      = (line.size() >=  41) ? line.substr(40) : "";

	    SixTwelvePotentialEntry* entry = new SixTwelvePotentialEntry(ltynb, pol_r_a, xneff_edep_c, rmin, comment);
	    this->six_twelve_potential_->AddSixTwelvePotentialEntry(entry);

	}

    }

    std::string title_;
    std::vector<MassLine*> mass_lines_;
    std::string hydrophilic_atom_types_;
    std::vector<BondLine*> bond_lines_;
    std::vector<AngleLine*> angle_lines_;
    std::vector<TorsionBlock*> torsion_blocks_;
    std::vector<TorsionBlock*> improper_torsion_blocks_;
    std::vector<HbondLine*> hbond_lines_;
    std::vector<EquiValencingAtom*> equivalencing_atoms_;
    SixTwelvePotential* six_twelve_potential_ = NULL;
};
#endif
