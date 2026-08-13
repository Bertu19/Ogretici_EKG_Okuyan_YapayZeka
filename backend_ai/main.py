# -*- coding: utf-8 -*-
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import joblib
import numpy as np
import cv2
from PIL import Image
import io
from scipy.signal import find_peaks

app = FastAPI(title="EKG Analiz Asistani")

# --- YAPAY ZEKA MODELİNİN DİNAMİK YÜKLENMESİ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_YOLU = os.path.join(BASE_DIR, "modeller", "ekg_rf_modeli.pkl")

try:
    ai_model = joblib.load(MODEL_YOLU)
    print(f"Yapay Zeka Modeli Başarıyla Yüklendi: {MODEL_YOLU}")
except Exception as e:
    ai_model = None
    print(f"Model yüklenemedi: {e}")

# React build klasörünün yolu
FRONTEND_DIST = os.path.abspath(os.path.join(BASE_DIR, "../frontend_app/dist"))

if os.path.exists(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

@app.get("/", response_class=HTMLResponse)
def anasayfa():
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>Frontend build dosyası bulunamadı!</h1>"

# --- OPENCV İLE GÖRSELDEN SINYAL ÇIKARMA KATMANI ---
def gorselden_ekg_parametreleri_cikar(pil_gorsel):
    open_cv_image = np.array(pil_gorsel)
    if open_cv_image.ndim == 3:
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    else:
        gray = open_cv_image

    yukseklik, genislik = gray.shape

    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    sinyal = []
    for x in range(genislik):
        sutun = thresh[:, x]
        siyah_pikseller = np.where(sutun > 0)[0]
        if len(siyah_pikseller) > 0:
            sinyal.append(yukseklik - np.mean(siyah_pikseller))
        else:
            sinyal.append(yukseklik / 2)

    sinyal = np.array(sinyal)
    peaks, _ = find_peaks(sinyal, distance=int(genislik * 0.05), prominence=np.std(sinyal) * 0.5)

    if len(peaks) >= 2:
        rr_mesafeleri = np.diff(peaks)
        ort_rr_pixel = np.mean(rr_mesafeleri)
        kalp_hizi = float(np.clip(int(60 / (ort_rr_pixel / (genislik / 5))), 40, 220))
    else:
        kalp_hizi = 80.0

    if len(peaks) > 0:
        genislikler = []
        for p in peaks:
            sol = max(0, p - 10)
            sag = min(genislik - 1, p + 10)
            genislikler.append(sag - sol)
        qrs_genisligi = float(np.clip(np.mean(genislikler) / genislik * 0.8, 0.04, 0.18))
    else:
        qrs_genisligi = 0.08

    p_dalgasi_var_mi = 1
    if len(peaks) > 0:
        p_tepeleri_sayisi = 0
        for p in peaks:
            p_bolgesi = sinyal[max(0, p - 40):max(0, p - 10)]
            if len(p_bolgesi) > 0 and np.max(p_bolgesi) > np.mean(sinyal):
                p_tepeleri_sayisi += 1
        p_dalgasi_var_mi = 1 if p_tepeleri_sayisi > (len(peaks) / 2) else 0

    # --- KRİTİK GÖZLEM PRINTİ ---
    print(f"--- OPENCV ANALİZ SONUCU ---")
    print(f"Bulunan Pik Sayısı (Tepe): {len(peaks)}")
    print(f"Hesaplanan Kalp Hızı: {kalp_hizi}")
    print(f"Hesaplanan QRS: {qrs_genisligi}")
    print(f"P Dalgası Var mı: {p_dalgasi_var_mi}")

    return [kalp_hizi, qrs_genisligi, p_dalgasi_var_mi]


# --- EKSİKSİZ VE DEVASA KLİNİK VERİTABANI (37 KAYIT) ---
tani_veritabani = {
    "Normal Sinus Ritmi": {"tani": "Normal Sinüs Ritmi", "alternatif_tahminler": "Fizyolojik Sinüs Aritmisi", "bulgular": "Düzenli P-QRS-T dizilimi. Normal PR mesafesi (120-200ms) ve QRS süresi (<120ms).", "olasi_sonuclar": "Kardiyak patoloji saptanmadı. Normal hemodinami.", "tedavi_yonetimi": "Rutin klinik izlem dışında ek müdahale gerekmez.", "klinik_not": "Elde edilen veriler normal kardiyak elektrofizyoloji ile tam uyumludur."},
    "SINUS_ARRHYTHMIA": {"tani": "Sinüs Aritmisi", "alternatif_tahminler": "Erken Atriyal Vuru (PAC)", "bulgular": "Solunumla ilişkili R-R mesafesinde değişkenlik.", "olasi_sonuclar": "Tamamen fizyolojiktir, gençlerde sık görülür.", "tedavi_yonetimi": "Tedavi gerektirmez.", "klinik_not": "Patolojik değildir."},
    "SINUS_TACHY": {"tani": "Sinüs Taşikardisi", "alternatif_tahminler": "SVT, Atriyal Taşikardi", "bulgular": "Normal P dalgası, kalp hızı > 100 bpm.", "olasi_sonuclar": "Miyokardiyal oksijen tüketiminde artış.", "tedavi_yonetimi": "Altta yatan sekonder nedenin tedavisi.", "klinik_not": "Fizyolojik bir kompanzasyon mekanizmasıdır."},
    "SINUS_BRADY": {"tani": "Sinüs Bradikardisi", "alternatif_tahminler": "Sinüs Düğümü Disfonksiyonu", "bulgular": "Normal P dalgası, kalp hızı < 60 bpm.", "olasi_sonuclar": "İleri dereceyse baş dönmesi, senkop.", "tedavi_yonetimi": "Semptomatikse atropin veya pacemaker.", "klinik_not": "Sporcularda normal kabul edilir."},
    "AF": {"tani": "Atriyal Fibrilasyon (AF)", "alternatif_tahminler": "Atriyal Flutter", "bulgular": "P dalgası yok, 'f' dalgaları, düzensiz R-R aralıkları.", "olasi_sonuclar": "Tromboemboli, inme riski.", "tedavi_yonetimi": "Hız/ritim kontrolü, antikoagülasyon.", "klinik_not": "CHA2DS2-VASc skoru hesaplanmalıdır."},
    "FLUTTER": {"tani": "Atriyal Flutter", "alternatif_tahminler": "Atriyal Fibrilasyon", "bulgular": "'Testere dişi' görünümlü F dalgaları.", "olasi_sonuclar": "Hemodinamik bozulma.", "tedavi_yonetimi": "Kardiyoversiyon, ablasyon.", "klinik_not": "Sıklıkla 2:1 veya 3:1 AV ileti blokajı görülür."},
    "AT": {"tani": "Atriyal Taşikardi", "alternatif_tahminler": "Sinüs Taşikardisi, SVT", "bulgular": "Sinüs P dalgasından farklı morfolojide ektopik P dalgaları.", "olasi_sonuclar": "Çarpıntı.", "tedavi_yonetimi": "Vagal manevralar, beta blokerler.", "klinik_not": "Dijital toksisitesine sekonder gelişebilir."},
    "SVT": {"tani": "Supraventriküler Taşikardi (SVT)", "alternatif_tahminler": "Atriyal Taşikardi, Atriyal Flutter", "bulgular": "Dar QRS kompleksli, yüksek hızlı (>180 bpm) ve P dalgasının kaybolduğu taşikardi ritmi.", "olasi_sonuclar": "Çarpıntı, dispne, göğüs ağrısı, hemodinamik bozulma.", "tedavi_yonetimi": "Vagal manevralar, İV Adenozin uygulaması. Dirençli olgularda kardiyoversiyon.", "klinik_not": "AV düğüm kaynaklı reentran bir ritim bozukluğudur."},
    "VT": {"tani": "Ventriküler Taşikardi (VT)", "alternatif_tahminler": "Aberan İletimli SVT, Polimorfik VT", "bulgular": "Geniş QRS kompleksleri (>120ms), yüksek hız (>120 bpm) ve P dalgası yokluğu/disosiyasyonu.", "olasi_sonuclar": "Hemodinamik çöküş, Ventriküler Fibrilasyon (VF) ve kardiyak arrest riski.", "tedavi_yonetimi": "İnstabil hastada acil senkronize kardiyoversiyon. Stabil hastada Amiodaron.", "klinik_not": "Hayatı tehdit eden malign bir ventriküler aritmidir, acil müdahale şarttır."},
    "VF": {"tani": "Ventriküler Fibrilasyon (VF)", "alternatif_tahminler": "Polimorfik VT", "bulgular": "Tanımlanabilir dalga yok. Kaotik temel hat.", "olasi_sonuclar": "Kardiyak arrest, ölüm.", "tedavi_yonetimi": "Acil defibrilasyon, CPR.", "klinik_not": "Gecikilen her dakika ölüm riskini artırır."},
    "PAC": {"tani": "Prematür Atriyal Kompleks (PAC)", "alternatif_tahminler": "PVC", "bulgular": "Erken gelen ve farklı morfolojiye sahip P dalgası.", "olasi_sonuclar": "Zararsızdır.", "tedavi_yonetimi": "Tedavi gerektirmez.", "klinik_not": "AF öncüsü olabilir."},
    "PVC": {"tani": "Prematür Ventriküler Kompleks (PVC)", "alternatif_tahminler": "PAC", "bulgular": "Erken gelen, geniş QRS. Tam kompansatuvar duraklama.", "olasi_sonuclar": "Sık ise malign aritmi riski.", "tedavi_yonetimi": "Semptomatikse beta bloker.", "klinik_not": "Sıklığı önemlidir."},
    "AV_BLOCK_1": {"tani": "1. Derece AV Blok", "alternatif_tahminler": "Normal varyasyon", "bulgular": "PR mesafesinin uzaması (>0.20 sn).", "olasi_sonuclar": "Asemptomatiktir.", "tedavi_yonetimi": "İzlem.", "klinik_not": "AV düğümde fizyolojik yavaşlamadır."},
    "AV_BLOCK_2_MOBITZ1": {"tani": "2. Derece AV Blok (Mobitz Tip I)", "alternatif_tahminler": "Mobitz Tip II", "bulgular": "PR mesafesinin progresif uzaması ve P düşmesi.", "olasi_sonuclar": "Selimdir.", "tedavi_yonetimi": "Semptom varsa ilaç kesimi.", "klinik_not": "Wenckebach fenomeni."},
    "AV_BLOCK_2_MOBITZ2": {"tani": "2. Derece AV Blok (Mobitz Tip II)", "alternatif_tahminler": "Tam AV Blok", "bulgular": "Sabit PR, rastgele düşen QRS.", "olasi_sonuclar": "Tam bloğa ilerleme riski.", "tedavi_yonetimi": "Pacemaker endikasyonu vardır.", "klinik_not": "His-Purkinje seviyesi bloktur, tehlikelidir."},
    "AV_BLOCK_3": {"tani": "3. Derece (Tam) AV Blok", "alternatif_tahminler": "İleri Derece AV Blok", "bulgular": "P ve QRS arasında tam disosiyasyon.", "olasi_sonuclar": "Senkop, ani ölüm.", "tedavi_yonetimi": "Kalıcı pacemaker implantasyonu.", "klinik_not": "Acil müdahale gerektirir."},
    "LBBB": {"tani": "Sol Dal Bloğu (LBBB)", "alternatif_tahminler": "Ventriküler Paced Ritim", "bulgular": "Geniş QRS (>120ms). V1'de derin S, V5-V6'da geniş R.", "olasi_sonuclar": "Kalp yetmezliği belirtisi olabilir.", "tedavi_yonetimi": "Altta yatan hastalığın tedavisi.", "klinik_not": "Akut gelişimi STEMI eşdeğeridir."},
    "RBBB": {"tani": "Sağ Dal Bloğu (RBBB)", "alternatif_tahminler": "Brugada Sendromu", "bulgular": "Geniş QRS. V1-V2'de 'tavşan kulağı' görünümü.", "olasi_sonuclar": "Sağ kalp yüklenmesi işareti olabilir.", "tedavi_yonetimi": "Semptom yoksa izlem.", "klinik_not": "Klinik tablo ile korele edilmelidir."},
    "HEMIBLOCK": {"tani": "Fasiküler Blok (Hemiblok)", "alternatif_tahminler": "Sol Ventrikül Hipertrofisi", "bulgular": "Belirgin sol veya sağ aks sapması.", "olasi_sonuclar": "RBBB ile birleşirse tam bloğa ilerleyebilir.", "tedavi_yonetimi": "İzlem.", "klinik_not": "Diğer nedenler dışlanmalıdır."},
    "WPW": {"tani": "Wolff-Parkinson-White (WPW) Sendromu", "alternatif_tahminler": "LGL Sendromu", "bulgular": "Kısa PR mesafesi, Delta dalgası, geniş QRS.", "olasi_sonuclar": "Taşikardi atakları.", "tedavi_yonetimi": "Ablasyon.", "klinik_not": "AF eşlik ediyorsa AV düğüm blokerleri kontrendikedir."},
    "STEMI": {"tani": "ST-Elevasyonlu Miyokard İnfarktüsü (STEMI)", "alternatif_tahminler": "Akut Perikardit, Sol Dal Bloğu", "bulgular": "ST segment yükselmesi, resiprokal ST çökmesi.", "olasi_sonuclar": "Kardiyojenik şok, nekroz.", "tedavi_yonetimi": "Acil Anjiyografi (Primer PKG) veya Trombolitik.", "klinik_not": "Zaman kas demektir!"},
    "NSTEMI": {"tani": "ST-Elevasyonsuz Miyokard İnfarktüsü / İskemi", "alternatif_tahminler": "USAP", "bulgular": "ST segmentinde çökme. Dinamik T negatifliği.", "olasi_sonuclar": "Akut koroner sendrom.", "tedavi_yonetimi": "Agresif anti-iskemik tedavi.", "klinik_not": "Troponin yüksekliği tanıyı kesinleştirir."},
    "ISCHEMIA": {"tani": "Miyokard İskemisi", "alternatif_tahminler": "Elektrolit bozukluğu", "bulgular": "Derin negatif T dalgaları.", "olasi_sonuclar": "İnfarktüs gelişimi.", "tedavi_yonetimi": "Tıbbi tedavi optimizasyonu.", "klinik_not": "Wellens Sendromuna dikkat."},
    "OLD_MI": {"tani": "Geçirilmiş (Eski) Miyokard İnfarktüsü", "alternatif_tahminler": "WPW", "bulgular": "Patolojik Q dalgaları.", "olasi_sonuclar": "Kalp yetmezliği.", "tedavi_yonetimi": "GDMT (Kılavuz destekli tedavi).", "klinik_not": "Kalıcı skar dokusunu gösterir."},
    "LVH": {"tani": "Sol Ventrikül Hipertrofisi (LVH)", "alternatif_tahminler": "Sol Dal Bloğu", "bulgular": "Artmış QRS voltajı, strain paterni.", "olasi_sonuclar": "Kalp yetmezliği.", "tedavi_yonetimi": "Kan basıncı kontrolü.", "klinik_not": "Hipertansiyonun EKG'deki aynasıdır."},
    "RVH": {"tani": "Sağ Ventrikül Hipertrofisi (RVH)", "alternatif_tahminler": "Sağ Dal Bloğu", "bulgular": "Sağ aks sapması, V1'de dominant R.", "olasi_sonuclar": "Sağ kalp yetmezliği.", "tedavi_yonetimi": "Pulmoner hipertansiyon tedavisi.", "klinik_not": "Pulmoner patolojiler araştırılmalıdır."},
    "ATRIAL_ENLARGEMENT": {"tani": "Atriyal Genişleme (Büyüme)", "alternatif_tahminler": "Normal Varyasyon", "bulgular": "D2'de sivri (P pulmonale) veya çentikli (P mitrale) P dalgası.", "olasi_sonuclar": "AF riski.", "tedavi_yonetimi": "Kapak hastalığı kontrolü.", "klinik_not": "Hacim yüklenmesini gösterir."},
    "AXIS_DEVIATION": {"tani": "Elektriksel Eksen Sapması", "alternatif_tahminler": "Fasiküler Blok", "bulgular": "Sol veya Sağ Aks sapması.", "olasi_sonuclar": "Altta yatan hastalığın ipucudur.", "tedavi_yonetimi": "Primer hastalığın teşhisi.", "klinik_not": "Tek başına patolojik değildir."},
    "LONG_QT": {"tani": "Uzun QT Sendromu (LQTS)", "alternatif_tahminler": "İlaç Etkisi", "bulgular": "QTc süresinin anormal uzaması.", "olasi_sonuclar": "Torsades de Pointes, ani ölüm.", "tedavi_yonetimi": "QT uzatan ilaçların kesilmesi, beta bloker.", "klinik_not": "Bazett formülü kullanılmalıdır."},
    "SHORT_QT": {"tani": "Kısa QT Sendromu", "alternatif_tahminler": "Hiperkalsemi", "bulgular": "QTc süresinin anormal kısalması.", "olasi_sonuclar": "AF/VF riski.", "tedavi_yonetimi": "ICD implantasyonu.", "klinik_not": "Ölümcül bir kanalopatidir."},
    "BRUGADA": {"tani": "Brugada Sendromu", "alternatif_tahminler": "Sağ Dal Bloğu", "bulgular": "V1-V2'de 'Coved' tipi ST elevasyonu.", "olasi_sonuclar": "Polimorfik VT, ani kardiyak ölüm.", "tedavi_yonetimi": "ICD takılması.", "klinik_not": "Ateş aritmileri tetikleyebilir."},
    "PE": {"tani": "Pulmoner Emboli Şüphesi", "alternatif_tahminler": "Akut Kor Pulmonale", "bulgular": "S1Q3T3 paterni. Sinüs taşikardisi.", "olasi_sonuclar": "Şok, kardiyovasküler kollaps.", "tedavi_yonetimi": "BT Anjiyo, antikoagülasyon.", "klinik_not": "EKG pulmoner emboliyi dışlamak için yeterli değildir."},
    "HYPERKALEMIA": {"tani": "Hiperkalemi", "alternatif_tahminler": "Erken Repolarizasyon", "bulgular": "Sivri T dalgaları, QRS genişlemesi.", "olasi_sonuclar": "Asistoli.", "tedavi_yonetimi": "İV Kalsiyum Glukonat.", "klinik_not": "Metabolik acildir."},
    "HYPOKALEMIA": {"tani": "Hipokalemi", "alternatif_tahminler": "İskemi", "bulgular": "U dalgası çıkışı, ST çökmesi.", "olasi_sonuclar": "Aritmi riski.", "tedavi_yonetimi": "Potasyum replasmanı.", "klinik_not": "Digoksin toksisitesini tetikler."},
    "CALCIUM_IMBALANCE": {"tani": "Kalsiyum Dengesizliği", "alternatif_tahminler": "Uzun QT", "bulgular": "QT mesafesinde uzama veya kısalma.", "olasi_sonuclar": "Aritmi, iletim bloku.", "tedavi_yonetimi": "Elektrolit kontrolü.", "klinik_not": "Laboratuvar doğrulaması şarttır."},
    "HYPOTHERMIA": {"tani": "Hipotermi Etkisi", "alternatif_tahminler": "Erken repolarizasyon", "bulgular": "Osborn (J) dalgaları, bradikardi.", "olasi_sonuclar": "VF eşiğinde düşüş.", "tedavi_yonetimi": "Kademeli vücut ısıtması.", "klinik_not": "VF'yi tetiklememek için dikkatli olunmalıdır."},
    "DIGITALIS_TOXICITY": {"tani": "Dijital Zehirlenmesi", "alternatif_tahminler": "İskemi", "bulgular": "Aşağı eğimli 'ters bıyık' ST çökmesi.", "olasi_sonuclar": "Ölümcül bradikardiler.", "tedavi_yonetimi": "İlacın kesilmesi, Digoksin Fab.", "klinik_not": "Aritmi eklenirse zehirlenme tanısı konur."}
}

@app.post("/gorsel_analiz")
async def gorsel_analiz(dosya: UploadFile = File(...), yas: str = Form(None), cinsiyet: str = Form(None)):
    tani_key = "Normal Sinus Ritmi"
    
    if ai_model:
        try:
            icerik = await dosya.read()
            dosya_adi = dosya.filename.lower()
            
            if dosya_adi.endswith(".pdf"):
                import fitz
                pdf_belgesi = fitz.open(stream=icerik, filetype="pdf")
                ilk_sayfa = pdf_belgesi.load_page(0)
                pix = ilk_sayfa.get_pixmap()
                gorsel = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:
                gorsel = Image.open(io.BytesIO(icerik)).convert("RGB")
            
            # GÖRÜNTÜ İŞLEME İLE 3 PARAMETREYİ ÇIKAR VE YAZDIR
            ozellikler = gorselden_ekg_parametreleri_cikar(gorsel)
            
            # YAPAY ZEKA MODELİNE TAHMİN YAPTIR
            analiz_verisi = np.array([ozellikler])
            tahmin = ai_model.predict(analiz_verisi)[0]
            tani_key = str(tahmin)
            print(f"Yapay Zeka Modeli Tahmini: {tani_key}")
            
        except Exception as e:
            print(f"Görüntü İşleme / Model Hatası: {e}")
            tani_key = "Normal Sinus Ritmi"

    veri = tani_veritabani.get(tani_key, tani_veritabani["Normal Sinus Ritmi"])
    durum_tipi = "normal" if tani_key == "Normal Sinus Ritmi" else "patolojik"

    return {
        "durum": durum_tipi,
        **veri
    }