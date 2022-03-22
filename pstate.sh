#!/bin/bash
for (( c=0 ; c<$1 ; c+=1 ));
do
ssh node$c "sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT='intel_pstate=disable'/' /etc/default/grub;
sudo update-grub2;
sudo reboot"< /dev/null &> /dev/null
done
