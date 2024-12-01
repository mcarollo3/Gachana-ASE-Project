#!/bin/bash

# Carica i segreti in variabili di ambiente
export MYSQL_ROOT_PASSWORD=$(cat /run/secrets/db_root_password)
export MYSQL_USER=$(cat /run/secrets/db_user)
export MYSQL_PASSWORD=$(cat /run/secrets/db_password)

chmod 644 /etc/mysql/my.cnf

exec "$@"
