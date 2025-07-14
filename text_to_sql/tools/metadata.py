import psycopg2
import json
import os
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

DATABASE = "northwind"
db_key = DATABASE.upper().replace("-", "_")

conn_params = {
    "host": os.getenv(f"DB_HOST_{db_key}"),
    "port": int(os.getenv(f"DB_PORT_{db_key}")),
    "dbname": os.getenv(f"DB_DATABASE_{db_key}"),
    "user": os.getenv(f"DB_USER_{db_key}"),
    "password": os.getenv(f"DB_PASSWORD_{db_key}")
}

def get_columns_metadata(cursor):
    cursor.execute("""
        SELECT 
            c.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable = 'YES' AS nullable,
            c.column_default,
            CASE WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PRIMARY KEY' ELSE NULL END AS attribute
        FROM 
            information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
            ON c.table_name = kcu.table_name
            AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON kcu.constraint_name = tc.constraint_name
            AND kcu.table_schema = tc.table_schema
        WHERE 
            c.table_schema = 'public'
        ORDER BY 
            c.table_name, c.ordinal_position;
    """)
    return cursor.fetchall()

def get_column_descriptions(cursor):
    cursor.execute("""
        SELECT
            cls.relname AS table_name,
            att.attname AS column_name,
            des.description AS column_description
        FROM 
            pg_catalog.pg_class cls
        JOIN pg_catalog.pg_namespace nsp
            ON nsp.oid = cls.relnamespace
        JOIN pg_catalog.pg_attribute att
            ON att.attrelid = cls.oid
        LEFT JOIN pg_catalog.pg_description des
            ON des.objoid = att.attrelid AND des.objsubid = att.attnum
        WHERE 
            nsp.nspname = 'public'
            AND att.attnum > 0
            AND NOT att.attisdropped;
    """)
    return {(row[0], row[1]): row[2] for row in cursor.fetchall()}

def get_table_descriptions(cursor):
    cursor.execute("""
        SELECT
            cls.relname AS table_name,
            des.description AS table_description
        FROM 
            pg_catalog.pg_class cls
        JOIN pg_catalog.pg_namespace nsp
            ON nsp.oid = cls.relnamespace
        LEFT JOIN pg_catalog.pg_description des
            ON des.objoid = cls.oid AND des.objsubid = 0
        WHERE 
            nsp.nspname = 'public';
    """)
    return dict(cursor.fetchall())

def get_foreign_keys(cursor):
    cursor.execute("""
        SELECT
            tc.table_name AS foreign_table,
            ccu.table_name AS primary_table,
            kcu.column_name AS foreign_column,
            ccu.column_name AS primary_column
        FROM 
            information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE 
            tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public';
    """)
    fks = cursor.fetchall()
    
    ref_map = defaultdict(dict)
    relation_map = defaultdict(list)

    for ft, pt, fc, pc in fks:
        ref_str = f"{pt}({pc})"
        join_str = f"{ft}.{fc} = {pt}.{pc}"
        ref_map[ft][fc] = ref_str
        relation_map[ft].append({
            "foreign_table": pt,
            "primary_table": ft,
            "join": join_str,
            "description": ""
        })

    return ref_map, relation_map

def build_metadata():
    with psycopg2.connect(**conn_params) as conn:
        cursor = conn.cursor()

        columns = get_columns_metadata(cursor)
        col_descriptions = get_column_descriptions(cursor)
        tbl_descriptions = get_table_descriptions(cursor)
        ref_map, relation_map = get_foreign_keys(cursor)

        tables = defaultdict(lambda: {"columns": [], "relations": []})

        for table_name, column_name, data_type, nullable, default, attribute in columns:
            col_key = (table_name, column_name)
            description = col_descriptions.get(col_key, "")
            references = ref_map.get(table_name, {}).get(column_name)
            column_entry = {
                "key": column_name,
                "name": column_name,
                "type": data_type,
                "nullable": nullable,
                "attributes": [attribute] if attribute else [],
                "references": references,
                "description": description or ""
            }
            tables[table_name]["columns"].append(column_entry)

        metadata = {
            "database": conn_params["dbname"],
            "tables": []
        }

        for table_name, data in tables.items():
            metadata["tables"].append({
                "name": table_name,
                "description": tbl_descriptions.get(table_name, ""),
                "columns": data["columns"],
                "relations": relation_map.get(table_name, [])
            })

        return metadata

if __name__ == "__main__":
    metadata = build_metadata()
    with open(f"{DATABASE}.json", "w") as f:
        json.dump(metadata, f, indent=2)
