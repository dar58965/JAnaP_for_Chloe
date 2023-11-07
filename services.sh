#!/bin/bash

python2.7 app/web/application.py &

jupyter notebook --no-browser --ip=0.0.0.0 --port=8888 --allow-root --notebook-dir=/tmp &

wait