import requests
import time

BASE = 'http://localhost:8000'

def run():
    print('Health:', requests.get(f'{BASE}/health').json())
    f = requests.post(f'{BASE}/forecast', json={'hours': 12}).json()
    print('Forecast sample:', list(f['forecast'].items())[:3])
    a = requests.get(f'{BASE}/anomalies').json()
    print('Anomalies:', a.get('count'))
    r = requests.post(f'{BASE}/recommend', json={'forecast': f['forecast'], 'anomalies': a}).json()
    print('Recommendations:', r.get('actions'))
    brief_obj = r.get('brief')
    if isinstance(brief_obj, dict):
        brief_text = brief_obj.get('brief') or str(brief_obj)
    else:
        brief_text = str(brief_obj)
    print('Brief (truncated):\n', brief_text[:800])

if __name__ == '__main__':
    run()
