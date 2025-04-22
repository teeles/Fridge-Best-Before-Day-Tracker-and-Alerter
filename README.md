# FridgeWatch  
_**Fridge Best Before Day Tracker and Alerter**_

FridgeWatch (or Fridge Best Before Day Tracker and Alerter for long) is a lightweight web app designed to track fridge and freezer items, manage leftovers, plan meals, and alert household members before anything goes off. It’s built with Flask and designed to run on a Raspberry Pi or Ubuntu machine using a simple deployment script.

---

## Features

- Track individual fridge/freezer items and leftovers meals.
- Minimal simple design that works on most devices. 
- Simple admin UI.
- Smart date warnings: Past, Today, Tomorrow, and Fresh.
- Email alerts at 6AM daily with a summary of expiring items (via cron job)
- Categorized shopping list with meal grouping, email shopping lists to multiple accounts. 

---

## Installation (Recommended: Raspberry Pi or Ubuntu)

The whole app setup process has been automated, all you need is a working RaspberyPI or VM idelly running Ubuntu Server.

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/fridgewatch/main/setup.sh | sudo bash
```

This will:

- Install required dependencies (Python, Git, Nginx, SQLite, etc.)
- Set up a system user called `fridge`
- Clone the repo to `/opt/fridgewatch`
- Set up a virtual environment
- Create the SQLite database
- Configure and launch Gunicorn + Nginx
- Set up a daily cron job for email reports

---

## Accessing the App

Once installed, visit:

```
http://<your-raspberrypi-ip>/
```

or just:

```
http://fridgewatch.local/
```

> (You can change the hostname and proxy config via Nginx.)

---

## SMTP Configuration

Visit the `/admin` page to add SMTP credentials. You’ll need:

- SMTP server (e.g., smtp.gmail.com)
- Port (usually 587)
- Username and password
- Add recipients to receive email reports

SMTP details are securely stored in the database and **never** hardcoded.

---

## Dev Setup

To run locally (macOS or Linux):

```bash
git clone https://github.com/YOUR_USERNAME/fridgewatch.git
cd fridgewatch
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
python app.py
```

Or to use Gunicorn:

```bash
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

---

## Folder Structure

```
fridgewatch/
├── app.py
├── init_db.py
├── send_report.py
├── cleanup_db.py
├── requirements.txt
├── data/
│   └── categories.json
├── db/
│   └── fbbdtaa.db
├── backups/
├── static/
│   └── style.css
├── templates/
│   ├── add_item.html
│   ├── admin.html
│   ├── dashboard.html
│   ├── history.html
│   ├── leftovers.html
│   └── shopping_list.html
```

---

## Cron Job

A daily email report is sent at 06:00:

```bash
0 6 * * * /opt/fridgewatch/venv/bin/python3 /opt/fridgewatch/send_report.py --report
```

---

## Admin Functions

All available at `/admin`:

- Cleanup old data
- Backup the database
- Reset all records (with confirmation)
- Manage categories and shopping list meals
- Configure SMTP and manage recipients

---

## To Do List

- Catagorise the firdge and freezer items on the dashbord do its easier to view. 
- Remove the "Added By" and migrate to user logins. 
- Add better logging (currently /log/).
- Add CSV upload function for categories.json
- Make Shopping list UX and UI better. 
- Add in function to change the daily report times. 
- Alphabetise all of the lists on items and leftovers. 


