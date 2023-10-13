# Run Instructions 
1. Set-up (Use cmd or Powershell)

|Make sure Git and Docker are installed on machine. All machines need them anyways.|
```
git --version
docker --version
```

Git and Docker distributions:
https://gitforwindows.org/
https://docs.docker.com/desktop/install/windows-install/

2. Git clone Docker image
```
git clone https://github.com/dar58965/JAnaP_for_Chloe.git janap-ubuntu-docker

cd janap-ubuntu-docker
```

3.  Docker build command. Creates docker image
```
docker build -t janap-jupyter-linux .
```
4. Docker run to initialize Junction Analyzer Program
```
docker run -p 5000:5000 janap-jupyter-linux
```

5. Access program in browser
```
localhost:5000
```

# Clean Up When Done
- ctrl + C to stop application run. ctrl + D to exit from Docker container if ran in interactive mode (docker run -it). 

- ```Docker ps -a``` to view current images. 
- To remove remaining unused Docker image and containers: 

```
docker rmi -f $(docker images -f "dangling=true" -q)
```
