# Notes
directory structure: 
/app
//bin 
//bin/packages

- Line 17 makes directory but does not move to that directory. Therefore, Line 21-22 is ran in parent directory. So should be no problems cuz py 2.7 also built in parent directory. 
    Python wheel dev???

Build Progress:
    FROM built
    LABEL built
    RUN 5/8

People I cheated off of:
- For legacy pip
```
https://stackoverflow.com/questions/65900292/how-can-i-install-a-legacy-pip-version-with-python-2-6-6-or-python-2-7-5
```
- For legacy wheel configurations
```
https://stackoverflow.com/questions/31573107/how-to-create-a-pure-python-wheel
```

