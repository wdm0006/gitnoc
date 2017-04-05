FROM continuumio/miniconda3:latest

ADD . /gitnoc
WORKDIR /gitnoc

# Add conda-forge channel
RUN conda config --add channels conda-forge && conda env create -n gitnoc
RUN apt-get install node && npm install -g bower && bower install

# activate the app environment
ENV PATH /opt/conda/envs/gitnoc/bin:$PATH