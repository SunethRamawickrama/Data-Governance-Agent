import os
import psycopg2
from dotenv import load_dotenv
from dataclasses import dataclass

@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict]
    row_count: int

'''Given the db name, returns the connection to that db which will be use to execute queries'''
def get_connection (db_name: str, host: str=None, port:int=None):

    load_dotenv()
    prefix = db_name.upper().replace("-", "_")
    conn = None
    try:

        user = os.getenv(f'{prefix}_USER')
        password = os.getenv(f'{prefix}_PASSWORD')
        port = os.getenv(f'{prefix}_PORT') if not port else port
        host = os.getenv(f'{prefix}_HOST') if not host else host
    
        # Establish the connection
        conn = psycopg2.connect(host=host, port=port, user=user,
            password=password, dbname=db_name)
      
        return conn

    except psycopg2.DatabaseError as e:
        raise Exception(f"Connection error: {str(e)}")
        

def execute_query (db_name: str, sql:str, params=None):
    conn = get_connection(db_name=db_name)
    try:
        with conn.cursor() as crsr:
            crsr.execute(sql, params)
            if crsr.description:
                columns = [desc[0] for desc in crsr.description]
                rows = [dict(zip(columns, row)) for row in crsr.fetchall()]
                conn.commit() 
                return QueryResult(columns=columns, rows=rows, row_count=len(rows))

            conn.commit()
            return QueryResult(columns=[], rows=[], row_count=crsr.rowcount)
        
    except Exception as e:
        raise e
    finally:
            conn.close()