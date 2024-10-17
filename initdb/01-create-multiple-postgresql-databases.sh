#!/bin/bash
set -e
set -u

function create_user_and_database() {
    local database=$1
    echo "Creating user and database '$database'"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
CREATE DATABASE $database;
GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
    echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        if [ "$db" = "$POSTGRES_DB" ]; then
            echo "Main database already initialized: $db"
        else
            create_user_and_database $db
        fi
    done
    echo "Multiple databases created"
fi

# Initialize the main database
if [ -n "$POSTGRES_DB" ]; then
    echo "Initializing main database: $POSTGRES_DB"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
\i /docker-entrypoint-initdb.d/02-create-tables.sql
\i /docker-entrypoint-initdb.d/03-insert-data.sql
EOSQL
fi

## Initialize the test database
#if [ -n "$POSTGRES_DB_TEST" ]; then
#    echo "Initializing test database: $POSTGRES_DB_TEST"
#    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB_TEST" <<-EOSQL
#\i /docker-entrypoint-initdb.d/tests/initdbtest/create_table_test.sql
#\i /docker-entrypoint-initdb.d/tests/initdbtest/insert_test.sql
#EOSQL
#fi