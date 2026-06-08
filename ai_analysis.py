import re
from textblob import TextBlob

# ── ML Model Integration ──────────────────────────────────────────────
# Import the real machine learning model trained on the labeled CSV data.
try:
    import ml_model as _ml
    _ml.load_models()
    ML_AVAILABLE = True
except Exception as _e:
    ML_AVAILABLE = False
    print(f"[ai_analysis] ML model not available, using rule-based fallback: {_e}")


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHTED KEYWORD DICTIONARIES
# Each word has a weight (higher = stronger signal)
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

# ─────────────────────────────────────────────────────────────────────────────
# NEGATION HANDLING
# ─────────────────────────────────────────────────────────────────────────────
NEGATIONS = ['not', "n't", 'no', 'never', 'neither', 'nor', 'without', 'hardly']


def preprocess(text):
    """Lowercase, remove punctuation except apostrophes."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", ' ', text)
    return text


def score_text(text, weight_dict):
    """
    Score text against a weights dictionary.
    Handles multi-word phrases and basic negation.
    Returns dict of {category: score}.
    """
    t = preprocess(text)
    words = t.split()
    scores = {cat: 0 for cat in weight_dict}

    for cat, kws in weight_dict.items():
        # Sort by length desc so multi-word phrases matched first
        for phrase, weight in sorted(kws.items(), key=lambda x: -len(x[0].split())):
            phrase_words = phrase.split()
            phrase_len = len(phrase_words)

            if phrase_len == 1:
                for i, w in enumerate(words):
                    if w == phrase:
                        # Check for negation in 3 words before
                        window = words[max(0, i-3):i]
                        if any(neg in window for neg in NEGATIONS):
                            # Negation — subtract half weight from opposite
                            scores[cat] -= weight * 0.5
                        else:
                            scores[cat] += weight
            else:
                # Multi-word phrase
                for i in range(len(words) - phrase_len + 1):
                    chunk = ' '.join(words[i:i+phrase_len])
                    if chunk == phrase:
                        # Check negation
                        window = words[max(0, i-3):i]
                        if any(neg in window for neg in NEGATIONS):
                            scores[cat] -= weight * 0.5
                        else:
                            scores[cat] += weight

    return scores


def detect_emotion(text):
    scores = score_text(text, EMOTION_WEIGHTS)
    # Prefer Neutral over Satisfied when Satisfied score is weak
    # and neutral indicators like 'nothing special', 'okay' are present
    t_low = text.lower()
    neutral_phrases = ['nothing special', 'just okay', 'so-so', 'no issues',
                       'nothing to complain', 'no complaints', 'mediocre']
    if scores.get('Satisfied',0) < 3 and any(p in t_low for p in neutral_phrases):
        scores['Neutral'] = scores.get('Neutral', 0) + 3
    best = max(scores, key=scores.get)
    best_score = scores[best]
    # If no signal at all, fall back to TextBlob polarity
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
    """TextBlob + keyword boosting for better accuracy."""
    try:
        pol = TextBlob(text).sentiment.polarity
    except:
        pol = 0.0

    t = preprocess(text)
    # Boost negative
    neg_boosters = ['rude', 'disrespectful', 'dangerous', 'overcharged', 'filthy',
                    'not working', 'overcrowded', 'no ac', 'broken', 'smelly', 'waiting',
                    'terrible', 'horrible', 'worst', 'disgusting', 'unsafe', 'drunk',
                    'threatening', 'abusive', 'cheated', 'broke down', 'useless']
    # Boost positive
    pos_boosters = ['excellent', 'amazing', 'wonderful', 'fantastic', 'superb',
                    'outstanding', 'perfect', 'brilliant', 'great', 'impressed',
                    'very helpful', 'very polite', 'well done', 'keep it up']
    for word in neg_boosters:
        if word in t:
            pol -= 0.25
    for word in pos_boosters:
        if word in t:
            pol += 0.2

    # Clamp: negated negative phrases should not produce strongly Positive
    t_low = text.lower()
    negated_negatives = ['not bad', 'not late', 'not terrible', 'not rude',
                         'not dirty', 'not too bad', 'not horrible']
    if any(p in t_low for p in negated_negatives) and pol > 0.1:
        pol = min(pol, 0.08)  # cap at Neutral
    if pol > 0.1:   return 'Positive'
    if pol < -0.1:  return 'Negative'
    return 'Neutral'


def analyze(text):
    if not text or not text.strip():
        return {'emotion': 'Neutral', 'quality': 'Average', 'sentiment': 'Neutral',
                'summary': 'No feedback text provided.', 'suggestion': 'Please provide detailed feedback.'}

    # ── Use Real ML Model (trained on labeled CSV data) ──────────────
    # The ML model has learned patterns from 100 real feedback examples.
    # It converts text into word scores (TF-IDF) and then predicts labels.
    # If ML is unavailable for any reason, we fall back to the keyword rules.
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

    # Summary
    summary_map = {
        ('Angry',  'Bad'):       'This complaint describes a serious service failure requiring urgent attention.',
        ('Angry',  'Average'):   'Passenger experienced frustration with service quality.',
        ('Frustrated', 'Bad'):   'Passenger is frustrated with poor service conditions.',
        ('Frustrated', 'Average'):'Service issues are causing passenger frustration.',
        ('Happy',  'Excellent'): 'Passenger had an excellent experience and is highly satisfied.',
        ('Happy',  'Average'):   'Passenger had a positive experience with some minor expectations.',
        ('Satisfied', 'Excellent'):'Passenger is satisfied and rates the service as excellent.',
        ('Satisfied', 'Average'): 'Passenger is satisfied with the current service level.',
        ('Neutral', 'Average'):   'Passenger had a neutral experience — service met basic expectations.',
    }
    summary = summary_map.get((emotion, quality),
        f'Feedback indicates {emotion.lower()} experience with {quality.lower()} service quality.')

    # Suggestion
    suggestion_map = {
        'Angry':     'Immediately investigate and address the reported incident. Consider disciplinary action and passenger compensation.',
        'Frustrated':'Improve service reliability on this route. Add more buses during peak hours and fix reported maintenance issues.',
        'Happy':     'Recognize and reward the staff involved. Share best practices with other routes.',
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
# CHATBOT
# ─────────────────────────────────────────────────────────────────────────────
CHATBOT_RULES = [
    (r'submit|complain|how.*submit|file.*complaint|register',
     "To submit a complaint:\n1. Fill in your name and CNIC\n2. Select your bus route\n3. Describe your issue clearly\n4. Click Submit Feedback\n\nYou will receive a Tracking ID instantly! "),
    (r'saddar|route.*saddar|saddar.*route|which route.*saddar',
     "Routes serving Saddar area:\n• R10 — Saddar ↔ Gulberg\n• R20 — Cantt ↔ Shalimar (via Saddar)\n\nBuses run every 15–20 minutes during peak hours. "),
    (r'track|status|check.*complaint|complaint.*status|find.*complaint',
     "To track your complaint:\n1. Keep your Tracking ID (e.g. MB-0001)\n2. Ask admin staff to check the dashboard\n3. Status: Pending → On Hold → Complete\n\nKeep your Tracking ID safe! "),
    (r'info|require|what.*need|information|which fields|what fields',
     "Required information:\n• Full Name\n• CNIC number (e.g. 35202-1234567-1)\n• Bus Route Number\n• Detailed feedback description\n\nAll fields are required. "),
    (r'timing|schedule|when|time.*bus|bus.*time|frequency',
     "Metro Bus Schedule:\n• Peak hours (7–9 AM, 5–8 PM): every 10–15 minutes\n• Off-peak: every 20–30 minutes\n• Night service: limited after 10 PM\n\nTimes vary by route. "),
    (r'clean|dirty|hygiene|sanitation|smell|filthy',
     "Cleanliness complaints are handled seriously!\nPlease submit a formal complaint with:\n• Route number and bus number\n• Date and time of travel\n• Description of the issue\n\nOur hygiene team will be notified. "),
    (r'driver|staff|behavior|conduct|rude|disrespect|abusive',
     "Staff behavior complaints are our top priority.\nPlease include in your feedback:\n• Route and bus number (if visible)\n• Time of the incident\n• Detailed description of behavior\n\nAction will be taken within 48 hours. "),
    (r'broken|repair|maintenance|ac|air condition|seat|window',
     "Vehicle maintenance complaints are important!\nPlease note:\n• Bus route and number\n• Specific issue (AC, seat, window, etc.)\n• Your travel time\n\nOur maintenance team will inspect the bus. "),
    (r'hello|hi|hey|salam|assalam|good morning|good evening|howdy',
     "Hello!  Welcome to Metro Bus AI Assistant!\nI can help you with:\n• Submitting complaints\n• Route information\n• Tracking complaint status\n• Bus timings and schedules\n\nHow can I assist you today?"),
    (r'thank|thanks|thank you|shukriya',
     "You are welcome! \nIf you have any other questions or need to submit a complaint, I am always here to help.\n\nHave a safe journey! "),
    (r'report|authority|government|official',
     "Official reports are generated automatically by our system and sent to the Punjab Transport Authority.\n\nEach complaint is tracked and included in monthly reports. All serious complaints are escalated immediately. "),
    (r'price|fare|ticket|cost|charge|money',
     "For fare complaints or overcharging:\n• Note the conductor's description\n• Note the route and time\n• Submit a formal complaint\n\nOvercharging is a serious offense handled by management. "),
]


def chatbot_reply(message):
    msg = message.lower().strip()
    for pattern, response in CHATBOT_RULES:
        if re.search(pattern, msg):
            return response
    return ("I understand your concern! For specific issues, please use the feedback form on the left.\n\n"
            "I can help you with:\n• How to submit a complaint\n• Route information\n"
            "• Complaint tracking\n• Bus timings\n• Driver/staff issues\n\nWhat would you like to know? ")


# ─────────────────────────────────────────────────────────────────────────────
# SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────
def generate_suggestions(records):
    if not records:
        return ["Submit more feedback to generate AI suggestions."]

    total = len(records)
    bad_count  = sum(1 for r in records if r.get('quality') == 'Bad')
    emotion_counts = {}
    for r in records:
        e = r.get('emotion', 'Neutral')
        emotion_counts[e] = emotion_counts.get(e, 0) + 1

    suggestions = []

    if bad_count > total * 0.5:
        suggestions.append(" URGENT: Over 50% of complaints rated Bad — conduct immediate service audit across all routes.")
    elif bad_count > total * 0.3:
        suggestions.append("️ High Bad complaint rate — schedule service quality review within this week.")

    if emotion_counts.get('Angry', 0) > total * 0.25:
        suggestions.append(" High anger level detected — implement mandatory staff behavior and customer service training program.")
    if emotion_counts.get('Frustrated', 0) > total * 0.25:
        suggestions.append(" High frustration rate — improve bus punctuality and add GPS-based real-time tracking for passengers.")

    suggestions.append(" Schedule weekly deep-cleaning inspections for all buses on all routes.")
    suggestions.append(" Increase bus frequency during peak hours (7–9 AM and 5–8 PM) to reduce overcrowding.")
    suggestions.append(" Introduce a mobile app for real-time bus tracking and digital complaint submission.")
    suggestions.append(" Conduct monthly passenger satisfaction surveys to track service improvement trends.")

    return suggestions[:6]
