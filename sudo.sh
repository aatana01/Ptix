#!/bin/bash
rm file
for (( i=0 ; i<$1 ; i++ ));
do
        sleep 2
        echo $i>>file
        ssh  node$i "sudo docker stats --no-stream;sleep 1;sudo docker stats --no-stream;sleep 1;sudo docker stats --no-stream;sleep 1;sudo docker stats --no-stream;sleep 1;">>file


done
