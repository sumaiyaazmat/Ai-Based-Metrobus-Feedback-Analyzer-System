import os
import pandas as pd
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
FEEDBACK_FILE  = os.path.join(DATA_DIR, 'feedback.csv')
NOTES_FILE     = os.path.join(DATA_DIR, 'notes.csv')
COLUMNS = ['id','name','cnic','route','feedback','emotion','sentiment','quality','status','date']

SAMPLES = [
    ['MB-0001','Ahmad Raza','35202-1234567-1','R10','Bus was extremely late and driver was very rude to passengers.','Angry','Negative','Bad','Pending','2025-01-10'],
    ['MB-0002','Sara Iqbal','35202-7654321-2','R12','Great service today! Bus was clean and arrived right on time.','Happy','Positive','Excellent','Complete','2025-01-11'],
    ['MB-0003','Usman Ali','35202-1111111-3','R15','Bus was overcrowded and AC was not working. Very uncomfortable.','Frustrated','Negative','Bad','Pending','2025-01-12'],
    ['MB-0004','Fatima Khan','35202-2222222-4','R10','Service is average, nothing special but acceptable overall.','Neutral','Neutral','Average','On Hold','2025-01-13'],
    ['MB-0005','Bilal Hussain','35202-3333333-5','R20','Amazing experience! Staff was helpful and bus was very comfortable.','Happy','Positive','Excellent','Complete','2025-01-14'],
    ['MB-0006','Zara Sheikh','35202-4444444-6','R25','Driver missed my stop and was not cooperative at all.','Angry','Negative','Bad','Pending','2025-01-15'],
    ['MB-0007','Hassan Malik','35202-5555555-7','R12','Bus timings have improved. Satisfied with the recent changes.','Satisfied','Positive','Average','Complete','2025-01-16'],
]

def init_csv():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(COLUMNS)
            csv.writer(f).writerows(SAMPLES)
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['complaint_id','note','admin','timestamp'])

def get_all():
    try:
        df = pd.read_csv(FEEDBACK_FILE, dtype=str)
        return df.fillna('').to_dict('records')
    except Exception as e:
        print('get_all error:', e); return []

def get_by_id(complaint_id):
    try:
        df = pd.read_csv(FEEDBACK_FILE, dtype=str)
        row = df[df['id'] == complaint_id]
        if row.empty: return None
        return row.fillna('').to_dict('records')[0]
    except Exception as e:
        print('get_by_id error:', e); return None

def save_feedback(data):
    try:
        df = pd.read_csv(FEEDBACK_FILE, dtype=str)
        new_id = 'MB-' + str(len(df)+1).zfill(4)
        row = {'id': new_id, 'name': str(data.get('name','')),
               'cnic': str(data.get('cnic','')), 'route': str(data.get('route','')),
               'feedback': str(data.get('feedback','')), 'emotion': str(data.get('emotion','Neutral')),
               'sentiment': str(data.get('sentiment','Neutral')), 'quality': str(data.get('quality','Average')),
               'status': 'Pending', 'date': datetime.now().strftime('%Y-%m-%d')}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(FEEDBACK_FILE, index=False, encoding='utf-8')
        return new_id
    except Exception as e:
        print('save_feedback error:', e); return 'MB-ERR'

def update_status(complaint_id, new_status):
    try:
        df = pd.read_csv(FEEDBACK_FILE, dtype=str)
        df.loc[df['id'] == complaint_id, 'status'] = new_status
        df.to_csv(FEEDBACK_FILE, index=False, encoding='utf-8')
        return True
    except Exception as e:
        print('update_status error:', e); return False

def save_note(complaint_id, note, admin='Admin'):
    try:
        with open(NOTES_FILE, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([complaint_id, note, admin,
                                    datetime.now().strftime('%Y-%m-%d %H:%M')])
        return True
    except Exception as e:
        print('save_note error:', e); return False

def get_notes(complaint_id):
    try:
        df = pd.read_csv(NOTES_FILE, dtype=str)
        rows = df[df['complaint_id'] == complaint_id].fillna('').to_dict('records')
        return rows
    except:
        return []

def get_stats():
    records = get_all()
    total   = len(records)
    pending = sum(1 for r in records if r.get('status') == 'Pending')
    complete= sum(1 for r in records if r.get('status') == 'Complete')
    on_hold = sum(1 for r in records if r.get('status') == 'On Hold')
    emotions, qualities, routes = {}, {}, {}
    for r in records:
        e = r.get('emotion','Neutral');  emotions[e]  = emotions.get(e,0)+1
        q = r.get('quality','Average');  qualities[q] = qualities.get(q,0)+1
        rt= r.get('route','Unknown');    routes[rt]   = routes.get(rt,0)+1
    return {'total':total,'pending':pending,'complete':complete,
            'on_hold':on_hold,'emotions':emotions,'qualities':qualities,'routes':routes}

def get_route_scores():
    records = get_all()
    route_data = {}
    for r in records:
        rt = r.get('route','Unknown')
        if rt not in route_data:
            route_data[rt] = {'total':0,'excellent':0,'average':0,'bad':0,'positive':0,'negative':0}
        route_data[rt]['total'] += 1
        q = r.get('quality','Average')
        if q == 'Excellent': route_data[rt]['excellent'] += 1
        elif q == 'Bad':     route_data[rt]['bad'] += 1
        else:                route_data[rt]['average'] += 1
        s = r.get('sentiment','Neutral')
        if s == 'Positive':  route_data[rt]['positive'] += 1
        elif s == 'Negative':route_data[rt]['negative'] += 1

    scores = []
    for rt, d in route_data.items():
        if d['total'] == 0: continue
        # Score formula: excellent=10pts, average=5pts, bad=0pts, weighted
        raw = (d['excellent']*10 + d['average']*5 + d['bad']*0) / d['total']
        # Sentiment bonus/penalty
        sent_ratio = (d['positive'] - d['negative']) / d['total']
        score = round(min(10, max(1, raw + sent_ratio)), 1)
        if score >= 7:   health = 'green'
        elif score >= 4: health = 'yellow'
        else:            health = 'red'
        scores.append({'route': rt, 'score': score, 'health': health,
                       'total': d['total'], 'excellent': d['excellent'],
                       'average': d['average'], 'bad': d['bad']})
    scores.sort(key=lambda x: x['score'], reverse=True)
    return scores

def merge_csv(filepath):
    try:
        uploaded = pd.read_csv(filepath, dtype=str)
        uploaded.columns = [c.lower().strip() for c in uploaded.columns]
        existing = pd.read_csv(FEEDBACK_FILE, dtype=str)
        count = 0
        for _, row in uploaded.iterrows():
            text = str(row.get('feedback', row.get('description','')))
            if text and text.lower() != 'nan':
                new_id = 'MB-' + str(len(existing)+count+1).zfill(4)
                new_row = {'id':new_id,'name':row.get('name','Unknown'),
                           'cnic':row.get('cnic','-'),'route':row.get('route','Unknown'),
                           'feedback':text,'emotion':row.get('emotion','Neutral'),
                           'sentiment':row.get('sentiment','Neutral'),'quality':row.get('quality','Average'),
                           'status':row.get('status','Pending'),
                           'date':row.get('date',datetime.now().strftime('%Y-%m-%d'))}
                existing = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
                count += 1
        existing.to_csv(FEEDBACK_FILE, index=False, encoding='utf-8')
        return count
    except Exception as e:
        print('merge_csv error:', e); return 0
