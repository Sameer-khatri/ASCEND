import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('ascend.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            awareness TEXT,
            strategy TEXT,
            cognition TEXT,
            emotional TEXT,
            network TEXT,
            development TEXT,
            feedback TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_checkin(awareness, strategy, cognition, emotional, network, development, feedback):
    conn = sqlite3.connect('ascend.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO checkins 
        (date, awareness, strategy, cognition, emotional, network, development, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d'),
        awareness, strategy, cognition,
        emotional, network, development, feedback
    ))
    conn.commit()
    conn.close()

def get_last_checkin():
    conn = sqlite3.connect('ascend.db')
    c = conn.cursor()
    c.execute('SELECT * FROM checkins ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row

def get_streak():
    conn = sqlite3.connect('ascend.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT date FROM checkins ORDER BY date DESC')
    dates = [row[0] for row in c.fetchall()]
    conn.close()
    
    if not dates:
        return 0
    
    streak = 1
    for i in range(len(dates) - 1):
        d1 = datetime.strptime(dates[i], '%Y-%m-%d')
        d2 = datetime.strptime(dates[i+1], '%Y-%m-%d')
        if (d1 - d2).days == 1:
            streak += 1
        else:
            break
    return streak