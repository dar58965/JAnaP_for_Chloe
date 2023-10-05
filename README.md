# Run Instructions 
These directions assume Windows Powershell 6+

|Make sure Git and Docker are installed on machine. All machines need them anyways.|
```
git --version
docker --version
```

Git and Docker distributions:
https://gitforwindows.org/
https://docs.docker.com/desktop/install/windows-install/

### Make sure WSL 2 is turned on as backend to allow Docker to use Linux distros as base image

### Open Windows Powershell or cmd

## Git clone Docker image
```
git clone https://github.com/dar58965/JAnaP_for_Chloe.git janap-ubuntu-docker

cd janap-ubuntu-docker
```

#### Start Docker Engine by opening desktop application

## Docker build command. Creates docker image
```
docker build -t janap-jupyter-linux .
```

## Git Clone original repo
```
cd ..

git clone https://github.com/StrokaLab/JAnaP.git JAnaP

cd janap-ubuntu-docker
```

#### Basically, this command initializes the docker image and connects Port 4000 of host computer with Port 80 of Docker. Bind mount
```
docker run -p 5000:5000 -v C:/Users/dar58/JAnaP-master:/app janap-jupyter-linux
```
