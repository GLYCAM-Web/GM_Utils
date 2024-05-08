#!/bin/bash
g++ -std=c++17 -I ${GEMSHOME}/gmml/ -L${GEMSHOME}/gmml/bin/ -Wl,-rpath,${GEMSHOME}/gmml/bin/ make_ligand_pdb2entropy_metadata.cpp -o make_ligand_pdb2entropy_metadata.exe -lgmml -lpthread
g++ -std=c++17 -I "${GEMSHOME}"/gmml -L"${GEMSHOME}"/gmml/bin -Wl,-rpath,"${GEMSHOME}"/gmml/bin/ reformat_pdb.cpp -o reformat_pdb.exe -lgmml -pthread
