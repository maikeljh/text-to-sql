import psycopg2

DT_WEIGHTS = {
    'bit':.01, 'tinyint':.06,'year':.06,'smallint':.11,
    'char':.12,'binary':.12,'tinytext':.12,'tinyblob':.12,
    'text':.16,'blob':.16,'varchar':.16,'varbinary':.16,
    'mediumint':.17,'int':.22,'float':.22,'timestamp':.22,
    'mediumtext':.24,'mediumblob':.24,
    'bigint':.44,'double':.44,'decimal':.44,'real':.44,
    'numeric':.44,'datetime':.44,'time':.44,
    'longtext':.48,'longblob':.48
}

def calc():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="academic",
        user="postgres",
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
    """)
    tables = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT conrelid::regclass AS table_from,
               confrelid::regclass AS table_to,
               conname
        FROM pg_constraint
        WHERE contype = 'f'
    """)
    fks = cur.fetchall()

    total_tables = len(tables)
    total_columns = 0
    total_PK = 0
    total_SK = 0
    total_FK = len(fks)
    total_Index = 0
    sum_DT = 0
    total_RC_1_1 = 0
    total_RC_1_M = len(fks)

    DC_TC = []

    for t in tables:
        cur.execute(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
        """, (t,))
        cols = cur.fetchall()
        total_columns += len(cols)

        colc = 0
        for name, dtype in cols:
            base = dtype.lower()
            weight = DT_WEIGHTS.get(base, 0.22)
            sum_DT += weight
            colc += weight

        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
        """, (t,))
        pk_cols = cur.fetchall()
        PK = len(pk_cols)

        cur.execute(f"""
            SELECT COUNT(*)
            FROM pg_index i
            JOIN pg_class c ON c.oid = i.indexrelid
            WHERE i.indrelid = '{t}'::regclass
              AND NOT i.indisprimary
        """)
        Index = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*)
            FROM pg_constraint
            WHERE contype = 'f'
              AND conrelid = %s::regclass
        """, (t,))
        FK = cur.fetchone()[0]

        SK = 0

        total_PK += PK
        total_SK += SK
        total_Index += Index

        keyc = 0.28*PK + 0.11*SK + 0.50*FK + 0.11*Index
        TC = 0.75*colc + 0.25*keyc
        DC_TC.append(TC)

    RC = 0.25*total_RC_1_1 + 0.75*total_RC_1_M
    DC = 0.75*sum(DC_TC) + 0.25*RC

    # Print Summary
    print("\n===== Summary Database =====\n")
    print(f"Tabel              : {total_tables}")
    print(f"Kolom              : {total_columns}")
    print(f"Relasi             : {len(fks)}")
    print(f"PK                 : {total_PK}")
    print(f"SK                 : {total_SK}")
    print(f"FK                 : {total_FK:.2f}")
    print(f"Index              : {total_Index}")
    print(f"Tipe Data          : {sum_DT:.2f}")
    print(f"Tipe Relasi        : {RC:.2f}")
    print(f"Database Complexity: {DC:.2f}")

    conn.close()

if __name__ == '__main__':
    calc()
