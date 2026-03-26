import sqlite3

conn = sqlite3.connect("spark-alpha-demo-seed-full-school.db")
cur = conn.cursor()

print("\nTABLES\n------")

cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""")

tables = [row[0] for row in cur.fetchall()]

for table in tables:
    print(f"\n{table}")
    print("-" * len(table))

    cur.execute(f"PRAGMA table_info({table})")

    for col in cur.fetchall():
        cid, name, ctype, notnull, default, pk = col
        print(f"{name:20} {ctype:10} NOT NULL:{notnull}")

conn.close()
