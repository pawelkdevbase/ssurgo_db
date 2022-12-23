ARG BASE_IMAGE=python:3.10.0-slim-bullseye

FROM ${BASE_IMAGE}

# Install GDAL
RUN apt-get update && apt-get upgrade -y
RUN apt-get install gdal-bin -y
ARG CPLUS_INCLUDE_PATH=/usr/include/gdal
ARG C_INCLUDE_PATH=/usr/include/gdal

# Install app
WORKDIR /usr/src/app
COPY ../data data
COPY ../sapi.py sapi.py
COPY ../import_soils.py import_soils.py
COPY ../requirements.txt requirements.txt
COPY ../soil_scripts soil_scripts

# System dependencies
RUN pip install -r requirements.txt

ENV PYTHONPATH=/usr/src/app
