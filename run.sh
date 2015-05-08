#!/bin/bash

export DB_NAME=${DB_NAME:-ttc}
export DB_USER=${DB_USER:-ttc}
export DB_HOST=${DB_HOST:-db}
export DB_PORT=${DB_PORT:-5432}
export DB_PASSWORD=${DB_PASSWORD}

cd tinyerp-server/bin
python tinyerp-server.py --config=terp_serverrc \
    --database=$DB_NAME \
    --db_user=$DB_USER \
    --db_host=$DB_HOST \
    --db_password=$DB_PASSWORD \
    --db_port=$DB_PORT
