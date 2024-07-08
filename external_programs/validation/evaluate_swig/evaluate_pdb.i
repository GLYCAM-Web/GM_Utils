%module evaluate_pdb

%{
#include "evaluate_pdb.hpp"
%}

%include "std_string.i"
%include "std_vector.i"

%typemap(new) std::vector<available_atom*> * {
    $1 = new std::vector<available_atom*>();
}

%typemap(destructor) std::vector<available_atom*> {
    delete $1;
}

%include "evaluate_pdb.hpp"

%template(available_atom_vector) std::vector<available_atom>;
