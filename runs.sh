#!/bin/bash
chmod +x sudo.sh
for (( c=0 ; c<$1 ; c++ )); 
do
		python3 ./profiler.py -n node$c start
done
for (( c=100 ; c<500 ; c+=100 ));
do
	echo $c>>file
	./wrk -D exp -t 2 -c 2 -d 100 -L -s ./scripts/social-network/compose-post.lua http://localhost:8080/wrk2-api/post/compose -R $c|./sudo.sh

done
for (( c=0 ; c<$1 ; c++ )); 
do
		python3 ./profiler.py -n node$c stop
done
for (( c=0 ; c<$1 ; c++ )); 
do
		python3 ./profiler.py -n node$c report -d /tmp/data
done




