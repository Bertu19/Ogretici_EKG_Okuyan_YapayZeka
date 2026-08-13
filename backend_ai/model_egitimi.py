import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def veri_olustur(ornek_sayisi=3000):
    np.random.seed(42)
    veri = []
    
    # 5 Farklı EKG Durumu (Sınıfı) eğitiyoruz
    durumlar = ["Normal Sinus Ritmi", "SINUS_TACHY", "SINUS_BRADY", "SVT", "VT"]
    
    for _ in range(ornek_sayisi):
        durum = np.random.choice(durumlar)
        
        if durum == "Normal Sinus Ritmi":
            kalp_hizi = np.random.randint(60, 100)
            qrs = np.random.uniform(0.04, 0.09)
            p_var = 1
            
        elif durum == "SINUS_TACHY": # Az önceki testte takıldığımız durum (Hızlı ama P dalgası var)
            kalp_hizi = np.random.randint(101, 160)
            qrs = np.random.uniform(0.04, 0.09)
            p_var = 1
            
        elif durum == "SINUS_BRADY":
            kalp_hizi = np.random.randint(40, 59)
            qrs = np.random.uniform(0.04, 0.09)
            p_var = 1
            
        elif durum == "SVT":
            kalp_hizi = np.random.randint(150, 250)
            qrs = np.random.uniform(0.04, 0.09)
            p_var = 0 # P dalgası yüksek hızdan dolayı QRS'in içine gizlenir/kaybolur
            
        elif durum == "VT":
            kalp_hizi = np.random.randint(120, 220)
            qrs = np.random.uniform(0.12, 0.20) # QRS'in kesinlikle geniş olması gerekir
            p_var = 0
            
        veri.append([kalp_hizi, qrs, p_var, durum])
        
    return pd.DataFrame(veri, columns=["kalp_hizi", "qrs_genisligi", "p_dalgasi_var_mi", "hedef_sinif"])

print("Gelişmiş EKG Veri seti olusturuluyor...")
df = veri_olustur()

# Özellikler (X) ve Hedef Sınıf (y)
X = df[["kalp_hizi", "qrs_genisligi", "p_dalgasi_var_mi"]]
y = df["hedef_sinif"]

print("Random Forest modeli 5 sınıf ile egitiliyor...")
rf_model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
rf_model.fit(X.values, y)

# Modeli her zaman "backend_ai/modeller" içine kaydetmesi için dinamik yol:
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_KLASORU = os.path.join(BASE_DIR, "modeller")

os.makedirs(MODEL_KLASORU, exist_ok=True)
joblib.dump(rf_model, os.path.join(MODEL_KLASORU, "ekg_rf_modeli.pkl"))
print("Model basariyla egitildi ve dogru klasore kaydedildi!")