# Run Instructions 

## Docker build command
- docker build -t janap-jupyter-linux .

## Run Docker command with input folder and output dir as arguments

#### Basically, this command initializes the docker image and adds two volume mounts: the input dir and the output dir
- docker run -v /path/:/input_folder -v /path/:/output_folder -it janap-jupyter-linux


# Notes
directory structure: 
/app
//bin //input_folder //output_folder 
//bin/scripts //bin/packages