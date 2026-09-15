import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


class LiquidStateForecaster:
    """A lightweight reservoir computing forecaster (Liquid State Machine like).

    - fast, on-device friendly
    - trains a linear readout on reservoir states
    """
    def __init__(self, reservoir_size=200, input_dim=4, spectral_radius=0.9, sparsity=0.1, ridge=1e-6, random_state=42):
        self.reservoir_size = reservoir_size
        self.input_dim = input_dim  # [lag1, temperature, solar, wind]
        self.spectral_radius = spectral_radius
        self.sparsity = sparsity
        self.ridge = ridge
        self.random_state = random_state
        rng = np.random.RandomState(random_state)
        # Input weights: reservoir_size x input_dim
        self.Win = rng.uniform(-0.5, 0.5, size=(reservoir_size, input_dim))
        # Reservoir recurrent weights
        W = rng.uniform(-0.5, 0.5, size=(reservoir_size, reservoir_size))
        mask = rng.rand(reservoir_size, reservoir_size) < sparsity
        W *= mask
        # scale to spectral radius
        try:
            eigvals = np.linalg.eigvals(W)
            emax = np.max(np.abs(eigvals))
            if emax > 0:
                W *= (spectral_radius / emax)
        except Exception:
            pass
        self.W = W
        self.readout = None
        self.last_state = np.zeros(reservoir_size)
        self.trained = False

    def _features_from_df(self, df: pd.DataFrame):
        # prepare input vectors: lag1, temperature, solar, wind
        df2 = df.copy()
        df2['lag1'] = df2['load'].shift(1).fillna(method='bfill')
        X = df2[['lag1', 'temperature', 'solar', 'wind']].values
        y = df2['load'].values
        return X, y

    def train(self, df: pd.DataFrame):
        X, y = self._features_from_df(df)
        T = X.shape[0]
        states = np.zeros((T, self.reservoir_size))
        state = np.zeros(self.reservoir_size)
        for t in range(T):
            u = X[t]
            state = np.tanh(self.Win.dot(u) + self.W.dot(state))
            states[t] = state
        # build design matrix with states, inputs and bias
        S = np.hstack([states, X, np.ones((T,1))])
        # ridge regression solve: (S^T S + ridge I) w = S^T y
        A = S.T.dot(S) + self.ridge * np.eye(S.shape[1])
        b = S.T.dot(y)
        w = np.linalg.solve(A, b)
        self.readout = w
        self.last_state = state
        self.trained = True

    def save(self, path: str):
        """Persist reservoir and readout to a npz file."""
        np.savez(path, Win=self.Win, W=self.W, readout=self.readout, last_state=self.last_state)

    @classmethod
    def load(cls, path: str, **kwargs):
        """Load model from npz and return an instance."""
        data = np.load(path, allow_pickle=True)
        obj = cls(**kwargs)
        obj.Win = data['Win']
        obj.W = data['W']
        obj.readout = data['readout']
        obj.last_state = data['last_state']
        obj.trained = True
        return obj

    def predict_hours(self, hours=24):
        if not self.trained:
            raise RuntimeError('Model not trained')
        preds = []
        state = self.last_state.copy()
        # start input from last known features: use zeros fallback if not available
        # For demo, generate simple diurnal estimates for temp/solar/wind
        now = pd.Timestamp.now().floor('H')
        # initialize lag1 as last output from training readout via last input zero
        lag1 = 100.0
        for h in range(1, hours+1):
            t = now + pd.Timedelta(hours=h)
            hour = t.hour
            temp = 20 + 5*np.sin((hour/24.0)*2*np.pi)
            solar = max(0, 50*np.sin(((hour-6)/24.0)*2*np.pi))
            wind = 20 + 3*np.sin(((hour+3)/24.0)*2*np.pi)
            u = np.array([lag1, temp, solar, wind])
            state = np.tanh(self.Win.dot(u) + self.W.dot(state))
            S = np.concatenate([state, u, [1.0]])
            p = float(self.readout.dot(S))
            preds.append(p)
            lag1 = p
        return {str(i+1): preds[i] for i in range(len(preds))}


class ForecastModel(LiquidStateForecaster):
    """Backward-compatible alias: `ForecastModel` uses the liquid/reservoir forecaster."""
    pass


class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.02, random_state=42)

    def train(self, df: pd.DataFrame):
        X = df[['load','solar','wind','temperature']]
        self.model.fit(X)

    def detect_recent(self, df: pd.DataFrame, window_hours=48):
        recent = df.tail(window_hours)
        X = recent[['load','solar','wind','temperature']]
        preds = self.model.predict(X)
        anomalies = recent[preds==-1]
        # return minimal info
        return {
            'count': len(anomalies),
            'timestamps': [str(ts) for ts in anomalies.index.tolist()],
            'examples': anomalies.head(5).to_dict(orient='records')
        }
