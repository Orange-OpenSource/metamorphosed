FROM ubuntu:24.04

# docker build -t jheinecke/metamorphosed:4.6.1 .
# grype jheinecke/metamorphosed:4.6.1 --only-fixed | egrep "High|Criti"
# trivy image jheinecke/metamorphosed:4.6.1 --scanners vuln --timeout 15m --severity MEDIUM,HIGH,CRITICAL --ignore-unfixed

# edit mode
# docker run --rm -d -t --name metamorphosed -p 4567:4567 -v <absolute/path/to/datadir>:/data --env AMRFILE=testamr.txt  jheinecke/metamorphosed:4.6.1

# comparison (the directory in COMPAREWITH must be /data ! (internal path of docker image))
# docker run --rm -d -t --name metamorphosed -p 4567:4567 -v <absolute/path/to/datadir>:/data --env AMRFILE=testamr.txt   --env COMPAREWITH="--compare /data/testamr.txt.2" jheinecke/metamorphosed:4.6.1



LABEL org.label-schema.name="metAMoRphosED"
LABEL org.label-schema.description="An Abstract Meaning Representations editor"
LABEL org.label-schema.summary="AMR annotation/validation/comparison"
LABEL org.label-schema.vendor="Johannes Heinecke <johannes.heinecke@orange.com>"
LABEL org.label-schema.version="${DOCKER_VERSION}"
LABEL org.label-schema.schema_version="RC1"

RUN apt-get update \
	&& apt-get -y upgrade \
        && apt-get -y install graphviz python3-minimal python3-pip python3.12-venv git wget libffi-dev \
        && apt-get clean
RUN python3 -m venv /opt/venv

WORKDIR /wikidata
COPY requirements.txt .
RUN . /opt/venv/bin/activate && pip --no-cache-dir install -r requirements.txt

RUN git clone https://github.com/Orange-OpenSource/metamorphosed.git

#RUN apt-get -y install wget
WORKDIR /wikidata/metamorphosed
RUN cd propbank-frames/frames; \
	git checkout ad2bafa4c9c9c58cc1bc89; \
	wget https://raw.githubusercontent.com/propbank/propbank-frames/development/frames/AMR-UMR-91-rolesets.xml; \
	cd ../..

RUN  . /opt/venv/bin/activate &&  ./metamorphosed/installJQ.py


EXPOSE 4567
ENV AMRLIB_URL=
ENV PROPERTY_LABELS=
ENV QUAL_LABELS=

#HEALTHCHECK --interval=60s --timeout=3s --retries=1 \
#  CMD curl --silent --fail --noproxy '*' http://localhost:3500/status | grep  '"status": "ok"' || exit 1


CMD . /opt/venv/bin/activate && exec ./metamorphosed_server.py \
	--pbframes ./propbank-frames/frames/ \
	--reifications ./metamorphosed/data/reification-table.txt \
        -f /data/$AMRFILE \
	$COMPAREWITH


