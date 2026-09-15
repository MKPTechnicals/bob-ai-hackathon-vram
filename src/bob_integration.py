import os
import requests
import json

BOB_API_URL = os.environ.get('BOB_API_URL', '')  # set in environment for real integration
BOB_API_KEY = os.environ.get('BOB_API_KEY', '')


def _compose_brief_text(forecast: dict, anomalies: dict, actions: dict):
    peak = max(map(float, forecast.values())) if forecast else None
    summary = {
        'peak_estimate': peak,
        'forecast_horizon': len(forecast) if forecast else 0,
        'anomalies': anomalies.get('count', 0) if anomalies else 0,
        'recommended_actions': actions.get('actions', actions) if isinstance(actions, dict) else actions
    }

    brief_text = (
        f"Operator Optimisation Brief:\nPeak estimate: {summary['peak_estimate']}\n"
        f"Forecast horizon: {summary['forecast_horizon']} hours\nAnomalies detected: {summary['anomalies']}\n"
        f"Recommendations:\n"
    )
    for a in summary['recommended_actions']:
        brief_text += f" - {a.get('type')}: {a.get('description')}\n"
    return brief_text


def call_bob_for_brief(forecast: dict, anomalies: dict, actions: dict, timeout: int = 10):
    """Send structured request to Bob AI API to generate an operator brief and explanations.

    Returns a dict with either {'brief': text} or an error dict.
    """
    brief_text = _compose_brief_text(forecast, anomalies, actions)
    if not (BOB_API_URL and BOB_API_KEY):
        return {'brief': brief_text}

    payload = {
        'input': {
            'forecast': forecast,
            'anomalies': anomalies,
            'actions': actions
        },
        'instruction': 'Generate an operator optimisation brief, include root-cause explanations for anomalies, concise curtailment minimisation plan, and actionable steps.'
    }
    headers = {'Authorization': f'Bearer {BOB_API_KEY}', 'Content-Type': 'application/json'}
    try:
        resp = requests.post(BOB_API_URL, headers=headers, data=json.dumps(payload), timeout=timeout)
        if resp.status_code == 200:
            # Attempt to decode expected fields
            try:
                j = resp.json()
                # common shapes: { 'result': 'text' } or { 'brief': 'text' }
                if isinstance(j, dict):
                    if 'brief' in j:
                        return {'brief': j['brief']}
                    if 'result' in j:
                        return {'brief': j['result']}
                    # fallback: return full json under 'brief'
                    return {'brief': json.dumps(j)}
            except Exception:
                return {'brief': resp.text}

        # If server returned non-200, attempt candidate endpoints
        attempts = []
        candidate_paths = [
            '/v1/generate', '/v1/completions', '/v1/completions?model=bob', '/v1/predict',
            '/assistant/api/v1', '/v1/assistant/generate', '/v1/engines/bob/completions',
            '/api/generate', '/v1/ai/generate', '/v1/requests', '/v1/completions', '/v1/answer'
        ]
        for p in candidate_paths:
            url = BOB_API_URL.rstrip('/') + p
            try:
                r2 = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
                attempts.append({'url': url, 'status_code': r2.status_code, 'text': r2.text[:400]})
                if r2.status_code == 200:
                    try:
                        j = r2.json()
                        if isinstance(j, dict):
                            if 'brief' in j:
                                return {'brief': j['brief']}
                            if 'result' in j:
                                return {'brief': j['result']}
                            return {'brief': json.dumps(j)}
                    except Exception:
                        return {'brief': r2.text}
                else:
                    continue
            except Exception as e:
                attempts.append({'url': url, 'error': str(e)})
                continue

        # If we got 401 errors, try alternative header formats (x-api-key, ApiKey)
        if any(a.get('status_code') == 401 for a in attempts):
            alt_headers_list = [
                {'x-api-key': BOB_API_KEY, 'Content-Type': 'application/json'},
                {'Authorization': f'ApiKey {BOB_API_KEY}', 'Content-Type': 'application/json'},
            ]
            for alt_headers in alt_headers_list:
                for p in candidate_paths:
                    url = BOB_API_URL.rstrip('/') + p
                    try:
                        r3 = requests.post(url, headers=alt_headers, data=json.dumps(payload), timeout=timeout)
                        attempts.append({'url': url, 'status_code': r3.status_code, 'text': r3.text[:400], 'headers_used': list(alt_headers.keys())})
                        if r3.status_code == 200:
                            try:
                                j = r3.json()
                                if isinstance(j, dict):
                                    if 'brief' in j:
                                        return {'brief': j['brief']}
                                    if 'result' in j:
                                        return {'brief': j['result']}
                                    return {'brief': json.dumps(j)}
                            except Exception:
                                return {'brief': r3.text}
                    except Exception as e:
                        attempts.append({'url': url, 'error': str(e), 'headers_used': list(alt_headers.keys())})
                        continue

        # if we get here, none of the candidate endpoints succeeded
        return {'error': 'bob_api_failed', 'status_code': resp.status_code, 'text': resp.text, 'brief': brief_text, 'attempts': attempts}

    except Exception as e:
        return {'error': 'exception', 'message': str(e), 'brief': brief_text}


def generate_operator_brief(forecast: dict, anomalies: dict, actions: dict, use_bob: bool = False):
    if use_bob:
        return call_bob_for_brief(forecast, anomalies, actions)
    return {'brief': _compose_brief_text(forecast, anomalies, actions)}
