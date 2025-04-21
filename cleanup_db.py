import sqlite3
from datetime import datetime, timedelta
import os
import argparse
import shutil

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'fbbdtaa.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    six_months_ago = datetime.now() - timedelta(days=180)
    twelve_months_ago = datetime.now() - timedelta(days=365)

    c.execute("""
        DELETE FROM individual_items
        WHERE status = 'dead'
        AND added_on < ?
    """, (six_months_ago.strftime('%Y-%m-%d %H:%M:%S'),))

    c.execute("""
        DELETE FROM leftovers
        WHERE status = 'dead'
        AND added_on < ?
    """, (twelve_months_ago.strftime('%Y-%m-%d %H:%M:%S'),))

    conn.commit()
    conn.close()
    print("Database cleanup complete.")

def reset_all(require_confirmation=True):
    if require_confirmation:
        confirm = input("Are you sure you want to delete ALL records from the database? Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Reset cancelled.")
            return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM individual_items")
    c.execute("DELETE FROM leftovers")
    c.execute("DELETE FROM shopping_list")
    conn.commit()
    conn.close()
    print("All records removed. Database reset complete.")

def backup_db():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = f'fbbdtaa_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup created: {backup_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='F.B.B.D.T.A.A. Maintenance Script')
    parser.add_argument('--cleanup', action='store_true', help='Delete old dead records only')
    parser.add_argument('--reset', action='store_true', help='Delete ALL data (confirmation required)')
    parser.add_argument('--backup', action='store_true', help='Create a timestamped backup of the database')

    args = parser.parse_args()

    if args.cleanup:
        cleanup()
    elif args.reset:
        reset_all(require_confirmation=True)
    elif args.backup:
        backup_db()
    else:
        print("No action specified. Use --cleanup, --reset, or --backup")
