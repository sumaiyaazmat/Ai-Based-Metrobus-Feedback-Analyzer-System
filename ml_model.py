

import os
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_FILE  = os.path.join(BASE_DIR, 'data', 'training_dataset_65k.csv')
MODEL_DIR  = os.path.join(BASE_DIR, 'data', 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# One model file per prediction target
MODEL_FILES = {
    'sentiment': os.path.join(MODEL_DIR, 'sentiment_model.pkl'),
    'emotion':   os.path.join(MODEL_DIR, 'emotion_model.pkl'),
    'quality':   os.path.join(MODEL_DIR, 'quality_model.pkl'),
}


_models = {}  



def train_all_models(verbose=True):
  
    # --- Load the labeled dataset ---
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Dataset not found at: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE, dtype=str)
    df = df.dropna(subset=['feedback'])          
    df = df[df['feedback'].str.strip() != '']   

    X = df['feedback'].astype(str)               
    accuracy_scores = {}

    targets = {
        'sentiment': df['sentiment'],   
        'emotion':   df['emotion'],     
        'quality':   df['quality'],    
    }

    for target_name, y in targets.items():


        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.20,     # 20 examples for testing
            random_state=42,    # fixed seed = reproducible results
            stratify=y          # keep class ratios balanced
        )

 
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),   
            max_features=500,     
            strip_accents='unicode',
            lowercase=True,
        )
        X_train_vec = vectorizer.fit_transform(X_train)  
        X_test_vec  = vectorizer.transform(X_test)        


        classifier = LogisticRegression(
            max_iter=1000,
            random_state=42,
            solver='lbfgs',
        )
        classifier.fit(X_train_vec, y_train)

      
        predictions = classifier.predict(X_test_vec)
        acc = accuracy_score(y_test, predictions)
        accuracy_scores[target_name] = round(acc * 100, 1)

        if verbose:
            print(f"\n{'='*50}")
            print(f"  {target_name.upper()} MODEL")
            print(f"{'='*50}")
            print(f"  Training examples : {len(X_train)}")
            print(f"  Testing  examples : {len(X_test)}")
            print(f"  Accuracy          : {acc:.1%}")
            print(f"\n  Detailed Report:")
            print(classification_report(y_test, predictions, zero_division=0))

    
        with open(MODEL_FILES[target_name], 'wb') as f:
            pickle.dump((vectorizer, classifier), f)

        # Also keep in memory
        _models[target_name] = (vectorizer, classifier)

    if verbose:
        print("\n  All 3 models trained and saved successfully!")
        print(f"    Sentiment accuracy : {accuracy_scores['sentiment']}%")
        print(f"    Emotion   accuracy : {accuracy_scores['emotion']}%")
        print(f"    Quality   accuracy : {accuracy_scores['quality']}%")

    return accuracy_scores




def load_models():

    global _models

    # Check if any model file is missing
    all_exist = all(os.path.exists(p) for p in MODEL_FILES.values())

    if not all_exist:
        print("ML models not found. Training now from dataset...")
        train_all_models(verbose=False)
        return

    for target_name, filepath in MODEL_FILES.items():
        with open(filepath, 'rb') as f:
            _models[target_name] = pickle.load(f)

    print(" ML models loaded from disk successfully.")




def ml_predict(text: str) -> dict:
    """
    Given a feedback text, return ML predictions for all three targets.

    Returns a dict like:
        { 'sentiment': 'Negative', 'emotion': 'Angry', 'quality': 'Bad' }
    """
    if not _models:
        load_models()

    if not text or not text.strip():
        return {'sentiment': 'Neutral', 'emotion': 'Neutral', 'quality': 'Average'}

    results = {}
    for target_name, (vectorizer, classifier) in _models.items():
        vec = vectorizer.transform([text])
        results[target_name] = classifier.predict(vec)[0]

    return results


def ml_predict_with_confidence(text: str) -> dict:
    """
    Same as ml_predict but also returns confidence % for each label.
    Example:
        {
          'sentiment': 'Negative',  'sentiment_confidence': '92%',
          'emotion':   'Angry',     'emotion_confidence':   '78%',
          'quality':   'Bad',       'quality_confidence':   '85%',
        }
    """
    if not _models:
        load_models()

    if not text or not text.strip():
        return {
            'sentiment': 'Neutral', 'sentiment_confidence': '0%',
            'emotion':   'Neutral', 'emotion_confidence':   '0%',
            'quality':   'Average', 'quality_confidence':   '0%',
        }

    results = {}
    for target_name, (vectorizer, classifier) in _models.items():
        vec   = vectorizer.transform([text])
        label = classifier.predict(vec)[0]
        proba = classifier.predict_proba(vec)[0]
        conf  = max(proba)
        results[target_name]                        = label
        results[f'{target_name}_confidence']        = f'{conf:.0%}'

    return results


def get_model_accuracy() -> dict:
  
    try:
        df = pd.read_csv(DATA_FILE, dtype=str).dropna(subset=['feedback'])
        df = df[df['feedback'].str.strip() != '']
        X  = df['feedback'].astype(str)

        scores = {}
        target_cols = {
            'sentiment': df['sentiment'],
            'emotion':   df['emotion'],
            'quality':   df['quality'],
        }

        if not _models:
            load_models()

        for target_name, y in target_cols.items():
            _, X_test, _, y_test = train_test_split(
                X, y, test_size=0.20, random_state=42, stratify=y
            )
            vec, clf = _models[target_name]
            preds    = clf.predict(vec.transform(X_test))
            acc      = accuracy_score(y_test, preds)
            scores[target_name] = f'{acc:.1%}'

        return scores

    except Exception as e:
        return {'error': str(e)}




if __name__ == '__main__':
    print("\n  Metro Bus Feedback Analyzer — ML Model Training")
    print("=" * 52)
    scores = train_all_models(verbose=True)
    print("\n  Final Accuracy Summary:")
    for name, acc in scores.items():
        bar = '█' * int(acc / 5) + '░' * (20 - int(acc / 5))
        print(f"    {name:<12} [{bar}]  {acc}%")
