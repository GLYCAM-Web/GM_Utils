#include "gridsearch_pthread.hpp"
#include "open_valence_derivative_moiety.hpp"
#include "utility.hpp"
#include "rotamer_library.hpp"
#include "amber_handling.hpp"
#include "option_handling.hpp"

#include <cstdlib>

typedef std::vector<MolecularModeling::Atom*> AtomVector;

int main(int argc, char* argv[])
{
    //glycomimetics
    int interval = 10;
    int max_num_threads = 4;
    int num_threads = 1;
    std::string ext = "";
    std::string cocrystal_pdb_path = "";
    std::string moiety_path = "";
    std::string output_pdb_path = "output";
    std::string logfile_path = "gridsearch_log.txt";
    std::string requested_combinations;

    std::vector<open_valence_option> open_valence_options;
    //ProcessOptions(argc, argv, interval, max_num_threads, num_threads, ext, cocrystal_pdb_path, moiety_path, output_pdb_path, logfile_path, open_valence_options, requested_combinations);
    bool use_input_file = false;
    bool option_valid = ValidateOptions(argc, argv, use_input_file);
    if (use_input_file){
        ProcessInputFile(argc, argv, interval, max_num_threads, num_threads, cocrystal_pdb_path, output_pdb_path, logfile_path, open_valence_options);
    }
    else if (option_valid){
        ProcessOptions(argc, argv, interval, max_num_threads, num_threads, cocrystal_pdb_path, output_pdb_path, logfile_path, open_valence_options, requested_combinations);
    }
    else{
        std::exit(1);
    }


    //Check if GEMSHOME is set
    char* gemshome = std::getenv("GEMSHOME");
    if (!gemshome){
        std::cout << "GEMSHOME environment variable must be set. Aborting." << std::endl;
        return 0;
    }
    std::string gems_home(gemshome);
    
    std::cout << "Cocrystal pdb path: " << cocrystal_pdb_path << std::endl;
    CoComplex* cocomplex = new CoComplex(cocrystal_pdb_path, gems_home, output_pdb_path, num_threads);
    std::cout << "Done cocomplex" << std::endl;

    AtomVector ligand_atoms = cocomplex->GetLigandAtoms();
    AtomVector receptor_atoms = cocomplex->GetReceptorAtoms();

    VinaScorePrerequisites requisites(ligand_atoms, receptor_atoms);
    std::vector<double> affinities = VinaScoreInPlace(requisites, 0);
    double total_affinity = affinities[0];

    std::cout << "reference affinity: " << total_affinity << std::endl;
    //std::exit(1);

    std::vector<OpenValence*> open_valences = GetOpenValenceSideGroupSp3Oxygens(cocomplex, open_valence_options, num_threads);
    std::cout << "Open valence size: " << open_valences.size() << std::endl;

    GridSearchingForOpenValenceAtoms(cocomplex, open_valences, interval, num_threads, output_pdb_path, logfile_path, requested_combinations);
    std::cout << "End" << std::endl;
} 

