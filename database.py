import os
from datetime import datetime
import json

# This function connects ASCEND with database
def get_conn():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        import psycopg2
        return psycopg2.connect(database_url)
    else:
        import sqlite3
        return sqlite3.connect('ascend.db')

# This function performs queries, like creating checkin, quicklogs, incidents table if not exist
def init_db():
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # PostgreSQL syntax
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

        # V2 — incidents table
        # clarity_gap     : 1-5 — did user know the better option? 1=fully aware, 5=no idea
        # resistance_score: 1-5 — did user act on what they knew? 1=executed, 5=avoided
        # state_code      : combined pattern
        #   1 = low clarity  + low resistance  → unaware, not resisting (needs education)
        #   2 = low clarity  + high resistance → confused AND avoiding (needs attention)
        #   3 = high clarity + high resistance → knows but won't act (most dangerous)
        #   4 = high clarity + low resistance  → knows and executes (growth state)
        # conversation    : full JSON of AI <-> user dialogue
        # is_complete     : 0 = conversation in progress, 1 = all 4 elements extracted
        c.execute('''
    CREATE TABLE IF NOT EXISTS incidents (
        id SERIAL PRIMARY KEY,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        pillar TEXT NOT NULL,
        situation TEXT,
        options_available TEXT,
        choice_made TEXT,
        resistance_reason TEXT,
        clarity_gap INTEGER,
        resistance_score INTEGER,
        state_code INTEGER,
        total_score INTEGER DEFAULT 0,
        score_label TEXT,
        pillars TEXT,
        conversation TEXT,
        is_complete INTEGER DEFAULT 0
    )
''')

    else:
        # SQLite syntax
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

        c.execute('''
            CREATE TABLE IF NOT EXISTS quicklogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                time TEXT,
                pillar TEXT,
                note TEXT
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                pillar TEXT NOT NULL,
                situation TEXT,
                options_available TEXT,
                choice_made TEXT,
                resistance_reason TEXT,
                clarity_gap INTEGER,
                resistance_score INTEGER,
                state_code INTEGER,
                total_score INTEGER DEFAULT 0,
                score_label TEXT,
                pillars TEXT,
                conversation TEXT,
                is_complete INTEGER DEFAULT 0
            )
        ''')

    conn.commit()
    conn.close()

# This function saves daily checkins to the checkin table
def save_checkin(awareness, strategy, cognition, emotional, network, development, feedback):
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    c.execute(f'''
        INSERT INTO checkins 
        (date, awareness, strategy, cognition, emotional, network, development, feedback)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
    ''', (
        datetime.now().strftime('%Y-%m-%d'),
        awareness, strategy, cognition,
        emotional, network, development, feedback
    ))
    conn.commit()
    conn.close()

# This function fetches last checkin from checkin table
def get_last_checkin():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM checkins ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    return row

# This function maintains streak of user
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

# This function saves quick logs to quicklogs table
def save_quicklog(pillar, note):
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    c.execute(f'''
        INSERT INTO quicklogs (date, time, pillar, note)
        VALUES ({p}, {p}, {p}, {p})
    ''', (
        datetime.now().strftime('%Y-%m-%d'),
        datetime.now().strftime('%H:%M'),
        pillar,
        note
    ))
    conn.commit()
    conn.close()

# This function is used to show today's quick logs that user submitted
def get_today_quicklogs():
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    c.execute(f'SELECT time, pillar, note FROM quicklogs WHERE date = {p} ORDER BY id DESC', (today,))
    logs = [{'time': r[0], 'pillar': r[1], 'note': r[2]} for r in c.fetchall()]
    conn.close()
    return logs

# This function saves career progress of user on different tracks in career_progress table
def save_career_progress(track1, track2, track3, track4):
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    pk = 'SERIAL' if database_url else 'INTEGER'
    ai = '' if database_url else 'AUTOINCREMENT'
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS career_progress (
            id {pk} PRIMARY KEY {ai},
            track1 INTEGER DEFAULT 1,
            track2 INTEGER DEFAULT 0,
            track3 INTEGER DEFAULT 0,
            track4 INTEGER DEFAULT 1,
            updated_at TEXT
        )
    ''')
    c.execute('DELETE FROM career_progress')
    c.execute(f'''
        INSERT INTO career_progress (track1, track2, track3, track4, updated_at)
        VALUES ({p}, {p}, {p}, {p}, {p})
    ''', (track1, track2, track3, track4, datetime.now().strftime('%Y-%m-%d %H:%M')))
    conn.commit()
    conn.close()

# This function fetches last tracks detail and on basis of it new mission is given to user
def load_career_progress():
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    pk = 'SERIAL' if database_url else 'INTEGER'
    ai = '' if database_url else 'AUTOINCREMENT'
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS career_progress (
            id {pk} PRIMARY KEY {ai},
            track1 INTEGER DEFAULT 1,
            track2 INTEGER DEFAULT 0,
            track3 INTEGER DEFAULT 0,
            track4 INTEGER DEFAULT 1,
            updated_at TEXT
        )
    ''')
    c.execute('SELECT track1, track2, track3, track4 FROM career_progress LIMIT 1')
    row = c.fetchone()
    conn.close()
    if row:
        return {'track1': row[0], 'track2': row[1], 'track3': row[2], 'track4': row[3]}
    return {'track1': 1, 'track2': 0, 'track3': 0, 'track4': 1}


# ── V2 INCIDENT FUNCTIONS ───────────────────────────────────────────────────────

# Creates a new incomplete incident and returns its ID so the conversation
# page can keep updating it as the AI extracts more data turn by turn
def create_incident(pillar, initial_note):
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # PostgreSQL — use RETURNING to get new id
        c.execute('''
            INSERT INTO incidents (date, time, pillar, situation, conversation, is_complete)
            VALUES (%s, %s, %s, %s, %s, 0) RETURNING id
        ''', (
            datetime.now().strftime('%Y-%m-%d'),
            datetime.now().strftime('%H:%M'),
            pillar,
            initial_note,
            '[]'
        ))
        incident_id = c.fetchone()[0]
    else:
        # SQLite — use lastrowid
        c.execute('''
            INSERT INTO incidents (date, time, pillar, situation, conversation, is_complete)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (
            datetime.now().strftime('%Y-%m-%d'),
            datetime.now().strftime('%H:%M'),
            pillar,
            initial_note,
            '[]'
        ))
        incident_id = c.lastrowid

    conn.commit()
    conn.close()
    return incident_id

# Updates an incident with all 4 extracted elements after AI conversation ends
# Auto-calculates state_code from clarity_gap and resistance_score
def update_incident(incident_id, situation, options_available, choice_made,
                    resistance_reason, clarity_gap, resistance_score, 
                    total_score, score_label, pillars, conversation):

    high_clarity    = clarity_gap <= 2        # low gap = high awareness
    high_resistance = resistance_score >= 3   # high score = high resistance

    if high_clarity and not high_resistance:
        state_code = 4   # knows and executes — growth
    elif high_clarity and high_resistance:
        state_code = 3   # knows but won't act — most dangerous
    elif not high_clarity and high_resistance:
        state_code = 2   # confused and avoiding — needs attention
    else:
        state_code = 1   # unaware, not resisting — needs education

    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'

    c.execute(f'''
    UPDATE incidents SET
        situation         = {p},
        options_available = {p},
        choice_made       = {p},
        resistance_reason = {p},
        clarity_gap       = {p},
        resistance_score  = {p},
        state_code        = {p},
        total_score       = {p},
        score_label       = {p},
        pillars           = {p},
        conversation      = {p},
        is_complete       = 1
    WHERE id = {p}
''', (
    situation, options_available, choice_made,
    resistance_reason, clarity_gap, resistance_score,
    state_code, total_score, score_label,
    json.dumps(pillars), conversation, incident_id
))
    conn.commit()
    conn.close()
    return state_code

# Returns all complete incidents for today
# Used by Check-in to know which pillars are covered and which are missing
def get_today_incidents():
    conn = get_conn()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'

    c.execute(f'''
        SELECT id, time, pillar, situation, options_available, choice_made,
               resistance_reason, clarity_gap, resistance_score, state_code
        FROM incidents
        WHERE date = {p} AND is_complete = 1
        ORDER BY id ASC
    ''', (today,))
    rows = c.fetchall()
    conn.close()
    return [
        {
            'id': r[0], 'time': r[1], 'pillar': r[2],
            'situation': r[3], 'options_available': r[4],
            'choice_made': r[5], 'resistance_reason': r[6],
            'clarity_gap': r[7], 'resistance_score': r[8],
            'state_code': r[9]
        }
        for r in rows
    ]

# Returns which of the 6 pillars have NO complete incident today
# Used by Check-in AI to ask targeted resistance questions for missing pillars
def get_missing_pillars_today():
    ALL_PILLARS = {'awareness', 'strategy', 'cognition', 'emotional', 'network', 'development'}
    incidents   = get_today_incidents()
    covered     = {i['pillar'].lower() for i in incidents}
    missing     = ALL_PILLARS - covered
    return list(missing)

# Fetches a single incident by ID
# Used during active AI conversation to load and update state turn by turn
def get_incident_by_id(incident_id):
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'

    c.execute(f'SELECT * FROM incidents WHERE id = {p}', (incident_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
    'id': row[0], 'date': row[1], 'time': row[2], 'pillar': row[3],
    'situation': row[4], 'options_available': row[5], 'choice_made': row[6],
    'resistance_reason': row[7], 'clarity_gap': row[8],
    'resistance_score': row[9], 'state_code': row[10],
    'total_score': row[11], 'score_label': row[12], 'pillars': row[13],
    'conversation': row[14], 'is_complete': row[15]
}