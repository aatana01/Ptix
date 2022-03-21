#!/bin/bash
chmod +x sudo.sh
for (( c=100 ; c<500 ; c+=100 ));
	echo $c>>file
	./wrk -D exp -t 2 -c 2 -d 100 -L -s ./scripts/social-network/compose-post.lua http://localhost:8080/wrk2-api/post/compose -R $c|./sudo.sh

done
#do this to all nodes that have containers: to run first sudo nano /etc/default/grub change default to intel_pstate=disable then cntrl x yes and enter and run sudo update-grub2 after that reboot(when i reboot cant connect,have to restart moba) and run https://github.com/hvolos/mcperf 






