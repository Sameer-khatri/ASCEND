from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import json
from database import init_db, save_checkin, get_last_checkin, get_streak, get_today_quicklogs
import sqlite3
from datetime import datetime
load_dotenv()

app = Flask(__name__)
init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/checkin')
def checkin():
    return render_template('checkin.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    groq_api_key = os.getenv('GROQ_API_KEY')

    quick_logs = get_today_quicklogs()
    quick_log_text = ""
    if quick_logs:
        quick_log_text = "\n\nQUICK LOGS FROM TODAY:\n"
        for log in quick_logs:
            quick_log_text += f"- [{log['time']}] {log['pillar'].upper()}: {log['note']}\n"

    prompt = f"""
You are ASCEND — a brutally honest personal development system for a user called SHADOW.
You do not motivate. You analyze and confront.
Based on today's entries AND quick logs, give direct, harsh, specific feedback in 4-5 lines.
No sugarcoating. No encouragement without evidence.

AWARENESS: {data['awareness']}
STRATEGY: {data['strategy']}
COGNITION: {data['cognition']}
EMOTIONAL: {data['emotional']}
NETWORK: {data['network']}
DEVELOPMENT: {data['development']}
{quick_log_text}
Analyze patterns across ALL entries including quick logs. Call out weaknesses directly. Be specific not generic.
For each weakness — give one specific action they should have taken instead. Be direct and practical. No theory.
"""

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300
        }
    )

    result = response.json()
    feedback = result.get('choices', [{}])[0].get('message', {}).get('content', str(result))

    save_checkin(
        data['awareness'], data['strategy'], data['cognition'],
        data['emotional'], data['network'], data['development'],
        feedback
    )
    return jsonify({'feedback': feedback})

@app.route('/quicklog', methods=['POST'])
def quicklog():
    data = request.get_json()
    note = data.get('note', '')
    pillar = data.get('pillar', 'general')
    from database import save_quicklog
    save_quicklog(pillar, note)
    return jsonify({'status': 'saved'})

@app.route('/getlogs')
def getlogs():
    logs = get_today_quicklogs()
    return jsonify({'logs': logs})

@app.route('/get_context')
def get_context():
    last = get_last_checkin()
    if not last:
        return jsonify({'has_context': False})
    return jsonify({
        'has_context': True,
        'date': last[1],
        'awareness': last[2],
        'strategy': last[3],
        'cognition': last[4],
        'emotional': last[5],
        'network': last[6],
        'development': last[7],
        'feedback': last[8]
    })

@app.route('/career')
def career():
    return render_template('career.html')

@app.route('/get_mission')
def get_mission():
    # Week 1 default mission — hardcoded for now, will adapt later
    return jsonify({
        'dsa': 'Two Sum — Easy — Array problem. Given an array of integers, return indices of two numbers that add up to target.',
        'dsa_link': 'https://leetcode.com/problems/two-sum/',
        'learn': 'Python functions and loops — write 5 functions from scratch today without googling syntax.',
        'learn_link': 'https://www.w3schools.com/python/python_functions.asp',
        'build': 'Open ASCEND code. Read through app.py and understand every route. Write comments explaining what each one does.'
    })

@app.route('/career_submit', methods=['POST'])
def career_submit():
    data = request.get_json()
    groq_api_key = os.getenv('GROQ_API_KEY')

    prompt = f"""
You are ASCEND Career Engine — brutally honest career coach for SHADOW.
Target: 15 LPA in 18 months. Currently at Level 0 coding. Tier 3 college.
Projects: ASCEND (personal AI system), PLC automation for industrial client.

Today's report:
DSA: {data['dsa_status']} — {data['dsa_notes']}
LEARN: {data['learn_status']} — {data['learn_notes']}
BUILD: {data['build_status']} — {data['build_notes']}

Give brutally honest assessment of today. Then give tomorrow's specific mission:
1. Tomorrow's DSA problem with exact name
2. Tomorrow's learning focus with exact resource
3. Tomorrow's build task

Be specific. No vague advice. Real actionable tasks only.
If they skipped today — call it out directly before giving tomorrow's mission.
"""

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 400
        }
    )

    result = response.json()
    feedback = result.get('choices', [{}])[0].get('message', {}).get('content', str(result))
    return jsonify({'feedback': feedback})
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)