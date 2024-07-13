%module evaluate_pdb
%{
#include "evaluate_pdb.hpp"
%}

%include "std_string.i"
%include "std_vector.i"
%include "exception.i"

%exception {
    try {
        $action
    } catch (const std::exception& e) {
        SWIG_exception(SWIG_RuntimeError, e.what());
    } catch (...) {
        SWIG_exception(SWIG_UnknownError, "Unknown exception");
    }
}

%typemap(new) std::vector<available_atom*> * {
 $1 = new std::vector<available_atom*>();
}
%typemap(destructor) std::vector<available_atom*> {
 delete $1;
}
%include "evaluate_pdb.hpp"
%template(available_atom_vector) std::vector<available_atom>;