#!/bin/bash
for (( c=0 ; c<$1 ; c+=1 ));
do
git clone https://github.com/hvolos/mcperf.git
cd mcperf
chmod +x turbo-boost.sh
./turbo-boost.sh
done
