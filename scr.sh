#!/bin/bash 

for (( i=0 ; i<$1 ; i++ )); 
do
	
    if [ $i -eq 0 ]; then
	chmod +x scr_master.sh
	yes Y|./scr_master.sh
	echo $variable=`cat file |  grep "docker swarm join --token"`
else
	echo "Worker now"
	ssh -o "StrictHostKeyChecking no"  -A node$i<<EOT
	git clone https://github.com/aatana01/Ptix.git
	cd Ptix
	chmod +x scr_work.sh
	yes Y|./scr_work.sh
	sudo$variable
EOT
	
	
fi
done
#yes Y|ssh node0
#cd Ptix
#sudo docker stack deploy --compose-file=docker-compose-swarm.yml SocialNetwork
#python3 scripts/init_social_graph.py --graph=socfb-Reed98
#cd wrk2
#make