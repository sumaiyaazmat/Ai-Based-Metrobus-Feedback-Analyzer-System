import re, os
from textblob import TextBlob

# ── Anthropic API Client ───────────────────────────────────────────────
try:
    import anthropic as _anthropic
    ANTHROPIC_AVAILABLE = True
except Exception as _ae:
    ANTHROPIC_AVAILABLE = False
    print(f"[ai_analysis] Anthropic SDK not available: {_ae}")

def _get_client():
    """Create a fresh Anthropic client reading key from env at call time."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return None
    return _anthropic.Anthropic(api_key=key)

# ── ML Model Integration ──────────────────────────────────────────────
try:
    import ml_model as _ml
    _ml.load_models()
    ML_AVAILABLE = True
except Exception as _e:
    ML_AVAILABLE = False
    print(f"[ai_analysis] ML model not available, using rule-based fallback: {_e}")


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHTED KEYWORD DICTIONARIES
# ─────────────────────────────────────────────────────────────────────────────

EMOTION_WEIGHTS = {
    'Angry': {
        'rude': 3, 'rudely': 3, 'disrespectful': 3, 'insulted': 3, 'abuse': 3,
        'abusive': 3, 'arrogant': 3, 'furious': 3, 'outraged': 3, 'outrageous': 3,
        'horrible': 2, 'terrible': 2, 'disgusting': 2, 'shameful': 2, 'unacceptable': 2,
        'worst': 2, 'useless': 2, 'ridiculous': 2, 'incompetent': 2, 'pathetic': 2,
        'overcharged': 2, 'cheated': 2, 'lied': 2, 'refused': 2, 'ignored': 2,
        'very rude': 4, 'extremely rude': 4, 'so rude': 4, 'badly behaved': 3,
        'bad language': 3, 'yelled': 2, 'shouted': 2, 'threatened': 3,
        'dangerous': 2, 'unsafe': 2, 'phone while driving': 4, 'mobile while driving': 4,
        'texting while driving': 4, 'drunk': 4, 'speeding': 2, 'reckless': 3,
        'no help': 2, 'no assistance': 2, 'worst service': 3, 'never again': 3,
        'waste of money': 2, 'lawsuit': 2, 'complaint': 1,
    },
    'Frustrated': {
        'late': 2, 'delay': 2, 'delayed': 2, 'waiting': 2, 'waited': 2,
        'overcrowded': 2, 'crowded': 2, 'full': 1, 'packed': 2, 'standing': 1,
        'no seat': 2, 'no ac': 3, 'ac not working': 3, 'air conditioning': 1,
        'broken': 2, 'dirty': 2, 'filthy': 3, 'smelly': 3, 'smell': 1,
        'missed': 2, 'skipped': 2, 'did not stop': 3, 'drove past': 3,
        'inconvenient': 2, 'problem': 1, 'issue': 1, 'poor': 2,
        'uncomfortable': 2, 'hot inside': 2, 'cold inside': 1, 'noise': 1,
        'slow': 1, 'very slow': 2, 'too slow': 2, 'again late': 3,
        'always late': 3, 'every day late': 4, 'third time': 3, 'second time': 2,
        'very frustrated': 4, 'very annoying': 3, 'really annoying': 3,
        'no announcement': 2, 'no information': 2, 'windows broken': 3,
        'seats broken': 3, 'garbage': 2, 'unhygienic': 3,
    },
    'Happy': {
        'excellent': 3, 'amazing': 3, 'wonderful': 3, 'fantastic': 3, 'superb': 3,
        'outstanding': 3, 'brilliant': 3, 'perfect': 3, 'great': 2, 'love': 2,
        'best': 2, 'impressed': 2, 'delighted': 3, 'pleased': 2, 'happy': 2,
        'thrilled': 3, 'very happy': 4, 'extremely happy': 4, 'so happy': 3,
        'very clean': 3, 'spotless': 3, 'very punctual': 3, 'on time': 2,
        'very helpful': 3, 'very polite': 3, 'courteous': 3, 'cheerful': 2,
        'early': 2, 'arrived early': 3, '5 minutes early': 3, 'smooth ride': 2,
        'comfortable': 2, 'very comfortable': 3, 'well maintained': 3,
        'highly recommend': 3, 'recommend': 2, 'keep it up': 2, 'well done': 2,
        'thank you': 1, 'appreciat': 2,
    },
    'Satisfied': {
        'satisfied': 3, 'good': 2, 'nice': 2, 'decent': 2, 'fine': 1,
        'acceptable': 2, 'adequate': 2, 'reasonable': 2, 'fair': 1,
        'improved': 2, 'better': 2, 'getting better': 3, 'improvement': 2,
        'okay': 1, 'alright': 1, 'not bad': 2, 'mostly good': 2,
        'generally good': 2, 'quite good': 2, 'pretty good': 2,
        'satisfied with': 3, 'happy with': 2, 'pleased with': 2,
        'consistent': 2, 'reliable': 2, 'professional': 2,
    },
    'Neutral': {
        'average': 2, 'normal': 2, 'ordinary': 2, 'standard': 1,
        'nothing special': 2, 'nothing to complain': 2, 'no issues': 2,
        'just okay': 2, 'mediocre': 2, 'so-so': 2, 'moderate': 2,
        'usual': 1, 'regular': 1, 'typical': 1,
    },
}

QUALITY_WEIGHTS = {
    'Bad': {
        'rude': 3, 'disrespectful': 3, 'abusive': 4, 'dangerous': 3,
        'horrible': 3, 'terrible': 3, 'disgusting': 3, 'worst': 3,
        'useless': 3, 'shameful': 3, 'unacceptable': 3, 'outrageous': 3,
        'very late': 2, 'extremely late': 3, 'always late': 4, 'never on time': 4,
        'broke down': 3, 'breakdown': 3, 'broken': 2,
        'dirty': 2, 'filthy': 3, 'smelly': 3, 'very dirty': 3,
        'overcrowded': 2, 'overcharged': 3, 'cheated': 3,
        'phone while driving': 4, 'mobile while driving': 4, 'speeding': 3,
        'no ac': 3, 'ac not working': 3, 'seats broken': 3,
        'skipped stop': 3, 'did not stop': 3, 'missed stop': 3,
        'no help': 2, 'pathetic': 3, 'incompetent': 3,
        'waste of money': 3, 'never again': 3, 'worst service': 4,
    },
    'Excellent': {
        'excellent': 3, 'amazing': 3, 'wonderful': 3, 'fantastic': 3, 'superb': 3,
        'outstanding': 3, 'perfect': 3, 'brilliant': 3, 'best service': 4,
        'very impressed': 3, 'highly impressed': 4, 'spotless': 3,
        'very clean': 3, 'very punctual': 3, 'arrived early': 3,
        'very helpful': 3, 'very polite': 3, 'courteous': 3, 'professional': 2,
        'smooth ride': 2, 'very comfortable': 3, 'well maintained': 3,
        'highly recommend': 4, 'keep it up': 2, 'well done': 2,
        'great service': 3, 'great experience': 3, 'love the service': 4,
    },
    'Average': {
        'average': 2, 'okay': 2, 'acceptable': 2, 'decent': 2, 'fine': 1,
        'not bad': 2, 'reasonable': 2, 'adequate': 2, 'nothing special': 3,
        'could be better': 2, 'room for improvement': 2, 'needs improvement': 2,
        'mostly good': 2, 'generally okay': 2, 'fairly good': 2,
        'satisfied': 1, 'good': 1, 'improved': 1,
    },
}

NEGATIONS = ['not', "n't", 'no', 'never', 'neither', 'nor', 'without', 'hardly']


def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^\w\s']", ' ', text)
    return text


def score_text(text, weight_dict):
    t = preprocess(text)
    words = t.split()
    scores = {cat: 0 for cat in weight_dict}

    for cat, kws in weight_dict.items():
        for phrase, weight in sorted(kws.items(), key=lambda x: -len(x[0].split())):
            phrase_words = phrase.split()
            phrase_len = len(phrase_words)

            if phrase_len == 1:
                for i, w in enumerate(words):
                    if w == phrase:
                        window = words[max(0, i-3):i]
                        if any(neg in window for neg in NEGATIONS):
                            scores[cat] -= weight * 0.5
                        else:
                            scores[cat] += weight
            else:
                for i in range(len(words) - phrase_len + 1):
                    chunk = ' '.join(words[i:i+phrase_len])
                    if chunk == phrase:
                        window = words[max(0, i-3):i]
                        if any(neg in window for neg in NEGATIONS):
                            scores[cat] -= weight * 0.5
                        else:
                            scores[cat] += weight

    return scores


def detect_emotion(text):
    scores = score_text(text, EMOTION_WEIGHTS)
    t_low = text.lower()
    neutral_phrases = ['nothing special', 'just okay', 'so-so', 'no issues',
                       'nothing to complain', 'no complaints', 'mediocre']
    if scores.get('Satisfied', 0) < 3 and any(p in t_low for p in neutral_phrases):
        scores['Neutral'] = scores.get('Neutral', 0) + 3
    best = max(scores, key=scores.get)
    best_score = scores[best]
    if best_score <= 0:
        try:
            pol = TextBlob(text).sentiment.polarity
            if pol > 0.2:   return 'Happy'
            if pol < -0.2:  return 'Angry'
            return 'Neutral'
        except:
            return 'Neutral'
    return best


def detect_quality(text):
    scores = score_text(text, QUALITY_WEIGHTS)
    best = max(scores, key=scores.get)
    best_score = scores[best]
    if best_score <= 0:
        try:
            pol = TextBlob(text).sentiment.polarity
            if pol > 0.3:  return 'Excellent'
            if pol < -0.1: return 'Bad'
            return 'Average'
        except:
            return 'Average'
    return best


def detect_sentiment(text):
    try:
        pol = TextBlob(text).sentiment.polarity
    except:
        pol = 0.0

    t = preprocess(text)
    neg_boosters = ['rude', 'disrespectful', 'dangerous', 'overcharged', 'filthy',
                    'not working', 'overcrowded', 'no ac', 'broken', 'smelly', 'waiting',
                    'terrible', 'horrible', 'worst', 'disgusting', 'unsafe', 'drunk',
                    'threatening', 'abusive', 'cheated', 'broke down', 'useless']
    pos_boosters = ['excellent', 'amazing', 'wonderful', 'fantastic', 'superb',
                    'outstanding', 'perfect', 'brilliant', 'great', 'impressed',
                    'very helpful', 'very polite', 'well done', 'keep it up']
    for word in neg_boosters:
        if word in t:
            pol -= 0.25
    for word in pos_boosters:
        if word in t:
            pol += 0.2

    t_low = text.lower()
    negated_negatives = ['not bad', 'not late', 'not terrible', 'not rude',
                         'not dirty', 'not too bad', 'not horrible']
    if any(p in t_low for p in negated_negatives) and pol > 0.1:
        pol = min(pol, 0.08)
    if pol > 0.1:   return 'Positive'
    if pol < -0.1:  return 'Negative'
    return 'Neutral'


def analyze(text):
    if not text or not text.strip():
        return {'emotion': 'Neutral', 'quality': 'Average', 'sentiment': 'Neutral',
                'summary': 'No feedback text provided.', 'suggestion': 'Please provide detailed feedback.'}

    if ML_AVAILABLE:
        ml_preds  = _ml.ml_predict_with_confidence(text)
        emotion   = ml_preds.get('emotion',   detect_emotion(text))
        sentiment = ml_preds.get('sentiment', detect_sentiment(text))
        quality   = ml_preds.get('quality',   detect_quality(text))
        ml_used   = True
    else:
        emotion   = detect_emotion(text)
        quality   = detect_quality(text)
        sentiment = detect_sentiment(text)
        ml_preds  = {}
        ml_used   = False

    summary_map = {
        ('Angry',  'Bad'):        'This complaint describes a serious service failure requiring urgent attention.',
        ('Angry',  'Average'):    'Passenger experienced frustration with service quality.',
        ('Frustrated', 'Bad'):    'Passenger is frustrated with poor service conditions.',
        ('Frustrated', 'Average'):'Service issues are causing passenger frustration.',
        ('Happy',  'Excellent'):  'Passenger had an excellent experience and is highly satisfied.',
        ('Happy',  'Average'):    'Passenger had a positive experience with some minor concerns.',
        ('Satisfied', 'Excellent'):'Passenger is satisfied and rates the service as excellent.',
        ('Satisfied', 'Average'): 'Passenger is satisfied with the current service level.',
        ('Neutral', 'Average'):   'Passenger had a neutral experience — service met basic expectations.',
    }
    summary = summary_map.get((emotion, quality),
        f'Feedback indicates {emotion.lower()} experience with {quality.lower()} service quality.')

    suggestion_map = {
        'Angry':     'Immediately investigate and address the reported incident. Consider disciplinary action and appropriate follow-up with the passenger.',
        'Frustrated':'Improve service reliability on this route. Add more buses during peak hours and address reported maintenance issues.',
        'Happy':     'Recognize and reward the staff involved. Share best practices with other routes as a benchmark.',
        'Satisfied': 'Maintain current service standards. Gather more detailed feedback to identify further improvement areas.',
        'Neutral':   'Conduct a detailed passenger satisfaction survey to identify specific areas for improvement.',
    }
    suggestion = suggestion_map.get(emotion, 'Review feedback and take appropriate corrective action.')

    return {
        'emotion':              emotion,
        'quality':              quality,
        'sentiment':            sentiment,
        'summary':              summary,
        'suggestion':           suggestion,
        'ml_used':              ml_used,
        'emotion_confidence':   ml_preds.get('emotion_confidence',   'N/A'),
        'sentiment_confidence': ml_preds.get('sentiment_confidence', 'N/A'),
        'quality_confidence':   ml_preds.get('quality_confidence',   'N/A'),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHATBOT — Powered by Anthropic Claude API
# ─────────────────────────────────────────────────────────────────────────────
_CHATBOT_SYSTEM = """You are a professional AI assistant for Metro Bus Pakistan, operated by the Punjab Mass Transit Authority.
Your role is to assist passengers with:
- Submitting complaints and feedback (form on the portal, fields: Name, CNIC, Bus Route, Feedback)
- Bus route information:
  R10: Saddar to Gulberg
  R12: Johar Town to Airport
  R15: DHA to Model Town
  R20: Cantt to Shalimar
  R25: Iqbal Town to Shahdara
- Tracking complaint status (Tracking ID format: MB-XXXX; statuses: Pending, On Hold, Complete)
- Bus schedules: Peak hours (7-9 AM, 5-8 PM) every 10-15 minutes; off-peak every 20-30 minutes; limited after 10 PM
- Staff behavior complaints: include route, bus number, time, and description; action taken within 48 hours
- Vehicle maintenance issues: AC, seats, windows — note bus route and number
- Fare/overcharging complaints: note conductor, route, and time

Rules:
- Be professional, concise, and helpful
- Do NOT use emojis or special symbols
- Keep responses under 5 sentences unless listing steps
- Always direct passengers to use the official feedback form for formal complaints
- Respond in the same language as the user"""

_CHATBOT_FALLBACK_RULES = [
    (r'submit|complain|how.*submit|file.*complaint|register',
     "To submit a complaint:\n1. Fill in your Name and CNIC\n2. Select your bus route\n3. Describe your issue clearly\n4. Click Submit Feedback\n\nYou will receive a Tracking ID instantly."),
    (r'saddar|route.*saddar|saddar.*route',
     "Routes serving Saddar area:\n- R10: Saddar to Gulberg\n- R20: Cantt to Shalimar (via Saddar)\n\nBuses run every 15-20 minutes during peak hours."),
    (r'track|status|check.*complaint|complaint.*status',
     "To track your complaint:\n1. Keep your Tracking ID (e.g. MB-0001)\n2. Contact admin staff to check the dashboard\n3. Status updates: Pending, On Hold, Complete"),
    (r'timing|schedule|when|time.*bus|bus.*time|frequency',
     "Metro Bus Schedule:\n- Peak hours (7-9 AM, 5-8 PM): every 10-15 minutes\n- Off-peak: every 20-30 minutes\n- Night service: limited after 10 PM\n\nTimes vary by route."),
    (r'hello|hi|hey|salam|good morning|good evening',
     "Welcome to the Metro Bus Passenger Portal. I am your AI Assistant. I can help you with complaints, routes, timings, and more. How can I assist you today?"),
    (r'thank|thanks|thank you',
     "You are welcome. If you have any other questions or need to submit a complaint, please use the feedback form or ask me anything."),
    (r'driver|staff|behavior|conduct|rude|disrespect|abusive',
     "Staff behavior complaints are treated as a top priority. Please include in your feedback: route and bus number, time of the incident, and a detailed description. Action will be taken within 48 hours."),
    (r'broken|repair|maintenance|ac|air condition|seat|window',
     "For vehicle maintenance complaints, please note the bus route, bus number, and the specific issue (AC, seat, window, etc.). Our maintenance team will inspect the vehicle after you submit a formal complaint."),
    (r'price|fare|ticket|cost|charge|overcharge',
     "For fare complaints or overcharging, note the conductor details, route, and time, then submit a formal complaint. Overcharging is a serious offense handled directly by management."),
]


def chatbot_reply(message):
    """AI chatbot powered by Anthropic Claude API with rule-based fallback."""
    if ANTHROPIC_AVAILABLE:
        client = _get_client()
        if client:
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=500,
                    system=_CHATBOT_SYSTEM,
                    messages=[{"role": "user", "content": message}]
                )
                return response.content[0].text.strip()
            except Exception as e:
                print(f"[chatbot_reply] Anthropic API error: {e}")

    # Rule-based fallback
    msg = message.lower().strip()
    for pattern, response in _CHATBOT_FALLBACK_RULES:
        if re.search(pattern, msg):
            return response
    return ("I understand your concern. For specific issues, please use the feedback form on the left.\n\n"
            "I can help you with:\n- How to submit a complaint\n- Route information\n"
            "- Complaint tracking\n- Bus timings\n- Driver or staff issues\n\nWhat would you like to know?")


# ─────────────────────────────────────────────────────────────────────────────
# SUGGESTIONS — Powered by Anthropic Claude API
# ─────────────────────────────────────────────────────────────────────────────
def generate_suggestions(records):
    """Generate AI-powered service improvement suggestions using Anthropic Claude API."""
    if not records:
        return ["No feedback data available yet. Submit feedback to generate AI-powered suggestions."]

    total = len(records)
    bad_count     = sum(1 for r in records if r.get('quality') == 'Bad')
    excellent_count = sum(1 for r in records if r.get('quality') == 'Excellent')
    emotion_counts = {}
    route_counts   = {}
    for r in records:
        e = r.get('emotion', 'Neutral')
        emotion_counts[e] = emotion_counts.get(e, 0) + 1
        rt = r.get('route', 'Unknown')
        route_counts[rt] = route_counts.get(rt, 0) + 1

    worst_route = max(route_counts, key=route_counts.get) if route_counts else "Unknown"

    # Try Anthropic API first
    if ANTHROPIC_AVAILABLE:
        client = _get_client()
        if client:
            try:
                summary_prompt = (
                    f"You are an expert transit authority analyst for Metro Bus Pakistan (Punjab Mass Transit Authority).\n"
                    f"Based on the following feedback data, provide exactly 6 specific, actionable improvement recommendations.\n\n"
                    f"FEEDBACK STATISTICS:\n"
                    f"- Total complaints: {total}\n"
                    f"- Bad quality ratings: {bad_count} ({round(bad_count/total*100)}%)\n"
                    f"- Excellent quality ratings: {excellent_count} ({round(excellent_count/total*100)}%)\n"
                    f"- Emotion breakdown: {emotion_counts}\n"
                    f"- Route with most complaints: {worst_route} ({route_counts.get(worst_route, 0)} complaints)\n\n"
                    f"REQUIREMENTS:\n"
                    f"- Provide exactly 6 recommendations, one per line\n"
                    f"- Each recommendation must be specific and actionable (1-2 sentences)\n"
                    f"- Do NOT use emojis, bullet points, or numbering\n"
                    f"- Do NOT add any preamble or conclusion\n"
                    f"- Focus on operations, staff, maintenance, and scheduling\n"
                    f"- Return only the 6 recommendations, each on its own line"
                )
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=600,
                    messages=[{"role": "user", "content": summary_prompt}]
                )
                text = response.content[0].text.strip()
                suggestions = [s.strip() for s in text.split('\n') if s.strip()]
                # Filter out empty lines and return up to 6
                suggestions = [s for s in suggestions if len(s) > 20][:6]
                if suggestions:
                    return suggestions
            except Exception as e:
                print(f"[generate_suggestions] Anthropic API error: {e}")

    # Rule-based fallback
    suggestions = []
    if bad_count > total * 0.5:
        suggestions.append("URGENT: Over 50% of complaints are rated Bad. Conduct an immediate service quality audit across all routes and implement corrective action within 72 hours.")
    elif bad_count > total * 0.3:
        suggestions.append("High Bad complaint rate detected. Schedule a service quality review this week and assign route supervisors to the most affected routes.")

    if emotion_counts.get('Angry', 0) > total * 0.25:
        suggestions.append("High anger level detected in passenger feedback. Implement mandatory customer service and de-escalation training for all bus staff immediately.")
    if emotion_counts.get('Frustrated', 0) > total * 0.25:
        suggestions.append("High frustration rate detected. Focus on improving bus punctuality — deploy GPS-based real-time tracking and adjust scheduling on delayed routes.")

    suggestions.append("Implement weekly deep-cleaning inspections for all buses, with documented hygiene reports submitted to the central authority.")
    suggestions.append("Increase bus frequency during peak hours (7-9 AM and 5-8 PM) to reduce overcrowding and improve passenger comfort.")
    suggestions.append("Introduce a passenger awareness campaign on how to submit complaints, available at each bus stop and inside buses.")
    suggestions.append("Conduct monthly anonymous passenger satisfaction surveys to track service improvement trends and identify recurring issues.")

    return suggestions[:6]
