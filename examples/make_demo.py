import numpy as np
import pandas as pd

r = np.random.default_rng(7)
n = 5000
amt = r.lognormal(3, 1, n)
hour = r.integers(0, 24, n)
dist = r.exponential(20, n)
z = 0.8 * np.log(amt) + 0.05 * dist + (hour < 5) * 1.2 - 7
y = (r.random(n) < 1 / (1 + np.exp(-z))).astype(int)
pd.DataFrame({
    "txn_id": [f"t{i}" for i in range(n)],
    "amount": amt,
    "hour": hour,
    "dist_home_km": dist,
    "channel": r.choice(["web", "app", "pos"], n),
    "chargeback_flag": y * 1.0,
    "is_fraud": y,
}).to_csv("demo.csv", index=False)
print("demo.csv written, fraud rate", round(float(y.mean()), 4))