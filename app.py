from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import os
from send_report import weekly_report, share_shopping_lists
from collections import defaultdict
import json
from flask import flash, get_flashed_messages
import subprocess

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'fbbdtaa.db')
app.secret_key = 'super-secret-key'

# ----------------------
# Utility Functions
# ----------------------
def query_individual_items():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT * FROM individual_items
        WHERE status = 'live'
        ORDER BY best_before ASC
    """)
    items = c.fetchall()
    conn.close()

    past, today_items, tomorrow_items, future = [], [], [], []
    for item in items:
        bb = datetime.strptime(item['best_before'], '%Y-%m-%d').date()
        if bb < today:
            past.append(item)
        elif bb == today:
            today_items.append(item)
        elif bb == tomorrow:
            tomorrow_items.append(item)
        else:
            future.append(item)

    return past, today_items, tomorrow_items, future

def query_leftovers():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT * FROM leftovers
        WHERE status = 'live'
        ORDER BY best_before ASC
    """)
    items = c.fetchall()
    conn.close()

    past, today_items, tomorrow_items, future = [], [], [], []
    for item in items:
        bb = datetime.strptime(item['best_before'], '%Y-%m-%d').date()
        if bb < today:
            past.append(item)
        elif bb == today:
            today_items.append(item)
        elif bb == tomorrow:
            tomorrow_items.append(item)
        else:
            future.append(item)

    return past, today_items, tomorrow_items, future

def load_categories():
    with open(os.path.join(os.path.dirname(__file__), 'data', 'categories.json')) as f:
        return json.load(f)

def save_categories(data):
    with open(os.path.join(os.path.dirname(__file__), 'data', 'categories.json'), 'w') as f:
        json.dump(data, f, indent=2)

# ----------------------
# Routes
# ----------------------
from collections import defaultdict

@app.route('/')
def index():
    past, today_items, tomorrow_items, future = query_individual_items()
    lo_past, lo_today, lo_tomorrow, lo_future = query_leftovers()

    # Build a dict of categories → items
    future_by_cat = defaultdict(list)
    for item in future:
        future_by_cat[item['category']].append(item)

    return render_template(
        'dashboard.html',
        past=past,
        today_items=today_items,
        tomorrow_items=tomorrow_items,
        future=future_by_cat,       # now a dict!
        lo_past=lo_past,
        lo_today=lo_today,
        lo_tomorrow=lo_tomorrow,
        lo_future=lo_future
    )

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        location = request.form['location']
        category = request.form['category']
        item = request.form['item']
        best_before = request.form['best_before']
        added_by = request.form['added_by']
        barcode = request.form.get('barcode', '')

        high_risk_categories = ["Chicken & Poultry", "Fish & Seafood", "Meat"]
        high_risk = 'yes' if category in high_risk_categories else 'no'

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO individual_items (
                location, category, item, best_before,
                added_by, high_risk, barcode
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (location, category, item, best_before, added_by, high_risk, barcode))
        conn.commit()
        conn.close()

        if request.form['action'] == 'add_another':
            return redirect('/add')
        else:
            return redirect('/')

    # This part only runs on GET
    CATEGORY_ITEMS = load_categories()
    sorted_categories = sorted(CATEGORY_ITEMS.keys())
    sorted_items_map = {
        category: sorted(CATEGORY_ITEMS[category])
        for category in sorted_categories
    }

    return render_template('add_item.html',
                           categories=sorted_categories,
                           items_map=sorted_items_map)

@app.route('/mark-dead/<int:item_id>', methods=['POST'])
def mark_dead(item_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE individual_items SET status = 'dead' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/leftovers', methods=['GET', 'POST'])
def leftovers():
    if request.method == 'POST':
        action = request.form.get('action')

        if action in ['add', 'add_another']:
            location = request.form['location']
            made_on = request.form['made_on']
            best_before = request.form['best_before']
            added_by = request.form['added_by']
            title = request.form['title']

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO leftovers (
                    location, made_on, best_before, added_by, title, added_on
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (location, made_on, best_before, added_by, title))
            conn.commit()
            conn.close()

            if action == 'add_another':
                return redirect('/leftovers')
            else:
                return redirect('/')

        elif action == 'mark_dead':
            lo_id = request.form.get('lo_id')
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE leftovers SET status = 'dead' WHERE id = ?", (lo_id,))
            conn.commit()
            conn.close()
            return redirect('/')

    return render_template('leftovers.html')

@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM individual_items WHERE status = 'dead' ORDER BY best_before DESC")
    items = c.fetchall()

    c.execute("SELECT * FROM leftovers WHERE status = 'dead' ORDER BY best_before DESC")
    leftovers = c.fetchall()

    conn.close()
    return render_template('history.html', items=items, leftovers=leftovers)

@app.route('/shopping-list', methods=['GET', 'POST'])
def shopping_list():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            item = request.form['item']
            added_by = request.form['added_by']
            meal = request.form.get('meal') or 'Misc'
            c.execute("INSERT INTO shopping_list (item, added_by, meal) VALUES (?, ?, ?)", (item, added_by, meal))
            conn.commit()

        elif action == 'send':
            c.execute("SELECT item FROM shopping_list")
            items = [row['item'] for row in c.fetchall()]
            if items:
                share_shopping_lists(items)
                c.execute("DELETE FROM shopping_list")
                conn.commit()

        elif action == 'remove':
            item_id = request.form.get('item_id')
            if item_id:
                c.execute("DELETE FROM shopping_list WHERE id = ?", (item_id,))
                conn.commit()

    c.execute("SELECT * FROM shopping_list ORDER BY meal, added_on ASC")
    rows = c.fetchall()
    conn.close()

    items_by_meal = defaultdict(list)
    for row in rows:
        meal = row['meal'] if row['meal'] else 'Misc'
        items_by_meal[meal].append(row)

    return render_template('shopping_list.html', items_by_meal=items_by_meal)


@app.route('/send-email', methods=['POST'])
def send_email_now():
    weekly_report()
    return redirect('/')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    categories = load_categories()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # --- Handle form actions ---
    if request.method == 'POST':
        action = request.form.get('action')

        # SMTP Settings Update
        if action == 'update_smtp':
            smtp_server = request.form['smtp_server']
            smtp_port = request.form['smtp_port']
            user = request.form['user']
            password = request.form['pass']

            c.execute("DELETE FROM smtp_settings")  # Wipe existing settings
            c.execute("""
                INSERT INTO smtp_settings (smtp_server, smtp_port, user, pass)
                VALUES (?, ?, ?, ?)
            """, (smtp_server, smtp_port, user, password))
            conn.commit()
            flash("SMTP settings updated successfully.")

        # Add a recipient
        elif action == 'add_recipient':
            email = request.form.get('new_email', '').strip()
            if email:
                c.execute("INSERT INTO smtp_recipients (email) VALUES (?)", (email,))
                conn.commit()
                flash(f"Recipient '{email}' added.")

        # Delete a recipient
        elif action == 'delete_recipient':
            email_id = request.form['recipient_id']
            c.execute("DELETE FROM smtp_recipients WHERE id = ?", (email_id,))
            conn.commit()
            flash("Recipient removed.")

        # Maintenance
        elif action == 'cleanup':
            subprocess.run(['python3', 'cleanup_db.py', '--cleanup'])
            flash("Cleanup complete.")
        elif action == 'backup':
            subprocess.run(['python3', 'cleanup_db.py', '--backup'])
            flash("Backup created.")
        elif action == 'reset':
            confirm = request.form.get('confirm')
            if confirm == 'yes':
                subprocess.run(['python3', 'cleanup_db.py', '--reset'], input='yes\n', text=True)
                flash("Database reset.")
            else:
                flash("Reset cancelled.")

        # Category Management
        elif action == 'add_category':
            new_cat = request.form['new_category'].strip()
            if new_cat and new_cat not in categories:
                categories[new_cat] = []
        elif action == 'delete_category':
            cat = request.form['category_to_delete']
            if cat in categories:
                del categories[cat]
        elif action == 'add_item':
            cat = request.form['item_category']
            new_item = request.form['new_item'].strip()
            if cat in categories and new_item and new_item not in categories[cat]:
                categories[cat].append(new_item)
        elif action == 'delete_item':
            cat = request.form['delete_item_category']
            item = request.form['item_to_delete']
            if cat in categories and item in categories[cat]:
                categories[cat].remove(item)

        save_categories(categories)
        conn.close()
        return redirect('/admin')

    # Query current SMTP settings
    c.execute("SELECT * FROM smtp_settings ORDER BY added_on DESC LIMIT 1")
    smtp_settings = c.fetchone()

    # Query recipients
    c.execute("SELECT * FROM smtp_recipients ORDER BY email ASC")
    recipients = c.fetchall()

    conn.close()

    return render_template('admin.html', categories=categories, smtp=smtp_settings, recipients=recipients)


if __name__ == '__main__':
    app.run(debug=True)
