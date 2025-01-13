import psycopg2
import Configs
 
# Establishing the connection
def schema_td():

    conn = psycopg2.connect(
        host=Configs.db_host,
        port=Configs.db_port,
        database=Configs.db_name,
        user=Configs.db_user,
        password=Configs.db_password,
        options= '-c search_path=DEMO2,public'
    )
    
    # Creating a cursor object
    cur = conn.cursor()
    
    # Query to fetch schema information
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'TD_DEMO_SCHEMA'
        ORDER BY table_name, ordinal_position;
    """)
    
    # Fetching the results
    schema_info = cur.fetchall()
    
    # Displaying the schema information
    #print(schema_info)
    # for table, column, data_type in schema_info:
    #     print(f"Table: {table}, Column: {column}, Data Type: {data_type}")
    
    # Closing the cursor and connection
    cur.close()
    conn.close()
    #print(schema_info)
    return str(schema_info)

schema_td()