FROM debian/eol:jessie

MAINTAINER Ferran Pegueroles

RUN apt-get update && \
    apt-get install -qq -y \
    python \
    python-dev \
    libkrb5-dev \
    zlib1g-dev \
    python-libxml2 \
    python-libxslt1 \
    libxslt-dev \
    curl \
    cups-bsd \
    ssh \
    htmldoc \
    postgresql-client-common \
    build-essential && \
    apt-get clean && \
    rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

RUN curl "https://bootstrap.pypa.io/pip/2.7/get-pip.py" -o "get-pip.py"
RUN python get-pip.py

RUN mkdir -p /app/
WORKDIR /app/

ADD libssl0.9.8_0.9.8o-4squeeze23_amd64.deb /app/
ADD libssl-dev_0.9.8o-4squeeze23_amd64.deb /app/
ADD libpq5_8.4.21-0squeeze1_amd64.deb /app/
ADD postgresql-client-8.4_8.4.21-0squeeze1_amd64.deb /app/
ADD libpq-dev_8.4.21-0squeeze1_amd64.deb /app/

RUN dpkg -i /app/libssl-dev_0.9.8o-4squeeze23_amd64.deb \
            /app/libssl0.9.8_0.9.8o-4squeeze23_amd64.deb \
            /app/postgresql-client-8.4_8.4.21-0squeeze1_amd64.deb \
            /app/libpq5_8.4.21-0squeeze1_amd64.deb \
            /app/libpq-dev_8.4.21-0squeeze1_amd64.deb

ADD egenix-mx-base-3.2.8.tar.gz /app/
RUN cd egenix-mx-base-3.2.8 && \
    python setup.py install

ADD psycopg-1.1.21.tar.gz /app/
RUN cd psycopg-1.1.21 && \
    ./configure --with-postgres-libraries=/usr/lib \
                --with-postgres-includes=/usr/include/postgresql \
                --with-mxdatetime-includes=../egenix-mx-base-3.2.8/mx/DateTime/mxDateTime/ && \
    make && make install

# ADD libxml2-python-2.6.9.tar.gz /app/
# RUN cd libxml2-python-2.6.9 && \
#     python setup.py install

ADD requirements.txt /app/
RUN pip install -r requirements.txt

ADD tinyerp-server /app/tinyerp-server/
ADD terp_serverrc /app/tinyerp-server/bin/
ADD run.sh /app/

VOLUME ["/app/tinyerp-server"]

# bitcoind testnet ports
EXPOSE 7070 7071

CMD ["./run.sh"]
