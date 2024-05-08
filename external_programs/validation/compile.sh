#!/bin/bash
#g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ main.cpp -L/usr/include/c++/9/boost_1_66_0/stage/lib -lgmml -pthread -o ./main.exe -lgmml -lpthread -lboost_filesystem -lboost_system
g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ main.cpp -lgmml -pthread -o ./main.exe -lgmml -lpthread 
