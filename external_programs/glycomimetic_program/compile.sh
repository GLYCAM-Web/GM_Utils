#!/bin/bash
g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ -g -fvar-tracking main.cpp -lgmml -pthread -o main.exe -lgmml -lpthread 
