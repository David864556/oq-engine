# Copyright (C) 2019-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
FROM python:3.8.6 AS compile-image
LABEL maintainer="GEM Foundation <devops@openquake.org>" \
       vendor="GEM Foundation"
RUN apt-get update &&  apt-get install -y --no-install-recommends build-essential gcc git libcap-dev ssh dnsutils telnet sudo netbase && \
    useradd -m -u 1000 -G sudo -s /bin/bash openquake && echo "openquake ALL=(ALL) NOPASSWD:ALL" | sudo tee -a /etc/sudoers
ARG oq_branch=master
# Setup the virtualenv
RUN python -m venv /opt/openquake
ENV PATH="/opt/openquake/bin:$PATH"
ENV LANG en_US.UTF-8
WORKDIR /opt
#clone repository and install engine
RUN git clone https://github.com/gem/oq-engine.git --depth=1 --branch $oq_branch && cd oq-engine && \
     python3 install.py server --version=master
#
ADD ./openquake.cfg /opt/openquake/openquake.cfg
USER openquake
ENV HOME /home/openquake
WORKDIR ${HOME}
RUN mkdir oqdata 
#
ADD scripts/oq-db_start.sh ${HOME}
ADD scripts/oq-start.sh ${HOME}
# if want to copy engine src to home
#ADD oq-engine-master ${HOME}
ENTRYPOINT ["/bin/bash"]
