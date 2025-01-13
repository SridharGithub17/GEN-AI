
import sys
import Configs

print(sys.path)

import psycopg2
# Connect to PostgreSQL

def connect_pg():
    pg_conn = psycopg2.connect(
        dbname=Configs.db_name,
        user=Configs.db_user,
        password=Configs.db_password,
        host=Configs.db_host,  # or your DB host
        port=Configs.db_port
    )

    pg_cursor = pg_conn.cursor()
    # pg_cursor.execute('SELECT * FROM "TD_DEMO_SCHEMA"."FIN_ACCT_TXNS"')
    # rows = pg_cursor.fetchall()
    # print(rows)
    return pg_cursor