# Run Instructions 
1. Set-up (Use cmd or Powershell)

|Make sure Git and Docker are installed on machine. All machines need them anyways.|
```
git --version
docker --version
```
|Check if you have any containers running the janap-jupyter-linux image. |
- List containers: ```docker ps -a```
- If container with the 'janap-jupyter-linux' image exists: ```docker rm -v {container_name}```
- If container exists and is running: ```docker stop {container name}``` then ```docker rm -v {container name}```
- Run ```docker ps -a``` again to make sure the container is gone. 

|If you have a forked repository: |
- Sync your fork with the master version using ```gh repo sync dar58965/JAnaP_for_Chloe -b {Forked name}```
You should do this every once in awhile. The Master version might have gotten better!

Git and Docker distributions:
https://gitforwindows.org/
https://docs.docker.com/desktop/install/windows-install/

2. Delete janap-ubuntu-docker directory
```
rmdir /s /q janap-ubuntu-docker
```

3. Git clone Docker image
```
git clone https://github.com/dar58965/JAnaP_for_Chloe.git janap-ubuntu-docker

cd janap-ubuntu-docker
```

4.  Docker build command. Creates docker image
```
docker build -t janap-jupyter-linux .
```
5. Docker run to initialize Junction Analyzer Program
```
docker run -p 5000:5000 -p 8888:8888 janap-jupyter-linux
```

For interactive mode: 
```
docker run -it -p 5000:5000 -p 8888:8888 janap-jupyter-linux
```

6. Access program in browser
```
localhost:8888 for jupyter notebook
localhost:5000 for JAnaP
```

# Clean Up When Done


- To view all current images: ```docker ps -a``` 

- To remove container: ```docker stop {container name}``` then ```docker rm -v {container name}```
