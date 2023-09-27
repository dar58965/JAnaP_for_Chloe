#Ubuntu version placeholder
FROM ubuntu:22.04

LABEL maintainer="Chloe Kaplan"

#Can not run apt-get install and upgrade to get latest versions cuz deprecated python. 
#apt-get clean + rm -rf var capabilities makes it lighter
RUN apt-get update && \
    apt-get install -y python2.7 && \
    apt-get install -y wget && \
    apt-get install -y unzip && \
    apt-get install -y python-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

#Create directory structure for the application
RUN mkdir -p /app/bin/packages

#Gather JAnaP from the og babes and place in packages folder
RUN wget -P /app/bin/packages https://s3.amazonaws.com/umd-cells/packages/ij150-linux64-java8.zip && \
    unzip /app/bin/packages/ij150-linux64-java8.zip -d /app/bin/packages

#Gather requirements.txt for pip installs and installs using dep pip
COPY bin/requirements.txt .
RUN pip install -r requirements.txt /app/tmp/requirements.txt && \
    rm -f /app/tmp/requirements.txt

#Jupyter notebook step
RUN jupyter nbextension enable --py widgetsnbextension

#Establish working directory
WORKDIR /JAnaP/web

#Run initialize script
CMD ["python", "application.py"]