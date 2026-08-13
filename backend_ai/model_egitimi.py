import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def veri_olustur(ornek_sayisi=1000):
    np.random.seed(42)
    veri = []
    for _ in range(ornek_sayisi):
        durum = np.random.choice(["Normal Sinus Ritmi", "SVT", "VT"])
        
        if durum == "Normal Sinus Ritmi":
            kalp_hizi = np.random.randint(60, 100)
            qrs = np.random.uniform(0.04, 0.08)
            p_var = 1
        elif durum == "SVT":
            kalp_hizi = np.random.randint(180, 250)
            qrs = np.random.uniform(0.04, 0.09)
            p_var = 0
        else:
            kalp_hizi = np.random.randint(121, 200)
            qrs = np.random.uniform(0.10, 0.16)
            p_var = 0
            
        veri.append([kalp_hizi, qrs, p_var, durum])
        
    return pd.DataFrame(veri, columns=["kalp_hizi", "qrs_genisligi", "p_dalgasi_var_mi", "hedef_sinif"])

print("EKG Veri seti olusturuluyor...")
df = veri_olustur()

X = df[["kalp_hizi", "qrs_genisligi", "p_dalgasi_var_mi"]]
y = df["hedef_sinif"]

print("Random Forest modeli egitiliyor...")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X.values, y)

os.makedirs("modeller", exist_ok=True)
joblib.dump(rf_model, "modeller/ekg_rf_modeli.pkl")
print("Model basariyla egitildi ve kaydedildi!")