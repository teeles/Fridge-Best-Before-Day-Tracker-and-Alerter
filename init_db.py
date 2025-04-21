import sqlite3
from datetime import datetime

conn = sqlite3.connect('db/fbbdtaa.db')
c = conn.cursor()

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

# Leftovers Table
c.execute('''
CREATE TABLE IF NOT EXISTS leftovers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT DEFAULT 'live',
    location TEXT NOT NULL,
    title TEXT NOT NULL,
    made_on DATETIME NOT NULL,
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP
    best_before DATE NOT NULL,
    added_by TEXT NOT NULL
)
''')

#Shopping Lists
c.execute('''
CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    added_by TEXT,
    meal TEXT DEFAULT 'Misc',
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("Database initialized")