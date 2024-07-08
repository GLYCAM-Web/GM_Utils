#!/bin/bash
if [ -z "$GEMSHOME" ]; then
    echo "Please set the GEMSHOME environment variable to the path of the GEMSHOME directory."
    exit 1
fi

if [[ $(hostname) == *"gw-grpc-delegator"* ]]; then
    echo "Compiling the C++ code and SWIG wrapper..."
    # Compile the C++ code and SWIG wrapper with debugging information
    g++ -std=c++17 -g -I$(realpath ../../glycomimetic_program/) -I$GEMSHOME/gmml/ -I/usr/include/python3.9 -I/usr/include/boost -I/usr/include/eigen3 -fPIC -c evaluate_pdb_wrap.cxx evaluate_pdb.cpp

    # Link the object files into a shared library with debugging information
    g++ -shared evaluate_pdb_wrap.o evaluate_pdb.o -L$GEMSHOME/gmml/bin/ -L$LIBSTDCXX_PATH -Wl,-rpath,$GEMSHOME/gmml/bin/ -Wl,-rpath,$LIBSTDCXX_PATH -lgmml -pthread -o _evaluate_pdb.so -lstdc++
else
    echo "Generating the SWIG wrapper..."
    swig -c++ -python evaluate_pdb.i

    # then call itself inside the container to perform the compilation, avoiding libstdc++ version issues and DevEnv changes for now.
    docker exec $(docker ps -a --format "{{.ID}}\t{{.Image}}" | grep gw-grpc-delegator | cut -f 1) /bin/bash -c "cd \$GEMSHOME/External/GM_Utils/external_programs/validation/evaluate_swig && ./swig_compile.sh && echo 'Testing...' && python test_evaluate.py"
fi