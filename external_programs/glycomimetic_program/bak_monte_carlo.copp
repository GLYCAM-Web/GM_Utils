#ifndef MONTE_CARLO_HPP
#define MONTE_CARLO_HPP

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

#include "vina_atom_data.hpp"
#include "rotamer_library.hpp"
#include "utility.hpp"
#include "open_valence_derivative_moiety.hpp"
#include "gridsearch_pthread.hpp"

#include <iostream>
#include <string>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdlib>
#include <pthread.h>
#include <iterator>
#include <chrono>
#include <sstream>
#include <functional> //std::greater
#include <random>
#include <cmath> //std::nextafter, pow
#include <cfloat> //DBL_MAX
#include <algorithm>

//int max_num_gens = 10000;
int max_num_gens = 50;
int convergence_gens = 50;
int num_individuals_per_thread =50;
int mating_trial_factor = 10;
double best_couple_mutation_rate = 0.25;
double chance_steered_mutation = 0.80;
double steered_mutation_base_range = 20.0; //During steered mutation, the best couple mutates with a limit of up two 20 degrees from current value;
typedef std::vector<double> chromosome; //Housing the values of each torsion.
typedef std::vector<chromosome> population;

namespace MonteCarloSearching{
struct fitness_thread_args{
    population* pop_ptr = NULL;
    std::vector<double>* fitness_ptr = NULL;
    AtomVector receptor_atoms;
    AtomVector ligand_atoms;
    AtomVector moiety_atoms;
    std::vector<AtomVector> all_torsions;
    pthread_mutex_t* mutex_ptr = NULL;
    int thread_id = 0;
    int start_index = 0; 
    int end_index = 0;

    fitness_thread_args(){
    }
    fitness_thread_args(population* pop, std::vector<double>* fitness_address, AtomVector& receptor_atoms, AtomVector& ligand_atoms_vector, AtomVector& moiety_atoms_vector, std::vector<AtomVector>& all_torsions_vector, pthread_mutex_t* mutex, int thread_id_value, int start_index_value, int end_index_value){
        this->pop_ptr = pop;
        this->fitness_ptr = fitness_address;
        this->receptor_atoms = receptor_atoms;
        this->ligand_atoms = ligand_atoms_vector;
        this->moiety_atoms = moiety_atoms_vector;
        this->all_torsions = all_torsions_vector;
        this->mutex_ptr = mutex;
        this->thread_id = thread_id_value;
        this->start_index = start_index_value;
        this->end_index = end_index_value;
    }

};

struct mating_mutation_thread_args{
    population* parent_pop_ptr = NULL;
    population* offspring_pop_ptr = NULL;
    std::vector<double>* fitness_ptr = NULL;
    double best_fitness = 999999;
    double worst_fitness = 999999;
    AtomVector moiety_atoms;
    AtomVector moiety_plus_ligand_atoms;
    std::vector<AtomVector> all_torsions;
    pthread_mutex_t* mutex_ptr = NULL;
    int thread_id = 0;
    int start_index = 0;
    int end_index = 0;
    std::pair<double, chromosome>* best_population_pair_ptr = NULL;
    double chance_increase_selection_pressure = 0.000;

    mating_mutation_thread_args(){
    }
    mating_mutation_thread_args(population* parent_pop, population* offspring_pop, std::vector<double>* fitness_address, double best_fitenss_val, double worst_fitness_val, AtomVector& moiety_atoms_vector, AtomVector& moiety_plus_ligand_atoms_vector, std::vector<AtomVector>& all_torsions_vector, pthread_mutex_t* mutex, int thread_id_value, int start_index_value, int end_index_value, std::pair<double, chromosome>* best_population_pair_address, double increase_selection_pressure_chance){
        this->parent_pop_ptr = parent_pop;
        this->offspring_pop_ptr = offspring_pop;
        this->fitness_ptr = fitness_address;
        this->best_fitness = best_fitenss_val;
        this->worst_fitness = worst_fitness_val;
        this->moiety_atoms = moiety_atoms_vector;
        this->moiety_plus_ligand_atoms = moiety_plus_ligand_atoms_vector;
        this->all_torsions = all_torsions_vector;
        this->mutex_ptr = mutex;
        this->thread_id = thread_id_value;
        this->start_index = start_index_value;
        this->end_index = end_index_value;
        this->best_population_pair_ptr = best_population_pair_address;
        this->chance_increase_selection_pressure = increase_selection_pressure_chance;
    }

};
}

double GetUniformDoubleDistributionBetween(int a , int b, bool include_upper_bound = false){
    std::random_device rd; //Seed the mt19937 generator
    std::mt19937 mt(rd());

    if (include_upper_bound){
        std::uniform_real_distribution<double> dist(a, std::nextafter(b, DBL_MAX)); //Get values within [a, b]
        return dist(mt);
    }

    std::uniform_real_distribution<double> dist(a, b); //Get values within [a, b)
    return dist(mt);
}

int GetUniformIntDistributionBetween(int a , int b){
    std::random_device rd; //Seed the mt19937 generator
    std::mt19937 mt(rd());

    std::uniform_int_distribution<int> dist(a, b); //Get values within [a, b)
    return dist(mt);
}

void EvaluateFitness(population* pop_ptr, std::vector<double>* fitness_ptr, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms, std::vector<AtomVector>& all_torsions, int thread_index, int start_index, int end_index){

    std::vector<double>& fitness = (*fitness_ptr);
    population& pop = (*pop_ptr);
    //std::cout << "This is thread " << thread_index << std::endl;

    for (unsigned int i = start_index; i <= end_index; i++){
        chromosome& chro = pop[i];
        for (unsigned int j = 0; j < chro.size(); j++){
            AtomVector& this_torsion = all_torsions[j];
            double& rotation_value = chro[j];
            //std::cout << "Rot value: " << rotation_value << std::endl;
            SetDihedral(this_torsion[0], this_torsion[1], this_torsion[2], this_torsion[3], rotation_value, thread_index);
        }

        VinaScorePrerequisites prerequisites(moiety_atoms, receptor_atoms);
        std::vector<double> scores = VinaScoreInPlace(prerequisites, thread_index);
        //std::cout << "Population " << i << " fitness " << scores[0] << std::endl;
        fitness[i] = scores[0];
    }    

    return;
}


void* EvaluateFitnessStartRoutine (void* arg_ptr){
    MonteCarloSearching::fitness_thread_args* argstruct = (MonteCarloSearching::fitness_thread_args*) arg_ptr;
    EvaluateFitness(argstruct->pop_ptr, argstruct->fitness_ptr, argstruct->receptor_atoms, argstruct->ligand_atoms, argstruct->moiety_atoms, argstruct->all_torsions, argstruct->thread_id, argstruct->start_index, argstruct->end_index);
    return NULL;
}

bool RandomizeChromosomeAndCheckInternalClashes(chromosome& chro, AtomVector& moiety_atoms, AtomVector& ligand_plus_moiety_atoms, std::vector<AtomVector>& all_torsions, int coord_index = 0){
    //If coord_index = -1, Randomize all coord sets.If supply 0 or positive values, only randomize that thread. 
    int max_num_attempts = 1000;
    int num_attempts = 0;
    bool internal_clashes_exists = true;

    while(internal_clashes_exists){
        for (unsigned int i = 0; i < all_torsions.size(); i++){
            AtomVector& this_torsion = all_torsions[i];
            chro[i] = GetUniformDoubleDistributionBetween(0, 360, false);

            SetDihedral(this_torsion[0], this_torsion[1], this_torsion[2], this_torsion[3], chro[i], coord_index);
        }

        internal_clashes_exists = InternalClashesExist(moiety_atoms, ligand_plus_moiety_atoms, coord_index);
        num_attempts++;

        if (num_attempts >= max_num_attempts){
            std::cout << "Failed to encounter a chrosome without internal clashes after a maximum of " << max_num_attempts << " atttempts. Aborting." << std::endl;
            std::cout << "This probably means that you have a bad initial moiety structure. Fix it if this is the case." << std::endl;
            std::exit(1);
        }
    }

    return internal_clashes_exists;
}

void RandomizePopulationUntilNoInternalClashes(population* pop_ptr, AtomVector& moiety_atoms, AtomVector& ligand_plus_moiety_atoms, CoComplex* cocomplex, std::vector<AtomVector>& all_torsions){
    int max_num_attempts = 1000;
    population& pop = (*pop_ptr);

    for (unsigned int i = 0; i < pop.size(); i++){
        chromosome& this_chromosome = pop[i];
        RandomizeChromosomeAndCheckInternalClashes(this_chromosome, moiety_atoms, ligand_plus_moiety_atoms, all_torsions);

    }

    return;
    
}

bool ReturnTrueBasedOnProbability(double probability){
    if (probability < 0){
        std::cout << "Error, ReturnTrueBasedOnProbability receive negative probabiity argument." << std::endl;
        std::exit(1);
    }
    else if (probability >= 1){
        return true;
    }

    double random_double_between_zero_and_one = GetUniformDoubleDistributionBetween(0, 1, false);
    if (probability > random_double_between_zero_and_one){
        return true;
    }
    return false;
}

//bool embryonic_lethal = Mating(parent_population, offspring_population, parent1, parent2, moiety_atoms, moiety_plus_ligand_atoms, all_torsions, thread_id);

bool Mating(chromosome& offspring, chromosome& parent1, chromosome& parent2, AtomVector& moiety_atoms, AtomVector& moiety_plus_ligand_atoms, std::vector<AtomVector>& all_torsions, int thread_id ){
    bool embryonic_lethal = true;
    int num_possibilities = std::pow(2, parent1.size());
    int max_trial = mating_trial_factor * num_possibilities;

    int num_trials = 0;
    while(num_trials < max_trial){
        for (unsigned int i = 0; i < parent1.size(); i++){
            bool inherit_from_parent1 = ReturnTrueBasedOnProbability(0.5);
            offspring[i] = (inherit_from_parent1) ? parent1[i] : parent2[i];
        }

        for (unsigned int i = 0; i < offspring.size(); i++){
            AtomVector& this_torsion = all_torsions[i];
            SetDihedral(this_torsion[0], this_torsion[1], this_torsion[2], this_torsion[3], offspring[i], thread_id);
        }
        bool interal_clashes_exist = InternalClashesExist(moiety_atoms, moiety_plus_ligand_atoms, thread_id);

        //Accept this mating if no internal clashes exist;
        num_trials++;
        if (!interal_clashes_exist){
            embryonic_lethal = false;
            break;
        }
        //Otherwise, try again. While loop repeats
    }

    return embryonic_lethal;
}

bool SteeredMutation(chromosome& offspring, AtomVector& moiety_atoms, AtomVector& moiety_plus_ligand_atoms, std::vector<AtomVector>& all_torsions, int thread_id, double fitness_percentile, chromosome& best_population){
    int num_possibilities = std::pow(2, offspring.size());
    int max_trial = mating_trial_factor * num_possibilities;
    int num_trials = 0;

    //I've design two modes for steered mutation, each having 50% probability. First, evolve towards the best individual among all generations so far. 
    //Second, random mutation +/- certain degrees around curent value. 
    bool learn_from_role_model = ReturnTrueBasedOnProbability(0.5);
    double variation_range = steered_mutation_base_range + 40 * (1- fitness_percentile); //When percentile is 0 (worst), range is 100 deg. When it is 100 (best), range is 20 deg (base range).
    //std::cout << "Fitness percentile: " << fitness_percentile << " and variation range: " << variation_range << std::endl;
    bool internal_clashes_exist = true;

    while(internal_clashes_exist){
        for (unsigned int i = 0; i < offspring.size(); i++){
            double current_value = offspring[i];
            double upper_bound = (learn_from_role_model) ? best_population[i] : current_value + variation_range; 
            double lower_bound = (learn_from_role_model) ? current_value : current_value - variation_range; 
            double new_value = GetUniformDoubleDistributionBetween(lower_bound, upper_bound, true);
            //std::cout << "Current value: " << current_value << " Lower bound: " << lower_bound << " and upper bound: " << upper_bound << " new value: " << new_value << std::endl;
            offspring[i] = new_value;
            AtomVector& this_torsion = all_torsions[i];
            SetDihedral(this_torsion[0], this_torsion[1], this_torsion[2], this_torsion[3], offspring[i], thread_id);
        }

        internal_clashes_exist = InternalClashesExist(moiety_atoms, moiety_plus_ligand_atoms, thread_id);
        num_trials++;

        if (num_trials >= max_trial){
            break;
        }
    }

    return internal_clashes_exist;
}

double ComputeChanceOfMating(double& fitness_percentile, double& best_affinity_so_far, double& best_affinity_this_generation, std::vector<double>& fitness, double& sum_deltaG, double& chance_increase_selection_pressure){
    bool increase_selection_pressure = ReturnTrueBasedOnProbability(chance_increase_selection_pressure);
    int power = (increase_selection_pressure) ? 3 : 2;
    return std::pow(fitness_percentile, power);
}

void MatingBasedOnFitness(population* parent_pop, population* offspring_pop, std::vector<double>* fitness_ptr, double best_fitness, double worst_fitness, AtomVector& moiety_atoms, AtomVector& moiety_plus_ligand_atoms, std::vector<AtomVector>& all_torsions, int thread_id, int start_index, int end_index, pthread_mutex_t* mutex_ptr, std::pair<double, chromosome>* best_population_pair_ptr, double& chance_increase_selection_pressure){
    int num_offspring_generated = 0;
    int num_iteration = 0;
    int num_offspring_to_generate = end_index - start_index + 1;

    population& parent_population =  (*parent_pop);
    population& offspring_population =  (*offspring_pop);
    std::vector<double>& fitness = (*fitness_ptr);
    std::pair<double, chromosome>& best_population_pair = (*best_population_pair_ptr);
    double& best_affinity_so_far = best_population_pair.first;
    double best_affinity_this_generation = (*std::min_element(fitness.begin(), fitness.end()));
    chromosome& best_population = best_population_pair.second;

    while (num_offspring_generated < num_offspring_to_generate){
        //std::cout << "Mating segfault1" << std::endl;
        int i = GetUniformIntDistributionBetween(start_index, end_index); //Each thread chooses parent1 within their range index, but choose 2nd parent from the entire population. 
        int j = GetUniformIntDistributionBetween(0, parent_population.size() - 1);
    
        while (j == i){
            j = GetUniformIntDistributionBetween(0, parent_population.size() - 1);
        }

        chromosome& parent1 = parent_population[i];
        chromosome& parent2 = parent_population[j];
        double fitness_sum = fitness[i] + fitness[j];

        double fitness_percentile = std::abs((worst_fitness - fitness_sum) / (worst_fitness - best_fitness));
        double sum_deltaG = fitness_sum - best_fitness;
        double chance_mating = ComputeChanceOfMating(fitness_percentile, best_affinity_so_far, best_affinity_this_generation, fitness, sum_deltaG, chance_increase_selection_pressure); 
        bool mate = ReturnTrueBasedOnProbability(chance_mating);
        
        if (mate){
            num_offspring_generated++;
            //std::cout << "About to mate " << i << " " << j << std::endl;
           
            chromosome offspring(parent1.size(), 0);
            //Embryonic lethal means that mating cannot find an offspring without internal clashes when maximum number of attempt is reached. 
            bool embryonic_lethal = Mating(offspring, parent1, parent2, moiety_atoms, moiety_plus_ligand_atoms, all_torsions, thread_id);

            if (embryonic_lethal){
                //std::cout << "About to mutate their offspring." << std::endl;
                //Random Mutation on the child resulting in no internal clashes. 
                RandomizeChromosomeAndCheckInternalClashes(offspring, moiety_atoms, moiety_plus_ligand_atoms, all_torsions, thread_id);
            }
            else{
                double relative_mutation_rate = 1- fitness_percentile;
                double chance_child_mutate =  relative_mutation_rate + best_couple_mutation_rate; 
                //std::cout << "Mating chance: " << chance_mating << " and child mutation rate " << chance_child_mutate << std::endl;
                bool mutate = ReturnTrueBasedOnProbability(chance_child_mutate);

                if (mutate){
                    //Mutate the child
                    bool steered_mutation = ReturnTrueBasedOnProbability(chance_steered_mutation);
                    if (steered_mutation){
                        bool mutation_lethal = SteeredMutation(offspring, moiety_atoms, moiety_plus_ligand_atoms, all_torsions, thread_id, fitness_percentile, best_population);
                        if (mutation_lethal){
                            RandomizeChromosomeAndCheckInternalClashes(offspring, moiety_atoms, moiety_plus_ligand_atoms, all_torsions, thread_id);
                        }
                    }
                    else{
                        RandomizeChromosomeAndCheckInternalClashes(offspring, moiety_atoms, moiety_plus_ligand_atoms, all_torsions, thread_id);
                    }
                }
            }

            pthread_mutex_lock(mutex_ptr);
            offspring_population.push_back(offspring);
            pthread_mutex_unlock(mutex_ptr);
        }

        num_iteration++;

    }

    return;
}

void* MatingBasedOnFitnessStartRoutine(void* arg_ptr){
    MonteCarloSearching::mating_mutation_thread_args* argstruct = (MonteCarloSearching::mating_mutation_thread_args*) arg_ptr;
    //pthread_mutex_lock(argstruct->mutex_ptr);
    MatingBasedOnFitness(argstruct->parent_pop_ptr, argstruct->offspring_pop_ptr, argstruct->fitness_ptr, argstruct->best_fitness, argstruct->worst_fitness, argstruct->moiety_atoms, argstruct->moiety_plus_ligand_atoms, argstruct->all_torsions, argstruct->thread_id, argstruct->start_index, argstruct->end_index, argstruct->mutex_ptr, argstruct->best_population_pair_ptr, argstruct->chance_increase_selection_pressure);
    //pthread_mutex_unlock(argstruct->mutex_ptr);
    return NULL;
}

std::pair<double, chromosome> ObtainBestIndividual(std::vector<double> fitness, population& this_population){
    chromosome new_chromosome(this_population[0].size(), 0);
    std::pair<double, chromosome> best_population_this_generation = std::make_pair(999999, new_chromosome);

    for (unsigned int i = 0; i < fitness.size(); i++){
        double& this_population_fitness = fitness[i];
        chromosome& this_individual = this_population[i];

        if (this_population_fitness < best_population_this_generation.first){
            best_population_this_generation.first = this_population_fitness; 
            best_population_this_generation.second = this_individual; 
        }
    }

    return best_population_this_generation;
}

double ChanceIncreaseSelectionPressure(std::vector<double> fitness, double& best_fitness_this_generation){
    double deltaG_factor_10 = 1.3634; //1.3634kcal/mol results in 10 fold of boltzmann probability
    int num_individual_within_tenfold_of_best = 0;
    for (unsigned int i = 0; i < fitness.size(); i++){
        if (fitness[i] - best_fitness_this_generation <= deltaG_factor_10){
            num_individual_within_tenfold_of_best++;
        }
    }

    //std::cout << "Best aff this generation: " << best_affinity_this_generation << " num with 10 fold: " << num_individual_within_tenfold_of_best << std::endl;
    double fraction_individual_within_tenfold_of_best = num_individual_within_tenfold_of_best / ((double) fitness.size());
    //return ReturnTrueBasedOnProbability(fraction_individual_within_tenfold_of_best);
    return fraction_individual_within_tenfold_of_best;
}

std::pair<double, std::vector<double> > MonteCarlo(CoComplex* cocomplex, OpenValence* open_valence, AtomVector& receptor_atoms, AtomVector& ligand_atoms, AtomVector& moiety_atoms,
                                              std::vector<AtomVector>& all_torsions, int interval, int num_threads){

    std::cout << "Start Monte Carlo" << std::endl;
    chromosome new_chromosome (all_torsions.size(), 0.000); //Initialize each torsion to 0.000 degrees
    int population_size = num_individuals_per_thread * num_threads;
    population parent_population (population_size, new_chromosome);
    //population offspring_population (population_size, new_chromosome);
    population offspring_population;
    std::vector<double> fitness(population_size, 999999);

    //Initialize population with random torsion values without internal clashes
    AtomVector ligand_plus_moiety_atoms = ligand_atoms;
    ligand_plus_moiety_atoms.insert(ligand_plus_moiety_atoms.end(), moiety_atoms.begin(), moiety_atoms.end());

    RandomizePopulationUntilNoInternalClashes(&parent_population, moiety_atoms, ligand_plus_moiety_atoms, cocomplex, all_torsions);
    cocomplex->RestoreLigandPositions();
    //std::exit(1);
    
    MonteCarloSearching::fitness_thread_args fitness_argstruct[num_threads];
    MonteCarloSearching::mating_mutation_thread_args mating_mutation_argstruct[num_threads];
    pthread_t tid[num_threads];

    pthread_mutex_t lock;
    if (pthread_mutex_init(&lock, NULL) != 0) {
        std::cout << "Pthread mutex init failed" << std::endl;
        std::exit(1);
    }

    std::pair<double, chromosome> best_population = std::make_pair(999999, new_chromosome);
    for (unsigned int i = 0; i < num_threads; i++){
        int start_index = num_individuals_per_thread * i;
        int end_index = num_individuals_per_thread * (i+1) - 1;
        //std::cout << "Start at: " << start_index << " and end at " << end_index << std::endl;
        fitness_argstruct[i] = MonteCarloSearching::fitness_thread_args(&parent_population, &fitness, receptor_atoms, ligand_atoms, moiety_atoms, all_torsions, &lock, i, start_index, end_index);
        mating_mutation_argstruct[i] = MonteCarloSearching::mating_mutation_thread_args(&parent_population, &offspring_population, &fitness, 999999, 999999, moiety_atoms, ligand_plus_moiety_atoms, all_torsions, &lock, i, start_index, end_index, &best_population, false);
    }

    int num_gens = 0;
    int generation_obtained = 0;
    bool converge = false;
    int num_gens_no_winner = 0;

    while(num_gens < max_num_gens){
        //std::cout << "This is generation " << num_gens + 1 << std::endl;
        //Evaluate fitness
        for (unsigned int i = 0; i < num_threads; i++){
            //Create a child thread
            int success_status = pthread_create(&tid[i], NULL, &EvaluateFitnessStartRoutine, &fitness_argstruct[i]);
            if (success_status != 0){
                std::cout << "Pthread create failed on thread " << i << " error code: " << success_status << " Aborting." << std::endl;
                std::exit(1);
            }
        }

        //Must join threads before fitness vector can be updated
        for (unsigned int i = 0; i < num_threads; i++){
            pthread_join(tid[i], NULL);
        }

        double fitness_sum = 0.0;
        for (unsigned int i = 0; i < fitness.size(); i++){
            fitness_sum += fitness[i];
        }

        //std::cout << num_gens + 1 << "    "  << (double) fitness_sum / fitness.size() << std::endl;

        //Record new winner if appears, otherwise, check for convergence. 
        std::pair<double, chromosome> best_population_this_generation = ObtainBestIndividual(fitness, parent_population);
        if (best_population_this_generation.first < best_population.first){
            best_population.first = best_population_this_generation.first;
            best_population.second = best_population_this_generation.second;
            //std::cout << "New winner appeared in generation: " << num_gens << " affinity " << best_population.first << std::endl;
            std::cout << num_gens + 1 << " " << best_population.first << std::endl;

            num_gens_no_winner = 0;
        }
        else{
            num_gens_no_winner++;
            if (num_gens_no_winner >= convergence_gens){
                std::cout << "Convergence upon no new winner for " << num_gens_no_winner << " generations." << std::endl;
                break;
            }
        }


        //Get best and worse fitness sum for all couples within the population
        std::vector<double> fitness_sorted = fitness;
        std::sort(fitness_sorted.begin(), fitness_sorted.end());
        double best_fitness = fitness_sorted[0] + fitness_sorted[1];
        double worst_fitness = fitness_sorted[fitness.size()-2] + fitness_sorted[fitness.size()-1];

        double chance_increase_selection_pressure = ChanceIncreaseSelectionPressure(fitness, fitness_sorted[0]);
        for (unsigned int i = 0; i < num_threads; i++){
            mating_mutation_argstruct[i].best_fitness = best_fitness;
            mating_mutation_argstruct[i].worst_fitness = worst_fitness;
            mating_mutation_argstruct[i].chance_increase_selection_pressure = chance_increase_selection_pressure; 
        }


        //Mating and mutation based on fitness
        offspring_population.clear();
        cocomplex->RestoreLigandPositions();
        for (unsigned int i = 0; i < num_threads; i++){
            //Create a child thread
            int success_status = pthread_create(&tid[i], NULL, &MatingBasedOnFitnessStartRoutine, &mating_mutation_argstruct[i]);
            if (success_status != 0){
                std::cout << "Pthread create failed on thread " << i << " error code: " << success_status << " Aborting." << std::endl;
                std::exit(1);
            }
        }

        //Must join thread before offspring population can be updated
        for (unsigned int i = 0; i < num_threads; i++){
            pthread_join(tid[i], NULL);
        }

        //The offspring generation becomes parent generation. Start next generation
        parent_population = offspring_population;//With bias
        //RandomizePopulationUntilNoInternalClashes(&parent_population, moiety_atoms, ligand_plus_moiety_atoms, cocomplex, all_torsions); //No bias
        num_gens++;
    }

    pthread_mutex_destroy(&lock);
    //std::exit(1);

    return best_population;
}
#endif //MONTE_CARLO_HPP
