import sqlite3
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import argparse
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'db', 'fbbdtaa.db')

# SMTP function
def smtp_send(subject, html_body):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM smtp_settings ORDER BY added_on DESC LIMIT 1")
    settings = c.fetchone()

    c.execute("SELECT email FROM smtp_recipients")
    recipients = [row['email'] for row in c.fetchall()]

    conn.close()

    if not settings:
        raise Exception("SMTP settings not found.")

    if not recipients:
        raise Exception("No recipients found.")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = "The Fridge"
    msg['To'] = ", ".join(recipients)

    part = MIMEText(html_body, 'html')
    msg.attach(part)

    try:
        with smtplib.SMTP(settings['smtp_server'], int(settings['smtp_port'])) as server:
            server.starttls()
            server.login(settings['user'], settings['pass'])
            server.send_message(msg)
        return True
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

# Email shopping list function
def share_shopping_lists(items):
    if not items:
        return

    html = "<h2>Shopping List</h2><ul>"
    for item in items:
        html += f"<li>{item}</li>"
    html += "</ul>"

    smtp_send("Shopping List", html)

# Weekly or auto trigger report function
def weekly_report():
    def fetch_data():
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)

        def group_items(query):
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(query)
            rows = c.fetchall()
            conn.close()

            past, today_list, tomorrow_list, future = [], [], [], []
            for row in rows:
                bb = datetime.strptime(row['best_before'], '%Y-%m-%d').date()
                if bb < today:
                    past.append(row)
                elif bb == today:
                    today_list.append(row)
                elif bb == tomorrow:
                    tomorrow_list.append(row)
                else:
                    future.append(row)
            return past, today_list, tomorrow_list, future

        item_query = "SELECT * FROM individual_items WHERE status = 'live'"
        lo_query = "SELECT * FROM leftovers WHERE status = 'live'"

        items = group_items(item_query)
        leftovers = group_items(lo_query)

        return items, leftovers

    def format_section(title, rows, is_leftover=False):
        if not rows:
            return ""
        output = f"<h3>{title}</h3><ul>"
        for row in rows:
            name = row['title'] if is_leftover else row['item']
            who = row['added_by']
            loc = row['location']
            bb = row['best_before']
            risk = row['high_risk'] if 'high_risk' in row.keys() else 'no'
            label = f" <strong style='color:red;'>(High Risk)</strong>" if risk == 'yes' else ""
            output += f"<li><strong>{name}</strong> – {bb} in the {loc} (added by {who}){label}</li>"
        output += "</ul>"
        return output

    items, leftovers = fetch_data()
    past, today, tomorrow, future = items
    lo_past, lo_today, lo_tomorrow, _ = leftovers  # ignore future leftovers
    now = datetime.now().strftime('%d-%m-%y %H:%M')

    html = f"<h2>Fridge Report: {now}</h2>"
    html += format_section("What's In My Fridge (Still Fresh)", future)
    html += format_section("Stuff you might need to bin", past)
    html += format_section("Stuff you need to use today", today)
    html += format_section("Stuff you need to use tomorrow", tomorrow)
    html += format_section("Leftovers Already Past Best Before", lo_past, True)
    html += format_section("Left Overs You Need To Eat Today", lo_today, True)
    html += format_section("Left Overs You Need To Eat Tomorrow", lo_tomorrow, True)

    if html.strip():
        smtp_send("FridgeWatch Daily Report", html)

# --------------------------------------
# 🔁 Manual Trigger
# --------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='F.B.B.D.T.A.A. Email Sender')
    parser.add_argument('--report', action='store_true', help='Send the daily fridge report')
    parser.add_argument('--shopping-list', action='store_true', help='Send the shopping list email')

    args = parser.parse_args()

    if args.report:
        weekly_report()

    if args.shopping_list:
        share_shopping_lists()

    if not args.report and not args.shopping_list:
        print("No option provided. Use --report or --shopping-list")

