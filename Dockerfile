FROM debian:6

MAINTAINER Ferran Pegueroles

RUN apt-get update && \
    apt-get install -qq -y \
    python \
    python-dev \
    python-reportlab \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    python-pip \
    cups-bsd \
    postgresql-client \
    htmldoc \
    build-essential && \
    apt-get clean && \
    rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN mkdir -p /app/
WORKDIR /app/

ADD egenix-mx-base-3.2.8.tar.gz /app/
ADD libxml2-python-2.6.9.tar.gz /app/
ADD psycopg-1.1.21.tar.gz /app/

RUN cd egenix-mx-base-3.2.8 && \
    python setup.py install

RUN cd psycopg-1.1.21 && \
    ./configure --with-postgres-libraries=/usr/lib \
                --with-postgres-includes=/usr/include/postgresql \
                --with-mxdatetime-includes=../egenix-mx-base-3.2.8/mx/DateTime/mxDateTime/ && \
    make && make install

RUN cd libxml2-python-2.6.9 && \
    python setup.py install

ADD requirements.txt /app/
RUN pip install -r requirements.txt

ADD tinyerp-server /app/tinyerp-server/
ADD terp_serverrc /app/tinyerp-server/bin/
ADD run.sh /app/

VOLUME ["/app/tinyerp-server"]
VOLUME ["/home"]

# bitcoind testnet ports
EXPOSE 7070 7071

CMD ["./run.sh"]
