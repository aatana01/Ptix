#!/bin/bash

#DOCKER INSTALL
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh


#DOCKER COMPOSE INSTALL
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-Linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose 

#Python 3.5+ (with asyncio and aiohttp)
sudo apt update
sudo apt install software-properties-common

sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9

sudo apt-get install python3-pip python-dev

pip3 install asyncio
pip3 install aiohttp
#libssl
sudo apt-get install libssl-dev

#libz
sudo apt-get install libz-dev

sudo apt-get install luarocks

sudo luarocks install luasocket


#add master node
sudo docker swarm init --advertise-addr 10.10.1.1 >file


