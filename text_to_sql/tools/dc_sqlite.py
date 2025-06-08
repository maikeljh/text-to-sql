import sqlite3

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
    conn = sqlite3.connect(r'')
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]

    fks = []
    for t in tables:
        cur.execute(f"PRAGMA foreign_key_list('{t}')")
        fkl = cur.fetchall()
        for fk in fkl:
            fks.append( (t, fk[2], fk[3], fk[4]) )

    total_tables = len(tables)
    total_columns = 0
    total_PK = 0
    total_SK = 0
    total_FK = 0
    total_Index = 0
    sum_DT = 0
    total_RC_1_1 = 0
    total_RC_1_M = len(fks)

    DC_TC = []

    for t in tables:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = cur.fetchall()
        total_columns += len(cols)

        cur.execute(f"PRAGMA index_list('{t}')")
        idxs = cur.fetchall()

        cur.execute(f"PRAGMA foreign_key_list('{t}')")
        fkl = cur.fetchall()

        colc = 0
        for _, name, dtype, notnull, dflt, pk in cols:
            base = dtype.split('(')[0].lower()
            weight = DT_WEIGHTS.get(base, 0.22)
            sum_DT += weight
            colc += weight

        PK = sum(1 for c in cols if c[-1])
        SK = sum(1 for idx in idxs if not idx[2])
        FK = len(fkl)
        Index = len(idxs)

        total_PK += PK
        total_SK += SK
        total_FK += FK
        total_Index += Index

        keyc = 0.28*PK + 0.11*SK + 0.50*FK + 0.11*Index
        TC = 0.75*colc + 0.25*keyc
        DC_TC.append(TC)

    RC = 0.25*total_RC_1_1 + 0.75*total_RC_1_M

    DC = 0.75*sum(DC_TC) + 0.25*RC

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
