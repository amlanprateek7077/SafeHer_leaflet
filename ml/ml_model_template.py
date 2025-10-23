# ml/ml_model_template.py
# Optional: use this template in Colab to analyze or retrain models.
import pandas as pd
from pathlib import Path
CSV_PATH = "data/woman_risk_for_frontend.csv"
df = pd.read_csv(CSV_PATH)
print(df.head())
# The dataset already has 'zone' and 'risk_score'. Use them for analysis / aggregation.
