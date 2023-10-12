
# JAnaP - Junction Analyzer Program

Please refer to the following article for more information and/or cite when using the JAnaP for published works : Gray, K.M., Katz, D.B., Brown, E.G. et al. Ann Biomed Eng (2019). https://doi.org/10.1007/s10439-019-02266-5

Please also complete this short form prior to download: https://forms.gle/m7sGwd69sEhiGRJc9 so we can track who is using the program and for what research applications it is being used. 

All neccessary insructions to install and use the program can be found in the JAnaP User Guide provided.






## Setup

### Configuration

The file `node.conf` contains a default configuration that is loaded by the application. If you need to move the data directory (i.e. using an external drive to hold large files), create a file named `node.conf.local` which will be read **instead** of `node.conf`. The application does not combine the options from both files, if `.local` exists it will use those options. 

### Windows 

You will need to install the C++ compiler for Python. Download it here: https://www.microsoft.com/en-us/download/details.aspx?id=44266

To setup everything you need to run the code on a Windows machine, run the `setup.bat` file which can be found in `bin/setup.bat`. This script will do the following: 

### Linux

Use the following commands:

```
$ mkdir bin/packages
$ wget -P bin/packages/ https://s3.amazonaws.com/umd-cells/packages/ij150-linux64-java8.zip
$ unzip bin/packages/ij150-linux64-java8.zip -d bin/packages/
```

Then setup a virtualenv to work out of and install requirements: 

```
$ virtualenv venv
$ . venv/bin/activate
$ pip install -r bin/requirements.txt
```

### Setting up Notebooks

```
$ jupyter nbextension enable --py widgetsnbextension
```

### Checking for Errors

In order to check for errors after running jobs, navigate to your main repository, then go to: data / projects / 'your project name' / system / job errors