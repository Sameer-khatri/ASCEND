import os
from datetime import datetime

def get_conn():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        import psycopg2
        return psycopg2.connect(database_url)
    else:
        import sqlite3
        return sqlite3.connect('ascend.db')

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id SERIAL PRIMARY KEY,
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS quicklogs (
            id SERIAL PRIMARY KEY,
            date TEXT,
            time TEXT,
            pillar TEXT,
            note TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_checkin(awareness, strategy, cognition, emotional, network, development, feedback):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO checkins 
        (date, awareness, strategy, cognition, emotional, network, development, feedback)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        datetime.now().strftime('%Y-%m-%d'),
        awareness, strategy, cognition,
        emotional, network, development, feedback
    ))
    conn.commit()
    conn.close()

def get_last_checkin():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM checkins ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row

def get_streak():
    conn = get_conn()
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

def save_quicklog(pillar, note):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO quicklogs (date, time, pillar, note)
        VALUES (%s, %s, %s, %s)
    ''', (
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%H:%M'),
        pillar,
        note
    ))
    conn.commit()
    conn.close()

def get_today_quicklogs():
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT time, pillar, note FROM quicklogs WHERE date = %s ORDER BY id DESC', (today,))
    logs = [{'time': r[0], 'pillar': r[1], 'note': r[2]} for r in c.fetchall()]
    conn.close()
    return logs