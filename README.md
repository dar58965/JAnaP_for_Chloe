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

### Open Windows Powershell

## Git clone Docker image
```
git clone https://github.com/dar58965/JAnaP_for_Chloe.git JAnaP_Ubuntu_Docker

cd JAnaP_Ubuntu_Docker
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

cd JAnaP
```

#### Basically, this command initializes the docker image and connects Port 4000 of host computer with Port 80 of Docker. Bind mount
```
docker run --build-arg UBUNTU_VERSION={VERSION NUMBER HERE} -v $(pwd):/JAnaP -p 4000:80 janap-jupyter-linux
```

# Notes
directory structure: 
/app
//bin //input_folder //output_folder 
//bin/scripts //bin/packages

## Because the Docker image uses Ubuntu as a base image, the software can be run from Windows Powershell without any need for WSL Ubuntu. Just run it from the Powershell. 


Build Progress:
    FROM built
    LABEL built
    RUN 3/8