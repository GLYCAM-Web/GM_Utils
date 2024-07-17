#!/bin/bash
export GEMSHOME=/programs/gems/yao
#g++ -std=c++11 -I$GEMSHOME/gmml/includes -L$GEMSHOME/gmml/lib main.cpp -L/usr/include/c++/9/boost_1_66_0/stage/lib -o ../main.exe -lgmml -lpthread -lboost_filesystem -lboost_system 
g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ main.cpp -L/usr/include/c++/9/boost_1_66_0/stage/lib -lgmml -pthread -o ./glycamGaffInterfacing.exe -lgmml -lpthread -lboost_filesystem -lboost_system
#g++ -std=c++17 -I $GEMSHOME/gmml/ -L$GEMSHOME/gmml/bin/ -Wl,-rpath,$GEMSHOME/gmml/bin/ main.cpp -lgmml -pthread -o ./main.exe -lgmml -lpthread 
#g++ -std=c++11 -I$GEMSHOME/gmml/includes -L$GEMSHOME/gmml/lib main.cpp -o ../main.exe -lgmml -lpthread 
