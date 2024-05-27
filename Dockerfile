FROM ubuntu:18.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update

# locale
RUN apt-get -y install locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get install -y python-pip

# added before the full folder, so caching of pip installation
# isn't broke when cached of the full zombsole folder breaks
ADD requirements.txt /home/docker/requirements.txt

WORKDIR /home/docker
RUN pip install -r requirements.txt

# now add the rest of the folder
ADD . /home/docker/zombsole/
WORKDIR /home/docker/zombsole

RUN pip install /home/docker/zombsole

EXPOSE 8000
ENTRYPOINT ["zombsole"]
