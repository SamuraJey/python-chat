from sqlalchemy import create_engine
from testcontainers.postgres import PostgresContainer

with PostgresContainer("postgres:17-alpine") as postgres:
    e = create_engine(postgres.get_connection_url())
    with e.connect() as connection:
        result = connection.exec_driver_sql("SELECT version()")
        print(result.fetchone())
