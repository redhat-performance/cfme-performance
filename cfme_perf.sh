#!/usr/bin/env bash

if hash dnf;
then
  YUM=dnf
else
  YUM=yum
fi

sudo $YUM install -y numpy \
     python-virtualenv \
     gcc \
     postgresql-devel \
     zeromq3-devel \
     libxml2-devel \
     libxslt-devel \
     libcurl-devel \
     redhat-rpm-config \
     gcc-c++ \
     python-virtualenv \
     libffi-devel \
     libpng \
     libpng-devel \
     freetype-devel \
     openssl-devel \
     libselinux-python \
     yum \
     sshpass

venv_path=$1

if [[ -z $venv_path ]]; then
  venv_path="./.cfme_perf"
fi

if [[ ! -d $venv_path ]]; then
  virtualenv -p python2 $venv_path
fi

echo "export PYTHONPATH='`pwd`'" | tee -a ${venv_path%/}/bin/activate
echo "export PYTHONDONTWRITEBYTECODE=yes" | tee -a ${venv_path%/}/bin/activate

. ${venv_path%/}/bin/activate

PYCURL_SSL_LIBRARY=nss pip install -Ur ./requirements.txt

echo "Run '. ${venv_path%/}/bin/activate' to load the virtualenv"
