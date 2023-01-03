ARG BASE_IMAGE=python:3.10.0-slim-bullseye

FROM ${BASE_IMAGE}

# Install GDAL
RUN apt-get update -y && apt-get upgrade -y && pip install --upgrade pip
RUN apt-get install gdal-bin -y
RUN apt-get -y install nginx
RUN apt-get -y install gcc
ARG CPLUS_INCLUDE_PATH=/usr/include/gdal
ARG C_INCLUDE_PATH=/usr/include/gdal

# Install app
WORKDIR /usr/src/app
COPY ../data data
COPY ../sapi.py sapi.py
COPY ../import_soils.py import_soils.py
COPY ../requirements.txt requirements.txt
COPY ../soil_scripts soil_scripts

COPY ../sapi_config/nginx.conf /etc/nginx
COPY ../sapi_config/uwsgi.ini uwsgi.ini
COPY ../sapi_config/start.sh start.sh
RUN chmod +x start.sh
RUN chown -R www-data:www-data /usr/src/app

# System dependencies
RUN pip install -r requirements.txt
ENV PYTHONPATH=/usr/src/app

CMD ["./start.sh"]
