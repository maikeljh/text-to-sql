import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from openpyxl import Workbook
from tabulate import tabulate

# === CONFIGURATION ===
CSV_FILE = "test.csv"              # CSV input file path
OUTPUT_FILE = "query_test_results.xlsx"   # Output Excel file path
DB_CONFIG = {
    "dbname": "adventure-works",
    "user": "postgres",
    "host": "localhost",
    "port": "5432"
}
# =======================

# Load CSV
df = pd.read_csv(CSV_FILE)

# Prepare Excel workbook
wb = Workbook()
ws = wb.active
ws.title = "Query Results"
ws.append(["Query", "Output Columns", "Status", "Error"])

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    for idx, row in df.iterrows():
        query = row['Answer']
        print(f"\n[{idx+1}] Executing Query:\n{query}")
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc.name for desc in cursor.description]
            ws.append([query, str(columns), "Success", ""])
            
            if results:
                table = tabulate(results, headers="keys", tablefmt="grid", showindex=False)
                print(table)
            else:
                print("No rows returned.")

        except Exception as e:
            print(f"Query failed: {e}")
            ws.append([query, "", "Failed", str(e)])
            conn.rollback()

    cursor.close()
    conn.close()

except Exception as conn_err:
    print(f"Connection failed: {conn_err}")
    ws.append(["", "", "Connection Failed", str(conn_err)])

# Save results
wb.save(OUTPUT_FILE)
print(f"\n✅ Results saved to {OUTPUT_FILE}")
