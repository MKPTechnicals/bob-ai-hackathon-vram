def recommend_actions(forecast: dict, anomalies: dict):
    # Simple heuristics for demo purposes
    # forecast: dict of hour->predicted_load
    values = list(map(float, forecast.values())) if isinstance(forecast, dict) else []
    actions = []
    if not values:
        return {'actions': actions}

    peak = max(values)
    avg = sum(values)/len(values)
    peak_hour = max(forecast, key=lambda k: float(forecast[k]))

    # If peak significantly above avg, recommend load-shedding alternatives
    if peak > avg * 1.15:
        actions.append({'type': 'demand_response', 'hour': peak_hour, 'description': 'Activate demand response for flexible loads'})
        actions.append({'type': 'battery_dispatch', 'hour': peak_hour, 'description': 'Dispatch battery to shave peak (supply ~10% peak)'} )
        actions.append({'type': 'curtailment_minimisation', 'hour': peak_hour, 'description': 'Prioritise local battery + demand response before curtailment'})
    else:
        actions.append({'type': 'monitor', 'description': 'No aggressive actions required; continue monitoring'})

    # If anomalies present, add investigation action
    if anomalies and anomalies.get('count',0) > 0:
        actions.append({'type': 'investigate_assets', 'count': anomalies.get('count'), 'description': 'Inspect underperforming renewable assets and telemetry'})

    return {'actions': actions}
