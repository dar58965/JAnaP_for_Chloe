#Ubuntu version placeholder
FROM ubuntu:22.04

LABEL maintainer="Chloe Kaplan"

#Gather necessary functionality for image build. 
#g++-multilib is C++ compiler for mahotas wheel configurations
#apt-get clean + rm -rf var capabilities makes it lighter
RUN apt-get update && \
    apt-get install -y python2.7 && \
    apt-get install -y wget && \
    apt-get install -y unzip && \
    apt-get install -y curl &&\
    apt-get install -y g++-multilib &&\
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


#Create directory structure for the application
RUN mkdir -p /app/bin/packages

#Gather legacy pip and rebuild
RUN curl -fsSL -O https://bootstrap.pypa.io/pip/2.7/get-pip.py
RUN python2.7 get-pip.py --no-python-version-warning && rm -f get-pip.py && apt-get clean


#Gather JAnaP from the og babes and place in packages folder
RUN wget -P /app/bin/packages https://s3.amazonaws.com/umd-cells/packages/ij150-linux64-java8.zip && \
    unzip /app/bin/packages/ij150-linux64-java8.zip -d /app/bin/packages

#Gather requirements.txt for pip installs and installs using dep pip
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    rm -f requirements.txt

#Jupyter notebook step
RUN jupyter nbextension enable --py widgetsnbextension

#Establish working directory
WORKDIR /JAnaP/web

#Run initialize script
CMD ["python", "application.py"]