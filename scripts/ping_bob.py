import os
import sys
import json
import requests

url = os.environ.get('BOB_API_URL')
key = os.environ.get('BOB_API_KEY')
if not url or not key:
    print('Set BOB_API_URL and BOB_API_KEY in env')
    sys.exit(1)

headers_list = [
    {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    {'x-api-key': key, 'Content-Type': 'application/json'},
    {'Authorization': f'ApiKey {key}', 'Content-Type': 'application/json'}
]

payload = { 'input': { 'text': 'Hello' }, 'instruction': 'Return a short acknowledgement.' }

for h in headers_list:
    try:
        print('Trying headers:', list(h.keys()))
        r = requests.post(url, headers=h, data=json.dumps(payload), timeout=10)
        print('Status:', r.status_code)
        txt = r.text
        print('Body (truncated 800 chars):', txt[:800])
    except Exception as e:
        print('Error:', e)
