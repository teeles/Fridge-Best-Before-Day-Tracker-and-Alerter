import sqlite3
from datetime import datetime

DB_PATH = 'db/fbbdtaa.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

def check_table_exists(name):
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return c.fetchone() is not None

# Track success/failure
errors = []

# Individual Items Table
c.execute('''
CREATE TABLE IF NOT EXISTS individual_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT DEFAULT 'live',
    location TEXT NOT NULL,
    category TEXT NOT NULL,
    item TEXT NOT NULL,
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    best_before DATE NOT NULL,
    added_by TEXT NOT NULL,
    high_risk TEXT NOT NULL,
    barcode TEXT
)
''')
if check_table_exists('individual_items'):
    print("Created 'individual_items'")
else:
    print("Failed to create 'individual_items'")
    errors.append('individual_items')

# Leftovers Table
c.execute('''
CREATE TABLE IF NOT EXISTS leftovers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT DEFAULT 'live',
    location TEXT NOT NULL,
    title TEXT NOT NULL,
    made_on DATETIME NOT NULL,
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    best_before DATE NOT NULL,
    added_by TEXT NOT NULL
)
''')
if check_table_exists('leftovers'):
    print("Created 'leftovers'")
else:
    print("Failed to create 'leftovers'")
    errors.append('leftovers')

# Shopping List Table
c.execute('''
CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    added_by TEXT,
    meal TEXT DEFAULT 'Misc',
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
if check_table_exists('shopping_list'):
    print("Created 'shopping_list'")
else:
    print("Failed to create 'shopping_list'")
    errors.append('shopping_list')

c.execute('''
CREATE TABLE IF NOT EXISTS smtp_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    smtp_server TEXT,
    smtp_port TEXT,
    user TEXT,
    pass TEXT,
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
if check_table_exists('smtp_settings'):
    print("Created 'smtp_settings'")
else:
    print("Failed to create 'smtp_settings'")
    errors.append('smtp_settings')

c.execute('''
CREATE TABLE IF NOT EXISTS smtp_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
if check_table_exists('smtp_recipients'):
    print("Created 'smtp_recipients'")
else:
    print("Failed to create 'smtp_recipients'")
    errors.append('smtp_recipients')

conn.commit()
conn.close()

# Final result
if errors:
    print("\nWARNING _ Some tables failed to create:")
    for table in errors:
        print(f"  - {table}")
    print("Please review init_db.py and re-run.")
else:
    print("Database initialization complete and successful.")