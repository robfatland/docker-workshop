# Prime Checker Workshop - Participant Instructions

## Prerequisites
- Docker Desktop installed and running
- Internet connection


## Part 1 Hello World


```bash
docker run hello-world
```


Unless you have run this before: The Docker Engine on your computer will look for an Image called 'hello-world' 
in its managed Image space and -- finding none -- will fetch the hello-world Image from Docker Hub. It will
save this Image locally and then create a Container from it. The Container is also saved locally. And finally
this Container will run, providing a few lines of text. So that's a first look at the Docker workflow.


## Part 2 Local copy of this repository


In case you plan to follow along, this command will set you up with the necessary files
in a folder called `docker-workshop`.


`cd ~; git clone https://github.com/robfatland/docker-workshop.git`


## Part 3 Dockerfile

This section does not touch the `docker-workshop` folder you may have cloned in the previous step. 
This part is standalone. 


### 3.1 A first command sequence 


Suggestion: Don't copy-paste if possible; the idea here is to start using the `docker` command line interface (CLI). 


```bash
cd ~ 
mkdir fu 
echo FROM python:3.11-slim > ~/fu/Dockerfile
cd ~/fu
ls
echo Note the period at the end of the next command!
docker build -t fu-image .
docker images
docker ps -a
docker run -it fu-image bash
echo From within this Container try some Linux commands, maybe run Python… then type exit to leave
docker ps -a
docker container prune
docker ps -a
docker images
docker rmi fu-image
docker images
```

In summary we created a rather unremarkable Container that consisted of a Debian bash shell and a lightweight
version of Python 3.11. We did this by means of a Dockerfile, then an Image called `fu-image`, then a 
Container that Docker gave some silly name to. We checked in on our work and deleted everything at the
end except for Dockerfile. Docker likes to see the Container deleted before the Image it was built from
so `container prune` preceded `rmi fu-image`.


### 3.2 A second command sequence


The next logical step in learning Docker is to work an example of *changing* a Container and seeing
that the changes persist. 


```bash
cd ~/fu
docker build -t fu-image .
docker images
docker run -it fu-image bash
```

This should get you on the `bash` command line inside the Container. From there issue:


```bash
pwd
ls
echo curious > thiswasnotherebefore
exit
```

Now the Container has halted but it is still stored within the Docker VM on your host machine. 
We will re-start it now. Please note that you will get your Container Name from the `ps -a` 
command. Use this on the subsequent command in place of `crazy_bullwinkle`. 


```bash
docker ps -a
docker start -ai crazy_bullwinkle
```


Once again we are on the command line inside the Container. Now check:


```bash
pwd
ls
cat thiswasnotherebefore
exit
```


Finally back on the host terminal: Tidy up.


```bash
docker container prune
docker rmi fu-image
```


## Part 4 Bind Mount


For this segment we need a Linux path to a temporary data directory on the host machine (laptop). 
I will refer to this location as `~/dwdata`.


Our goal is to create a corresponding data space in the Container. The host data directory is then 
bound to the data directory on the Container.


In this way -- while the Container runs in an isolated space -- its results are accessible
in our host world. 

```
ls ~/fu
cat ~/fu/Dockerfile
echo WORKDIR app >> ~/fu/Dockerfile
cd fu
docker build -t fu-image .
mkdir ~/dwdata
echo This is the host machine > ~/dwdata/host.txt
cat ~/dwdata/host.txt
docker run -it -v ~/dwdata:/data fu-image bash
```

part 2


```
pwd
ls
cd /data
ls
cat host.txt
echo This is from the Container > container.txt
exit
cd ~/dwdata
ls
cat container.txt
```

## Part 5 Summary and Context So Far


## Part 6 Running a cooperative Two Container application

```bash
cd ~/docker-workshop
docker network create prime-net
cd prime-checker
docker build -t prime-checker .
cd ..
cd prime-frontend
docker build -t prime-frontend .
cd ..
docker images
docker run -d --name prime-api --network prime-net prime-checker
docker run -d --name prime-web --network prime-net -p 8080:8080 prime-frontend
docker ps
```

In a browser tab address bar type <b>`http://localhost:8080`</b> and see if the application works.


#### Possible problem with using port 8080


If the web app fails the problem might be that your host computer is using port 8080 for some other
purpose. To confirm this: On a Mac/Linux/WSL instance you can try `lsof -i :8080`. On Windows (not in WSL) 
you can try `netstat -ano | findstr :8080`. In any case you can try a dodge: 


```bash
docker rm -f prime-web
docker run -d --name prime-web --network prime-net -p 9090:8080 prime-frontend
```

...and now in the address bar use `http://localhost:9090`. 


A moment of debugging Zen: You can see what Docker has been up to by checking log files
associated with your Containers.


```bash
docker logs prime-api
docker logs prime-web
```


If a firewall is blocking `http://localhost:8080` you can also try `http://127.0.0.1:8080`.


#### Finishing up part 6


Tidy up: 


```bash
docker rm -f prime-api prime-web
docker network rm prime-net
docker rmi prime-checker prime-frontend
```


For the record, the `prime-web` Container does two things. First it uses the `Flask` web framework to 
hand over the `index.html` file to the browser in response to the browser connecting to `localhost:8080`. 
This `index.html` file is the formatting template for what the browser layout.


Second, `prime-web` responds to the User clicking the **Check** button by acting as a proxy server
with respect to `prime-api`. That is: It gives the number to the second Container `prime-api` which
returns the prime / not-prime evaluation; which is then passed along to the browser.


## Part 7 Running ResNet in a Container


```bash
cd ~/docker-workshop/resnet-classifier
docker build -t resnet-classifier .
docker run -d --name resnet -p 8081:8080 resnet-classifier
```

## Part 8 Summary & Conclusion



# Residual from CA 



## Cleanup (After Workshop)
```bash
docker rm -f prime-api prime-web
docker network rm prime-net
docker rmi robfatland/prime-checker:latest robfatland/prime-frontend:latest
```

## Troubleshooting

**Port 8080 already in use?**
```bash
docker run -d --name prime-web --network prime-net -p 9090:8080 robfatland/prime-frontend:latest
```
Then access at `http://localhost:9090`

**Containers not starting?**
```bash

```

## What's Happening Behind the Scenes?
- `prime-web` serves the HTML interface on port 8080
- When you enter a number, `prime-web` calls `prime-api` via Docker network
- `prime-api` checks if the number is prime and returns the result
- Result is displayed in your browser

This demonstrates Docker networking between containers!
