#!/bin/bash
for (( i=0 ; i<$1 ; i++ ));
do
        echo $i>>file
        ssh  node$i "sudo docker stats --no-stream;sleep 1;sudo docker stats --no-stream;sleep 1;">>file
        #ssh node$i"sudo docker stats --no-stream; sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream;sudo docker stats --no-stream" >> file


done
