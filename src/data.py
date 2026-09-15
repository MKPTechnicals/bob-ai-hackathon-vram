import pandas as pd
import numpy as np
import datetime


def generate_synthetic_data(days=14, freq='1H'):
    rng = pd.date_range(end=pd.Timestamp.now(), periods=24*days, freq=freq)
    n = len(rng)
    np.random.seed(42)

    # base load with daily seasonality
    hours = rng.hour.values
    base = 100 + 30 * np.sin((hours / 24.0) * 2 * np.pi)
    noise = np.random.normal(0, 5, size=n)
    temperature = 20 + 8 * np.sin((hours / 24.0) * 2 * np.pi) + np.random.normal(0,1,n)

    renewable = 50 * np.clip(np.sin(((hours-6)/24.0)*2*np.pi), 0, None)  # solar-like
    wind = 20 + 5 * np.sin(((hours+3)/24.0)*2*np.pi) + np.random.normal(0,3,n)

    load = base + renewable * 0.2 + wind * 0.1 + noise

    df = pd.DataFrame({
        'timestamp': rng,
        'load': load,
        'temperature': temperature,
        'solar': renewable + np.random.normal(0,2,n),
        'wind': wind + np.random.normal(0,1,n),
    })
    df = df.set_index('timestamp')
    return df
