from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import json
from database import (
    init_db, save_checkin, get_last_checkin, get_streak,
    get_today_quicklogs, save_career_progress, load_career_progress,
    create_incident, update_incident, get_today_incidents,
    get_missing_pillars_today, get_incident_by_id, get_conn
)
import sqlite3
from datetime import datetime
load_dotenv()

app = Flask(__name__)
init_db()

GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'

def call_groq(messages, max_tokens=400):
    groq_api_key = os.getenv('GROQ_API_KEY')
    response = requests.post(
        GROQ_URL,
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': GROQ_MODEL,
            'messages': messages,
            'max_tokens': max_tokens
        }
    )
    result = response.json()
    return result.get('choices', [{}])[0].get('message', {}).get('content', '')


# ── V1 ROUTES (untouched) ──────────────────────────────────────────────────────

# when user go to / show home screen
@app.route('/')
def home():
    return render_template('home.html')

# when user go to checkin show checkin page
@app.route('/checkin')
def checkin():
    return render_template('checkin.html')

@app.route('/checkin_v2_page')
def checkin_v2_page():
    return render_template('checkin_v2.html')

# when user go to analyze reply to the user with groq api key
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()

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

    feedback = call_groq([{'role': 'user', 'content': prompt}], max_tokens=300)

    save_checkin(
        data['awareness'], data['strategy'], data['cognition'],
        data['emotional'], data['network'], data['development'],
        feedback
    )
    return jsonify({'feedback': feedback})

# saves a quick log entry to the database
@app.route('/quicklog', methods=['POST'])
def quicklog():
    data = request.get_json()
    note = data.get('note', '')
    pillar = data.get('pillar', 'general')
    from database import save_quicklog
    save_quicklog(pillar, note)
    return jsonify({'status': 'saved'})

# fetches today's quick logs
@app.route('/getlogs')
def getlogs():
    logs = get_today_quicklogs()
    return jsonify({'logs': logs})

# fetches yesterday's check-in data so check-in page can show personalized questions
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

# when user go to /career show him career page
@app.route('/career')
def career():
    return render_template('career.html')

# give mission according to progression
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

# submit career mission response and get groq feedback
@app.route('/career_submit', methods=['POST'])
def career_submit():
    data = request.get_json()

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

    feedback = call_groq([{'role': 'user', 'content': prompt}], max_tokens=300)
    save_career_progress(
        career_progress['track1'], career_progress['track2'],
        career_progress['track3'], career_progress['track4']
    )
    return jsonify({'feedback': feedback})


# ── V2 ROUTES ─────────────────────────────────────────────────────────────────

# SHADOW's personality — used in every incident conversation
SHADOW_SYSTEM_PROMPT = """
You are SHADOW — the internal voice inside ASCEND, a personal behavioral intelligence system.
Your job: extract 4 things from every incident the user logs — Situation, Options, Choice, Resistance.

PERSONALITY:
- Direct, sharp, zero fluff. Like a smart friend who doesn't let you off the hook.
- Never a therapist. Never a cheerleader. Never preachy.
- Ask one question at a time. Short. Pointed.
- Sound human, not like a form.
- Never repeat or rephrase a question you already asked.

YOUR GOAL PER CONVERSATION:
Extract these 4 elements through natural back-and-forth:
1. SITUATION   — what actually happened (context + facts)
2. OPTIONS     — what choices were available (including ones they didn't see)
3. CHOICE      — what they picked and why
4. RESISTANCE  — why they didn't pick the better option

RULES:
- Ask only ONE follow-up question per turn.
- Don't list questions. Don't number them.
- If the user's message already answers the next question, skip it and move to the one after.
- Once you clearly have all 4 elements, stop asking and return the JSON immediately.
- Do NOT ask for scores — infer them from what the user tells you.
- Do NOT ask the same thing twice in different words.
- Do not complete the extraction if OPTIONS or RESISTANCE are vague or empty. 
- "None" is never an acceptable resistance_reason. Dig deeper.
- If the user seems to have no resistance, ask what they gave up or what they avoided thinking about.

PILLAR DETECTION:
From the incident content, detect which 1-2 ASCEND pillars are most relevant:
- awareness: self-observation, noticing patterns, triggers
- strategy: decisions, planning, priorities
- cognition: thinking quality, focus, mental clarity
- emotional: feelings, reactions, emotional control
- network: relationships, social interactions, communication
- development: skills, learning, habits, growth

SCORING:

clarity_gap — how aware were you of better options:
1 = fully aware, knew exactly what the right option was
2 = knew a better option existed but wasn't sure what it was
3 = had a vague gut feeling something was off but couldn't identify it
4 = didn't think about options at all, just reacted
5 = genuinely had no idea better options existed

resistance_score — knowing vs doing:
1 = knew the right thing and did it immediately
2 = knew the right thing, took it after some delay or hesitation
3 = knew the right thing, did something neutral instead
4 = knew the right thing, consciously chose the worse option
5 = fully knew, felt the guilt, and avoided it anyway

total_score = clarity_gap + resistance_score

total_score meaning:
2-3  = GROWTH STATE — saw clearly, acted on it. Log what made this possible.
4-5  = DEVELOPING — some awareness but something slowed you down. Was it clarity or will?
6    = PATTERN WARNING — blind to options OR know and won't move. Which one?
7    = CONSISTENT AVOIDANCE — you've been here before. Name what's blocking you.
8    = STRUCTURAL PROBLEM — something in your environment or mindset is working against you.
9    = CRISIS POINT — fully aware, fully resistant, repeatedly. This is costing you real things.
10   = FULL BLOCK — complete unawareness + complete avoidance. External help needed.

WHEN YOU HAVE ALL 4 ELEMENTS, respond ONLY with this JSON and nothing else:
{
  "complete": true,
  "situation": "...",
  "options_available": "...",
  "choice_made": "...",
  "resistance_reason": "...",
  "clarity_gap": <1-5>,
  "resistance_score": <1-5>,
  "total_score": <2-10>,
  "score_label": "...",
  "pillars": ["pillar1", "pillar2"]
}
"""

# Renders the conversation page for a given incident ID
# This is the dedicated page user lands on after logging an incident
@app.route('/incident/<int:incident_id>')
def incident_page(incident_id):
    incident = get_incident_by_id(incident_id)
    if not incident:
        return "Incident not found", 404
    return render_template('incident.html', incident=incident)

# Called when user submits a new incident from Quick Log
# Creates the incident in DB, sends first AI question, returns incident_id + first message
@app.route('/start_incident', methods=['POST'])
def start_incident():
    data = request.get_json()
    pillar = data.get('pillar', 'general')
    note = data.get('note', '').strip()

    if not note:
        return jsonify({'error': 'No incident text provided'}), 400

    # Save incomplete incident to DB, get ID
    incident_id = create_incident(pillar, note)

    # Build first AI message — read the incident, ask first follow-up
    messages = [
        {'role': 'system', 'content': SHADOW_SYSTEM_PROMPT},
        {'role': 'user', 'content': f"[PILLAR: {pillar.upper()}]\n{note}"}
    ]

    first_question = call_groq(messages, max_tokens=150)

    # Save this opening exchange to conversation history
    conversation = [
        {'role': 'user', 'content': note},
        {'role': 'assistant', 'content': first_question}
    ]

    # Update incident with initial conversation (still incomplete)
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
        'message': first_question
    })

# Called on every user reply inside the conversation page
# Continues the AI conversation, detects when all 4 elements are extracted
@app.route('/chat_incident', methods=['POST'])
def chat_incident():
    data = request.get_json()
    incident_id = data.get('incident_id')
    user_message = data.get('message', '').strip()

    if not incident_id or not user_message:
        return jsonify({'error': 'Missing incident_id or message'}), 400

    incident = get_incident_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404

    if incident['is_complete']:
        return jsonify({'error': 'This incident is already complete'}), 400

    # Load existing conversation history
    conversation = json.loads(incident['conversation'] or '[]')

    # Append new user message
    conversation.append({'role': 'user', 'content': user_message})

    # Build full message list for Groq: system + full history
    messages = [{'role': 'system', 'content': SHADOW_SYSTEM_PROMPT}]
    # Add pillar context at start of conversation
    messages.append({
        'role': 'user',
        'content': f"[PILLAR: {incident['pillar'].upper()}]\n{incident['situation']}"
    })
    # Add all conversation turns after the first user message
    for turn in conversation[1:]:
        messages.append(turn)

    ai_response = call_groq(messages, max_tokens=300)

    # Check if AI returned the completion JSON
    try:
        # Strip any text around the JSON if present
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            extracted = json.loads(ai_response[json_start:json_end])
            if extracted.get('complete'):
                total_score = extracted.get('total_score', extracted['clarity_gap'] + extracted['resistance_score'])
                score_label = extracted.get('score_label', '')
                pillars = extracted.get('pillars', [incident['pillar']])

                state_code = update_incident(
                    incident_id,
                    extracted['situation'],
                    extracted['options_available'],
                    extracted['choice_made'],
                    extracted['resistance_reason'],
                    extracted['clarity_gap'],
                    extracted['resistance_score'],
                    total_score,
                    score_label,
                    pillars,
                    json.dumps(conversation)
                )
                return jsonify({
                    'complete': True,
                    'state_code': state_code,
                    'summary': {
                        'situation': extracted['situation'],
                        'options': extracted['options_available'],
                        'choice': extracted['choice_made'],
                        'resistance': extracted['resistance_reason'],
                        'clarity_gap': extracted['clarity_gap'],
                        'resistance_score': extracted['resistance_score'],
                        'total_score': total_score,
                        'score_label': score_label,
                        'pillars': pillars,
                    }
                })
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    # Not complete yet — save updated conversation and return next question
    conversation.append({'role': 'assistant', 'content': ai_response})

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
        'message': ai_response
    })

# Smart Check-in V2
# Step 1: returns missing pillars + first question for the first missing one
# Step 2: handles answers, logs incidents, moves to next missing pillar
# Step 3: once all pillars covered, generates day summary
@app.route('/checkin_v2', methods=['POST'])
def checkin_v2():
    data = request.get_json()
    action = data.get('action')

    # action: 'start' — user opens check-in, get missing pillars
    if action == 'start':
        missing = get_missing_pillars_today()
        today_incidents = get_today_incidents()

        if not missing and not today_incidents:
            return jsonify({
                'phase': 'empty_day',
                'message': "You logged nothing today. What actually happened?"
            })

        if missing:
            first_missing = missing[0]
            question = call_groq([
                {'role': 'system', 'content': SHADOW_SYSTEM_PROMPT},
                {'role': 'user', 'content': (
                    f"The user has NOT logged anything for the {first_missing.upper()} pillar today. "
                    f"Ask them one sharp question about why they didn't work on {first_missing} today. "
                    f"Focus on what got in the way — the resistance. Keep it short and direct."
                )}
            ], max_tokens=100)

            return jsonify({
                'phase': 'gap_fill',
                'missing_pillars': missing,
                'current_pillar': first_missing,
                'message': question
            })

        # All pillars covered — go straight to summary
        return _generate_day_summary(today_incidents)

    # action: 'answer' — user responded to a missing pillar question
    # Create an incident from this answer and move to next pillar
    elif action == 'answer':
        pillar = data.get('pillar')
        answer = data.get('answer', '').strip()
        remaining = data.get('remaining_pillars', [])

        incident_id = None
        if answer and pillar:
            incident_id = create_incident(pillar, answer)

        return jsonify({
            'phase': 'redirect',
            'incident_id': incident_id,
            'remaining_pillars': remaining
        })

    return jsonify({'error': 'Invalid action'}), 400


def _generate_day_summary(incidents):
    """Internal helper — generates end-of-day summary from all today's incidents."""
    if not incidents:
        return jsonify({
            'phase': 'summary',
            'message': "Nothing logged today. Tomorrow, log at least one real incident."
        })

    incident_text = ""
    for i in incidents:
        incident_text += f"\n[{i['pillar'].upper()}] {i['situation'] or 'No detail'}"
        incident_text += f"\n  Choice: {i['choice_made'] or '—'}"
        incident_text += f"\n  Resistance: {i['resistance_reason'] or '—'}"
        incident_text += f"\n  State: {i['state_code']} | Clarity Gap: {i['clarity_gap']} | Resistance: {i['resistance_score']}\n"

    summary_prompt = f"""
You are SHADOW — end-of-day debrief for ASCEND user.
Here are today's logged incidents:
{incident_text}

Give a 4-5 line brutally honest summary:
- What pattern is showing up today?
- Which pillar is the biggest problem?
- One specific thing to fix tomorrow.
No motivation. No padding. Be direct.
"""

    summary = call_groq([{'role': 'user', 'content': summary_prompt}], max_tokens=250)

    return jsonify({
        'phase': 'summary',
        'message': summary,
        'incidents': incidents
    })
@app.route('/quick_analyze', methods=['POST'])
def quick_analyze():
    data = request.get_json()
    situation = data.get('situation', '').strip()
    options = data.get('options', '').strip()
    choice = data.get('choice', '').strip()
    resistance = data.get('resistance', '').strip()

    if not situation:
        return jsonify({'error': 'No situation provided'}), 400

    # Ask SHADOW to score and detect pillars
    prompt = f"""
You are SHADOW. A user has logged this incident:

SITUATION: {situation}
OPTIONS AVAILABLE: {options}
CHOICE MADE: {choice}
RESISTANCE/WHY NOT BETTER OPTION: {resistance}

CRITICAL: pillars array MUST contain ONLY values from this exact list: ["awareness", "strategy", "cognition", "emotional", "network", "development"]. No other strings allowed. Pick 1-2 most relevant.
- awareness: self-observation, noticing patterns, emotional triggers, recognizing your own behavior
- strategy: decisions, planning, priorities, choosing what to work on
- cognition: thinking quality, focus, mental clarity, learning
- emotional: feelings, reactions, stress, emotional control
- network: relationships, social interactions, communication
- development: skills, habits, growth, building things
No other values allowed.

Based on this, respond ONLY with this JSON and nothing else:

{{
  "complete": true,
  "situation": "{situation}",
  "options_available": "{options}",
  "choice_made": "{choice}",
  "resistance_reason": "{resistance}",
  "clarity_gap": <1-5>,
  "resistance_score": <1-5>,
  "total_score": <2-10>,
  "score_label": "...",
  "pillars": ["pillar1", "pillar2"]
}}
"""

    response = call_groq([{'role': 'user', 'content': prompt}], max_tokens=300)

    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        extracted = json.loads(response[json_start:json_end])

        total_score = extracted.get('total_score', extracted['clarity_gap'] + extracted['resistance_score'])
        score_label = extracted.get('score_label', '')
        pillars = extracted.get('pillars', ['general'])

        incident_id = create_incident('general', situation)
        state_code = update_incident(
            incident_id, situation, options, choice, resistance,
            extracted['clarity_gap'], extracted['resistance_score'],
            total_score, score_label, pillars, '[]'
        )

        return jsonify({
            'complete': True,
            'state_code': state_code,
            'summary': {
                'situation': situation,
                'options': options,
                'choice': choice,
                'resistance': resistance,
                'clarity_gap': extracted['clarity_gap'],
                'resistance_score': extracted['resistance_score'],
                'total_score': total_score,
                'score_label': score_label,
                'pillars': pillars,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/get_streak')
def get_streak_route():
    return jsonify({'streak': get_streak()})
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
