import psycopg2
import pandas as pd
from langchain_community.utilities.sql_database import SQLDatabase
import Configs

def execute(sql_query):

    try:
        conn = psycopg2.connect(
            host=Configs.db_host,
            port=Configs.db_port,
            database=Configs.db_name,
            user=Configs.db_user,
            password=Configs.db_password
        )

        cur = conn.cursor()
        cur.execute('''{}'''.format(sql_query))
        rows = cur.fetchall()
        columns = [description[0] for description in cur.description]
        df=pd.DataFrame(rows, columns=columns)  
        #print(columns)
        print(df.head())
        cur.close()
        conn.close()
        return df

    except Exception as e:
        print(e)

#execution('SELECT * FROM "TD_DEMO_SCHEMA"."SRC1_FILE"')

def execute(query,parameters=''):
    db_user = Configs.db_user
    db_password = Configs.db_password
    db_host =Configs.db_host
    db_port = Configs.db_port
    db_name = Configs.db_name
    db = SQLDatabase.from_uri(f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",schema='TD_DEMO_SCHEMA')
    
# db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",sample_rows_in_table_info=1,include_tables=['customers','orders'],custom_table_info={'customers':"customer"})


    response=db.run(query,parameters=parameters,include_columns='true')
    #df=pd.DataFrame(eval(response))
    return (response)