#Ubuntu version placeholder
FROM ubuntu:22.04

LABEL maintainer="Davide Rossotto"

#Gather necessary functionality for image build. 
#g++-multilib is C++ compiler for mahotas wheel configurations
#apt-get clean + rm -rf var capabilities makes it lighter
RUN apt-get update && \
    apt-get install -y wget && \
    apt-get install -y unzip && \
    apt-get install -y curl && \
    apt-get install -y python2.7 && \
    apt-get install -y python2.7-dev && \
    apt-get install -y g++-multilib && \
    apt-get install -y libglib2.0.0 && \
    apt-get install -y libsm6 && \
    apt-get install -y libxrender1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y libxext6 && \
    apt-get install -y libgl1-mesa-glx && \
    apt-get install -y libgtk2.0-0 && \
    apt-get clean

RUN apt-get update && \
    apt-get install -y python-tk && \
    apt-get clean

#Create directory structure for the application
RUN mkdir -p /app/bin/packages

#Gather legacy pip and rebuild
RUN curl -fsSL -O https://bootstrap.pypa.io/pip/2.7/get-pip.py
RUN python2.7 get-pip.py --no-python-version-warning && rm -f get-pip.py && apt-get clean

#Don't remember exactly what this is from but junction analyzer wants it, therefore shall have it
RUN wget -P /app/bin/packages https://s3.amazonaws.com/umd-cells/packages/ij150-linux64-java8.zip && \
    unzip /app/bin/packages/ij150-linux64-java8.zip -d /app/bin/packages


#Gather requirements.txt for pip installs and installs using dep pip
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    rm -f requirements.txt

COPY JAnaP-1.1 /app/

COPY images /tmp/
#Jupyter notebook step
RUN jupyter nbextension enable --py widgetsnbextension

COPY services.sh /app/services.sh
RUN chmod +x /app/services.sh

EXPOSE 5000
EXPOSE 8888


CMD ["/app/services.sh"]