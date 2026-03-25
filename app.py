from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import json
from database import (
    init_db, save_checkin, get_last_checkin, get_streak,
    get_today_quicklogs, save_career_progress, load_career_progress,
    create_incident, update_incident, get_today_incidents,
    get_missing_pillars_today, get_incident_by_id
)
import sqlite3
from datetime import datetime
load_dotenv()

app = Flask(__name__)
init_db()

GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'

# SHADOW personality — used for all incident conversations
SHADOW_SYSTEM_PROMPT = """
You are SHADOW — the internal voice of ASCEND, a brutal self-analysis system.
Your job is to extract 4 specific things from the user about a behavioral incident:
1. The exact situation (what happened)
2. What options were available to them
3. What they actually chose and why
4. Why they didn't choose the better option — this is the most important part.
   Sometimes they didn't know the better option existed (clarity gap).
   Sometimes they knew but still avoided it (resistance).

Rules:
- Ask only ONE question at a time. Never list multiple questions.
- Be direct, sharp, honest. Like a smart friend — not a therapist, not a form.
- No sugarcoating. No generic encouragement.
- Keep questions short. Make them feel like a real conversation.
- Once you have all 4 elements clearly, respond with EXACTLY this JSON and nothing else:

{
  "complete": true,
  "situation": "...",
  "options_available": "...",
  "choice_made": "...",
  "resistance_reason": "...",
  "clarity_gap": <1-5>,
  "resistance_score": <1-5>
}

clarity_gap: How aware were they of the better option? 1=fully aware, 5=had no idea
resistance_score: Did they act on what they knew? 1=executed cleanly, 5=knew but completely avoided

Do not output the JSON until you genuinely have all 4 elements from the conversation.
"""


# ── V1 ROUTES (untouched) ───────────────────────────────────────────────────────

# When user goes to / show home screen
@app.route('/')
def home():
    return render_template('home.html')

# When user goes to checkin show checkin page
@app.route('/checkin')
def checkin():
    return render_template('checkin.html')

# When user goes to analyze reply with groq api feedback
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
        GROQ_URL,
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': GROQ_MODEL,
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

# When user submits a quick log save it
@app.route('/quicklog', methods=['POST'])
def quicklog():
    data = request.get_json()
    note = data.get('note', '')
    pillar = data.get('pillar', 'general')
    from database import save_quicklog
    save_quicklog(pillar, note)
    return jsonify({'status': 'saved'})

# Fetch today's quick logs
@app.route('/getlogs')
def getlogs():
    logs = get_today_quicklogs()
    return jsonify({'logs': logs})

# Fetch yesterday's check-in data so checkin page can show personalized questions
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

TRACK1_DSA = [
    {"problem": "Two Sum — DONE ✅", "link": "#"},
    {"problem": "Best Time to Buy and Sell Stock", "link": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/"},
    {"problem": "Contains Duplicate", "link": "https://leetcode.com/problems/contains-duplicate/"},
    {"problem": "Maximum Subarray", "link": "https://leetcode.com/problems/maximum-subarray/"},
    {"problem": "Move Zeroes", "link": "https://leetcode.com/problems/move-zeroes/"},
    {"problem": "Single Number", "link": "https://leetcode.com/problems/single-number/"},
    {"problem": "Find All Numbers Disappeared in Array", "link": "https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/"},
    {"problem": "Running Sum of 1D Array", "link": "https://leetcode.com/problems/running-sum-of-1d-array/"},
    {"problem": "Shuffle the Array", "link": "https://leetcode.com/problems/shuffle-the-array/"},
    {"problem": "Kids With the Greatest Number of Candies", "link": "https://leetcode.com/problems/kids-with-the-greatest-number-of-candies/"},
]

TRACK2_LEARN = [
    {"task": "Write 5 Python functions from scratch — no AI, no googling syntax", "link": "https://www.w3schools.com/python/python_functions.asp"},
    {"task": "Loops — write 3 programs using for loops and 3 using while loops", "link": "https://www.w3schools.com/python/python_for_loops.asp"},
    {"task": "Lists — create, access, modify, sort, loop through 10 exercises", "link": "https://www.w3schools.com/python/python_lists.asp"},
    {"task": "Dictionaries — create, access, modify, loop through 10 exercises", "link": "https://www.w3schools.com/python/python_dictionaries.asp"},
    {"task": "File handling — read a file, write to a file, append to a file", "link": "https://www.w3schools.com/python/python_file_handling.asp"},
]

TRACK3_BUILD = [
    {"task": "Open ASCEND app.py — write a comment above every route explaining what it does in plain English"},
    {"task": "Open ASCEND database.py — explain every function in comments without AI help"},
    {"task": "Draw on paper — how ASCEND works end to end from user clicking submit to getting response"},
    {"task": "Modify ASCEND feedback prompt — make it more brutal without breaking anything"},
    {"task": "Add error handling to one route in app.py — what happens if Groq API fails?"},
]

TRACK4_VISIBILITY = [
    {"task": "LeetCode account created and Two Sum solved ✅"},
    {"task": "Write ASCEND README — problem it solves, tech stack, how to run it, screenshots"},
    {"task": "Make ASCEND GitHub repo public with README"},
    {"task": "Create LinkedIn — photo, headline, education, add ASCEND as project"},
    {"task": "Connect with 20 people from your college on LinkedIn"},
]

career_progress = load_career_progress()

# When user goes to /career show career page
@app.route('/career')
def career():
    return render_template('career.html')

# Give mission according to user's progression
@app.route('/get_mission')
def get_mission():
    t1 = career_progress["track1"]
    t2 = career_progress["track2"]
    t3 = career_progress["track3"]
    t4 = career_progress["track4"]

    dsa = TRACK1_DSA[t1] if t1 < len(TRACK1_DSA) else {"problem": "Phase 1 Complete — Phase 2 unlocked", "link": "#"}
    learn = TRACK2_LEARN[t2] if t2 < len(TRACK2_LEARN) else {"task": "Track 2 Phase 1 Complete", "link": "#"}
    build = TRACK3_BUILD[t3] if t3 < len(TRACK3_BUILD) else {"task": "Track 3 Phase 1 Complete"}
    visibility = TRACK4_VISIBILITY[t4] if t4 < len(TRACK4_VISIBILITY) else {"task": "Track 4 Phase 1 Complete"}

    return jsonify({
        'dsa': dsa['problem'],
        'dsa_link': dsa.get('link', '#'),
        'learn': learn['task'],
        'learn_link': learn.get('link', '#'),
        'build': build['task'],
        'visibility': visibility['task']
    })

# Submit career mission response and get Groq feedback
@app.route('/career_submit', methods=['POST'])
def career_submit():
    data = request.get_json()
    groq_api_key = os.getenv('GROQ_API_KEY')

    t1 = career_progress["track1"]
    t2 = career_progress["track2"]

    if data.get('dsa_status') in ['solved', 'partial']:
        career_progress["track1"] = min(t1 + 1, len(TRACK1_DSA) - 1)
    if data.get('learn_status') in ['done', 'partial']:
        career_progress["track2"] = min(t2 + 1, len(TRACK2_LEARN) - 1)
    if data.get('build_status') == 'done':
        career_progress["track3"] = min(career_progress["track3"] + 1, len(TRACK3_BUILD) - 1)
    if data.get('visibility_status') == 'done':
        career_progress["track4"] = min(career_progress["track4"] + 1, len(TRACK4_VISIBILITY) - 1)

    prompt = f"""
You are ASCEND Career Engine — brutally honest career coach for SHADOW.
Target: 15 LPA in 18 months. Tier 3 college. AI/automation focus.
Projects: ASCEND (personal AI system), PLC automation for industrial client.
Current DSA progress: Problem {career_progress['track1']} of 10 in Phase 1.

Today's report:
DSA: {data['dsa_status']} — {data['dsa_notes']}
LEARN: {data['learn_status']} — {data['learn_notes']}
BUILD: {data['build_status']} — {data['build_notes']}

Give brutally honest assessment. Call out if skipped.
End with one specific tip for tomorrow based on today's performance.
"""

    response = requests.post(
        GROQ_URL,
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': GROQ_MODEL,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300
        }
    )

    result = response.json()
    feedback = result.get('choices', [{}])[0].get('message', {}).get('content', str(result))
    save_career_progress(career_progress['track1'], career_progress['track2'], career_progress['track3'], career_progress['track4'])
    return jsonify({'feedback': feedback})


# ── V2 INCIDENT ROUTES ──────────────────────────────────────────────────────────

# Called when user submits a new incident from Quick Log
# Creates the incident in DB and returns the first AI question
@app.route('/start_incident', methods=['POST'])
def start_incident():
    data = request.get_json()
    pillar = data.get('pillar', 'awareness')
    note = data.get('note', '')
    groq_api_key = os.getenv('GROQ_API_KEY')

    # Save incomplete incident to DB, get its ID
    incident_id = create_incident(pillar, note)

    # Build initial conversation — user's raw note is the first message
    conversation = [
        {'role': 'user', 'content': note}
    ]

    # Ask Groq for the first follow-up question
    response = requests.post(
        GROQ_URL,
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': GROQ_MODEL,
            'messages': [
                {'role': 'system', 'content': SHADOW_SYSTEM_PROMPT},
                {'role': 'user', 'content': note}
            ],
            'max_tokens': 150
        }
    )

    result = response.json()
    ai_reply = result.get('choices', [{}])[0].get('message', {}).get('content', '')

    # Save conversation so far to incident
    conversation.append({'role': 'assistant', 'content': ai_reply})
    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    c.execute(f'UPDATE incidents SET conversation = {p} WHERE id = {p}',
              (json.dumps(conversation), incident_id))
    conn.commit()
    conn.close()

    return jsonify({
        'incident_id': incident_id,
        'ai_question': ai_reply,
        'complete': False
    })


# Called on every user reply during the incident conversation
# Either asks the next question OR extracts all 4 elements and saves them
@app.route('/continue_incident', methods=['POST'])
def continue_incident():
    data = request.get_json()
    incident_id = data.get('incident_id')
    user_message = data.get('message', '')
    groq_api_key = os.getenv('GROQ_API_KEY')

    # Load existing conversation for this incident
    incident = get_incident_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404

    conversation = json.loads(incident['conversation'])

    # Add user's new message to conversation
    conversation.append({'role': 'user', 'content': user_message})

    # Build messages for Groq — system prompt + full conversation history
    messages = [{'role': 'system', 'content': SHADOW_SYSTEM_PROMPT}] + conversation

    response = requests.post(
        GROQ_URL,
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': GROQ_MODEL,
            'messages': messages,
            'max_tokens': 300
        }
    )

    result = response.json()
    ai_reply = result.get('choices', [{}])[0].get('message', {}).get('content', '')

    # Check if Groq returned the completion JSON
    try:
        # Try to parse the reply as JSON — means AI has all 4 elements
        parsed = json.loads(ai_reply)
        if parsed.get('complete'):
            # Save all extracted structured data to the incident
            state_code = update_incident(
                incident_id,
                parsed.get('situation', ''),
                parsed.get('options_available', ''),
                parsed.get('choice_made', ''),
                parsed.get('resistance_reason', ''),
                parsed.get('clarity_gap', 3),
                parsed.get('resistance_score', 3),
                json.dumps(conversation)
            )
            return jsonify({
                'complete': True,
                'state_code': state_code,
                'situation': parsed.get('situation', ''),
                'clarity_gap': parsed.get('clarity_gap'),
                'resistance_score': parsed.get('resistance_score')
            })
    except (json.JSONDecodeError, TypeError):
        # Not JSON — AI is still asking questions
        pass

    # Still in conversation — save updated conversation and return next question
    conversation.append({'role': 'assistant', 'content': ai_reply})

    from database import get_conn
    conn = get_conn()
    c = conn.cursor()
    database_url = os.getenv('DATABASE_URL')
    p = '%s' if database_url else '?'
    c.execute(f'UPDATE incidents SET conversation = {p} WHERE id = {p}',
              (json.dumps(conversation), incident_id))
    conn.commit()
    conn.close()

    return jsonify({
        'complete': False,
        'ai_question': ai_reply
    })


# Called by Check-in page to know which pillars are missing today
# Also returns today's incidents summary for the debrief
@app.route('/checkin_context', methods=['GET'])
def checkin_context():
    missing = get_missing_pillars_today()
    incidents = get_today_incidents()

    return jsonify({
        'missing_pillars': missing,
        'incidents_today': len(incidents),
        'incidents': incidents
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
