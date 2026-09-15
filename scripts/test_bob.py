import os
import sys
import json
# ensure repository root on path so `src` imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.data import generate_synthetic_data
from src.model import ForecastModel, AnomalyDetector
from src.optimizer import recommend_actions
from src.bob_integration import call_bob_for_brief


def build_demo_payload():
    df = generate_synthetic_data(days=2)
    fm = ForecastModel()
    fm.train(df)
    preds = fm.predict_hours(12)
    ad = AnomalyDetector()
    ad.train(df)
    an = ad.detect_recent(df)
    actions = recommend_actions(preds, an)
    return preds, an, actions


def main():
    print('BOB_API_URL=', os.environ.get('BOB_API_URL'))
    print('BOB_API_KEY=', '***' + os.environ.get('BOB_API_KEY','')[-6:])
    preds, an, actions = build_demo_payload()
    print('Calling Bob API...')
    resp = call_bob_for_brief(preds, an, actions)
    print('Response:')
    print(json.dumps(resp, indent=2))


if __name__ == '__main__':
    main()
