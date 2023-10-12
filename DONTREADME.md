# Notes
directory structure: 
/app
//bin 
//bin/packages

- Line 17 makes directory but does not move to that directory. Therefore, Line 21-22 is ran in parent directory. So should be no problems cuz py 2.7 also built in parent directory. 
    Python wheel dev???

- Idea time for wheel builds: Filter the requirements.txt to not include the packages which require the unsupported wheel configurations. 
    Rewrite the setup.py for those scripts using legacy wheel config, parse that into procedure, pip install, continue

- Prediction: That fucking jupyter line is not going to work. Gonna use default ver., gonna need legacy

- If I can forcefeed pip the ability to interact with 'x86-Linux-gnu-gcc', then it can probably work out. All fucked up wheel configurations are those which rely on C++ compiler. 

Build Progress:
    FROM built \
    LABEL built \
    RUN 12/15 \
    RUN *past pip* Lol kind of. Should isolate packages that require C++ compiler. 

People I cheated off of:
- For legacy pip
```
https://stackoverflow.com/questions/65900292/how-can-i-install-a-legacy-pip-version-with-python-2-6-6-or-python-2-7-5
```
- For legacy wheel configurations
```
https://stackoverflow.com/questions/31573107/how-to-create-a-pure-python-wheel
```

- Mahotas wheel archive (Let's fucking go I can just patch a compatible one in hype)
```
https://www.lfd.uci.edu/~gohlke/pythonlibs/#mahotas
```

#### Because the Docker image uses Ubuntu as a base image, the software can be run from Windows Powershell without any need for WSL Ubuntu. Just run it from the Powershell. 