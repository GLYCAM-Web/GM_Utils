#!/bin/bash
export GEMSHOME=/programs/gems/yao
g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ -g -fvar-tracking main.cpp -lgmml -pthread -o glycomimetic.exe -lgmml -lpthread 
