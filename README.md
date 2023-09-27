# Run Instructions 

### Open ubuntu linux

## Git Clone original repo
- git clone https://github.com/StrokaLab/JAnaP.git JAnaP
- cd JAnaP

## Docker build command
- docker build -t janap-jupyter-linux .

#### Basically, this command initializes the docker image and connects Port 4000 of host computer with Port 80 of Docker
- docker run -v $(pwd):/JAnaP -p 4000:80 janap-jupyter-linux


# Notes
directory structure: 
/app
//bin //input_folder //output_folder 
//bin/scripts //bin/packages