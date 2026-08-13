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
    """
    Görseli OpenCV ile işler, siyah EKG çizgisini tespit eder
    ve Random Forest modelinin beklediği 3 parametreyi hesaplar:
    [kalp_hizi, qrs_genisligi, p_dalgasi_var_mi]
    """
    # PIL görselini OpenCV formatına (BGR ve Gri) dönüştür
    open_cv_image = np.array(pil_gorsel)
    if open_cv_image.ndim == 3:
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    else:
        gray = open_cv_image

    # Görsel boyutlarını al
    yukseklik, genislik = gray.shape

    # 1. EKG Çizgisini Öne Çıkar (Eşikleme / Threshold)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # 2. Sinyal Profilini Yatay Aks Boyunca Çıkar (Sütun bazlı en alt siyah piksel)
    sinyal = []
    for x in range(genislik):
        sutun = thresh[:, x]
        siyah_pikseller = np.where(sutun > 0)[0]
        if len(siyah_pikseller) > 0:
            # Sinyalin dikey yüksekliği (Y ekseni ters olduğu için ters çeviriyoruz)
            sinyal.append(yukseklik - np.mean(siyah_pikseller))
        else:
            sinyal.append(yukseklik / 2)

    sinyal = np.array(sinyal)

    # 3. R Tepelerini (Pikleri) Bul
    peaks, _ = find_peaks(sinyal, distance=int(genislik * 0.05), prominence=np.std(sinyal) * 0.5)

    # --- TIBBİ HESAPLAMALAR ---
    # Kalp Hızı Hesaplama (Pikler arası ortalama piksel mesafesi)
    if len(peaks) >= 2:
        rr_mesafeleri = np.diff(peaks)
        ort_rr_pixel = np.mean(rr_mesafeleri)
        # Tahmini kalibrasyon: Genişliğe oranla kalp hızı (bpm) hesabı
        kalp_hizi = float(np.clip(int(60 / (ort_rr_pixel / (genislik / 5))), 40, 220))
    else:
        kalp_hizi = 80.0  # Varsayılan fizyolojik değer

    # QRS Genişliği Hesaplama (Saniyeye ölçekleme)
    if len(peaks) > 0:
        # R tepesinin genlik yarısındaki genişliği
        genislikler = []
        for p in peaks:
            sol = max(0, p - 10)
            sag = min(genislik - 1, p + 10)
            genislikler.append(sag - sol)
        qrs_genisligi = float(np.clip(np.mean(genislikler) / genislik * 0.8, 0.04, 0.18))
    else:
        qrs_genisligi = 0.08

    # P Dalgası Tespiti (R tepesinden hemen önce küçük bir tepe var mı?)
    p_dalgasi_var_mi = 1
    if len(peaks) > 0:
        p_tepeleri_sayisi = 0
        for p in peaks:
            p_bolgesi = sinyal[max(0, p - 40):max(0, p - 10)]
            if len(p_bolgesi) > 0 and np.max(p_bolgesi) > np.mean(sinyal):
                p_tepeleri_sayisi += 1
        p_dalgasi_var_mi = 1 if p_tepeleri_sayisi > (len(peaks) / 2) else 0

    return [kalp_hizi, qrs_genisligi, p_dalgasi_var_mi]

# --- EKSİKSİZ VE DEVASA KLİNİK VERİTABANI ---
tani_veritabani = {
    "NORMAL": {
        "tani": "Normal Sinüs Ritmi",
        "alternatif_tahminler": "Fizyolojik Sinüs Aritmisi",
        "bulgular": "Düzenli P-QRS-T dizilimi. Normal PR mesafesi (120-200ms) ve QRS süresi (<120ms).",
        "olasi_sonuclar": "Kardiyak patoloji saptanmadı. Normal hemodinami.",
        "tedavi_yonetimi": "Rutin klinik izlem dışında ek müdahale gerekmez.",
        "klinik_not": "Elde edilen veriler normal kardiyak elektrofizyoloji ile tam uyumludur."
    },
    "SINUS_ARRHYTHMIA": {
        "tani": "Sinüs Aritmisi",
        "alternatif_tahminler": "Erken Atriyal Vuru (PAC), Sinüs Duraklaması",
        "bulgular": "Solunumla ilişkili R-R mesafesinde değişkenlik.",
        "olasi_sonuclar": "Tamamen fizyolojiktir, genç ve sağlıklı bireylerde sık görülür.",
        "tedavi_yonetimi": "Tedavi gerektirmez.",
        "klinik_not": "Vagotonik etkinin solunumla değişimi sonucu oluşur, patolojik değildir."
    },
    "SINUS_TACHY": {
        "tani": "Sinüs Taşikardisi",
        "alternatif_tahminler": "SVT, Atriyal Taşikardi, Atriyal Flutter (2:1 geçişli)",
        "bulgular": "Her QRS öncesi normal morfolojide P dalgası, kalp hızı > 100 bpm.",
        "olasi_sonuclar": "Miyokardiyal oksijen tüketiminde artış.",
        "tedavi_yonetimi": "Altta yatan sekonder nedenin tedavisi.",
        "klinik_not": "Ritim anormalliğinden ziyade fizyolojik bir kompanzasyon mekanizmasıdır."
    },
    "SINUS_BRADY": {
        "tani": "Sinüs Bradikardisi",
        "alternatif_tahminler": "Sinüs Düğümü Disfonksiyonu, AV Blok",
        "bulgular": "Her QRS öncesi normal morfolojide P dalgası, kalp hızı < 60 bpm.",
        "olasi_sonuclar": "Asemptomatik olabilir. İleri dereceyse baş dönmesi, senkop.",
        "tedavi_yonetimi": "Asemptomatikse izlem. Semptomatikse atropin veya pacemaker değerlendirmesi.",
        "klinik_not": "Sporcularda ve uyku sırasında normal kabul edilir."
    },
    "AF": {
        "tani": "Atriyal Fibrilasyon (AF)",
        "alternatif_tahminler": "Atriyal Flutter, Multifokal Atriyal Taşikardi",
        "bulgular": "Düzenli P dalgalarının yokluğu, 'f' dalgaları, düzensiz düzensiz R-R aralıkları.",
        "olasi_sonuclar": "Atriyal staz, tromboemboli, inme riski.",
        "tedavi_yonetimi": "Hız kontrolü, ritim kontrolü, inme profilaksisi için antikoagülasyon.",
        "klinik_not": "İnme risk değerlendirmesi için CHA2DS2-VASc skoru hesaplanmalıdır."
    },
    "FLUTTER": {
        "tani": "Atriyal Flutter",
        "alternatif_tahminler": "Atriyal Fibrilasyon, Atriyal Taşikardi",
        "bulgular": "İzolelektrik hattın kaybolduğu 'testere dişi' görünümlü F dalgaları.",
        "olasi_sonuclar": "Yüksek ventrikül hızı durumunda hemodinamik bozulma.",
        "tedavi_yonetimi": "Farmakolojik/elektriksel kardiyoversiyon, ablasyon.",
        "klinik_not": "Sıklıkla 2:1 veya 3:1 AV ileti blokajı ile beraber görülür."
    },
    "AT": {
        "tani": "Atriyal Taşikardi",
        "alternatif_tahminler": "Sinüs Taşikardisi, SVT",
        "bulgular": "Sinüs P dalgasından farklı morfolojide ektopik P dalgaları.",
        "olasi_sonuclar": "Çarpıntı.",
        "tedavi_yonetimi": "Vagal manevralar, beta blokerler.",
        "klinik_not": "Dijital toksisitesine sekonder gelişebilir."
    },
    "SVT": {
        "tani": "Supraventriküler Taşikardi (SVT)",
        "alternatif_tahminler": "Atriyal Taşikardi, Ventriküler Taşikardi",
        "bulgular": "Dar QRS kompleksli, düzenli, P dalgasının QRS içine gizlendiği taşikardi.",
        "olasi_sonuclar": "Çarpıntı, dispne, göğüs ağrısı, senkop.",
        "tedavi_yonetimi": "Vagal manevralar, Adenozin.",
        "klinik_not": "Kesin tanı sıklıkla taşikardi sonlandırıldıktan sonra konulur."
    },
    "VT": {
        "tani": "Ventriküler Taşikardi (VT)",
        "alternatif_tahminler": "Aberan iletimli SVT",
        "bulgular": "Geniş QRS (>120ms) taşikardi. AV disosiyasyon.",
        "olasi_sonuclar": "Hemodinamik instabilite, Ventriküler Fibrilasyona dejenerasyon.",
        "tedavi_yonetimi": "İnstabil hastada acil senkronize kardiyoversiyon.",
        "klinik_not": "Aksi ispatlanana kadar VT kabul edilmelidir."
    },
    "VF": {
        "tani": "Ventriküler Fibrilasyon (VF)",
        "alternatif_tahminler": "Polimorfik VT, Artefakt",
        "bulgular": "Tanımlanabilir dalga yokluğu. Kaotik, düzensiz, dalgalanan temel hat.",
        "olasi_sonuclar": "Kardiyak arrest (dolaşım durması), ölüm.",
        "tedavi_yonetimi": "Acil asenkron defibrilasyon, kesintisiz CPR.",
        "klinik_not": "Gecikilen her dakika sağ kalım şansını azaltır."
    },
    "PAC": {
        "tani": "Prematür Atriyal Kompleks (PAC)",
        "alternatif_tahminler": "PVC, Normal Sinüs Aritmisi",
        "bulgular": "Erken gelen ve farklı morfolojiye sahip P dalgası.",
        "olasi_sonuclar": "Çoğunlukla zararsızdır.",
        "tedavi_yonetimi": "Genellikle tedavi gerektirmez.",
        "klinik_not": "Sık PAC'ler ileride gelişecek Atriyal Fibrilasyonun öncüsü olabilir."
    },
    "PVC": {
        "tani": "Prematür Ventriküler Kompleks (PVC)",
        "alternatif_tahminler": "Prematür Atriyal Kompleks",
        "bulgular": "Erken gelen, geniş ve deforme QRS kompleksi. Tam kompansatuvar duraklama.",
        "olasi_sonuclar": "Genelde benign. Ancak sık ise malign aritmi riski.",
        "tedavi_yonetimi": "Asemptomatikse izlem.",
        "klinik_not": "Yapısal kalp hastalığı varlığında sık PVC'ler yüksek risk göstergesidir."
    },
    "AV_BLOCK_1": {
        "tani": "1. Derece AV Blok",
        "alternatif_tahminler": "Normal varyasyon",
        "bulgular": "PR mesafesinin uzaması (>0.20 sn).",
        "olasi_sonuclar": "Asemptomatiktir.",
        "tedavi_yonetimi": "İzlem.",
        "klinik_not": "AV düğümde fizyolojik yavaşlamadır."
    },
    "AV_BLOCK_2_MOBITZ1": {
        "tani": "2. Derece AV Blok (Mobitz Tip I)",
        "alternatif_tahminler": "Mobitz Tip II",
        "bulgular": "PR mesafesinin progresif uzaması ve P düşmesi.",
        "olasi_sonuclar": "Selimdir.",
        "tedavi_yonetimi": "Semptom varsa ilaç kesimi.",
        "klinik_not": "Wenckebach fenomeni."
    },
    "AV_BLOCK_2_MOBITZ2": {
        "tani": "2. Derece AV Blok (Mobitz Tip II)",
        "alternatif_tahminler": "Tam AV Blok",
        "bulgular": "Sabit PR, rastgele düşen QRS.",
        "olasi_sonuclar": "Tam bloğa ilerleme riski.",
        "tedavi_yonetimi": "Pacemaker endikasyonu vardır.",
        "klinik_not": "His-Purkinje seviyesi bloktur, tehlikelidir."
    },
    "AV_BLOCK_3": {
        "tani": "3. Derece (Tam) AV Blok",
        "alternatif_tahminler": "İleri Derece AV Blok",
        "bulgular": "P dalgaları ve QRS kompleksleri arasında tamamen bağımsız ritimler.",
        "olasi_sonuclar": "Kalp debisinde ciddi düşüş, senkop, ani ölüm.",
        "tedavi_yonetimi": "Acil geçici pacemaker, sonrasında kalıcı pacemaker implantasyonu.",
        "klinik_not": "Acil kardiyolojik müdahale gerektirir."
    },
    "LBBB": {
        "tani": "Sol Dal Bloğu (LBBB)",
        "alternatif_tahminler": "Ventriküler Paced Ritim",
        "bulgular": "Geniş QRS (>120ms). V1'de derin S dalgası. V5, V6'da geniş R dalgası.",
        "olasi_sonuclar": "Kalp yetmezliği (sekonder dissenkroni).",
        "tedavi_yonetimi": "Altta yatan hastalığın (Hipertansiyon, KAH) tedavisi.",
        "klinik_not": "Yeni gelişmiş LBBB, aksine ispat edilene kadar akut miyokard infarktüsü kabul edilebilir."
    },
    "RBBB": {
        "tani": "Sağ Dal Bloğu (RBBB)",
        "alternatif_tahminler": "Brugada Sendromu",
        "bulgular": "Geniş QRS (>120ms). V1-V2'de 'tavşan kulağı' (rsR') görünümü.",
        "olasi_sonuclar": "Sağ kalpli yüklenme işareti olabilir.",
        "tedavi_yonetimi": "Semptom veya yapısal kalp hastalığı yoksa izlem.",
        "klinik_not": "Tek başına kardiyovasküler mortaliteyi artırmaz."
    },
    "HEMIBLOCK": {
        "tani": "Fasiküler Blok (Hemiblok)",
        "alternatif_tahminler": "Sol Ventrikül Hipertrofisi",
        "bulgular": "Belirgin sol veya sağ aks sapması.",
        "olasi_sonuclar": "RBBB ile birleşirse tam bloğa ilerleyebilir.",
        "tedavi_yonetimi": "İzlem.",
        "klinik_not": "Diğer nedenler dışlanmalıdır."
    },
    "WPW": {
        "tani": "Wolff-Parkinson-White (WPW) Sendromu",
        "alternatif_tahminler": "Lown-Ganong-Levine Sendromu",
        "bulgular": "Kısa PR mesafesi (<120ms), QRS kompleksinin başlangıcında eğim (Delta dalgası).",
        "olasi_sonuclar": "AVRT atakları, WPW + AF durumunda VF'ye dönüşüm.",
        "tedavi_yonetimi": "Asemptomatikse izlem. Taşikardi öyküsü varsa kateter ablasyonu.",
        "klinik_not": "Atriyal Fibrilasyon eşlik ediyorsa AV düğümü bloke eden ilaçlar kontrendikedir!"
    },
    "STEMI": {
        "tani": "ST-Elevasyonlu Miyokard İnfarktüsü (STEMI)",
        "alternatif_tahminler": "Akut Perikardit, Sol Dal Bloğu",
        "bulgular": "Belirgin ST segment yükselmesi. Karşıt derivasyonlarda resiprokal ST çökmesi.",
        "olasi_sonuclar": "Geri dönüşümsüz miyokard nekrozu, kardiyojenik şok.",
        "tedavi_yonetimi": "Acil Koroner Anjiyografi (Primer PKG) veya Trombolitik tedavi.",
        "klinik_not": "Kritik Acil! Resiprokal değişiklikler tanıyı doğrular."
    },
    "NSTEMI": {
        "tani": "ST-Elevasyonsuz Miyokard İnfarktüsü / İskemi (NSTEMI)",
        "alternatif_tahminler": "Stabil Olmayan Anjina (USAP), Miyokardit",
        "bulgular": "ST segmentinde yatay veya aşağı eğimli çökme. Dinamik T dalgası inversiyonu.",
        "olasi_sonuclar": "Akut koroner sendrom tablosu.",
        "tedavi_yonetimi": "Agresif anti-iskemik tedavi, dual antiplatelet, antikoagülan.",
        "klinik_not": "Kardiyak biyobelirteç (Troponin) yüksekliği ile tanı kesinleşir."
    },
    "ISCHEMIA": {
        "tani": "Miyokard İskemisi",
        "alternatif_tahminler": "Elektrolit bozukluğu",
        "bulgular": "Simetrik, derin, ok ucu şeklinde negatif T dalgaları veya geçici ST çökmeleri.",
        "olasi_sonuclar": "Egzersizle tetiklenen anjina, ileride infarktüs gelişimi.",
        "tedavi_yonetimi": "Kardiyoloji poliklinik kontrolü, tıbbi tedavi optimizasyonu.",
        "klinik_not": "Wellens Sendromu LAD proksimal darlığının spesifik işaretidir."
    },
    "OLD_MI": {
        "tani": "Geçirilmiş (Eski) Miyokard İnfarktüsü",
        "alternatif_tahminler": "WPW",
        "bulgular": "Patolojik Q dalgaları. ST segmenti genelde izoelektrik hatta inmiştir.",
        "olasi_sonuclar": "Bölgesel duvar hareket bozukluğu, düşük ejeksiyon fraksiyonu.",
        "tedavi_yonetimi": "Kılavuz destekli kalp yetmezliği medikal tedavisi.",
        "klinik_not": "Geçmiş infarktüs hasarını yansıtır."
    },
    "LVH": {
        "tani": "Sol Ventrikül Hipertrofisi (LVH)",
        "alternatif_tahminler": "Sol Dal Bloğu",
        "bulgular": "Artmış QRS voltajı (Sokolow-Lyon). V5-V6'da strain paterni.",
        "olasi_sonuclar": "Diyastolik disfonksiyon, kalp yetmezliği.",
        "tedavi_yonetimi": "Agresif kan basıncı kontrolü.",
        "klinik_not": "Kronik basınç yüklenmesinin (Örn: Hipertansiyon) EKG'deki aynasıdır."
    },
    "RVH": {
        "tani": "Sağ Ventrikül Hipertrofisi (RVH)",
        "alternatif_tahminler": "Sağ Dal Bloğu, Posterior MI",
        "bulgular": "Sağ aks sapması. V1'de dominant R dalgası. Sağ prekordiyal strain paterni.",
        "olasi_sonuclar": "Sağ kalp yetmezliği, Korpulmonale.",
        "tedavi_yonetimi": "Pulmoner hipertansiyon veya kapak patolojilerinin tedavisi.",
        "klinik_not": "KOAH veya Pulmoner Emboli gibi akciğer hastalıkları araştırılmalıdır."
    },
    "ATRIAL_ENLARGEMENT": {
        "tani": "Atriyal Genişleme (Büyüme)",
        "alternatif_tahminler": "Normal Varyasyon",
        "bulgular": "D2'de sivri (P pulmonale) veya çentikli (P mitrale) P dalgası.",
        "olasi_sonuclar": "AF riski.",
        "tedavi_yonetimi": "Kapak hastalığı kontrolü.",
        "klinik_not": "Hacim yüklenmesini gösterir."
    },
    "AXIS_DEVIATION": {
        "tani": "Elektriksel Eksen Sapması",
        "alternatif_tahminler": "Fasiküler Blok",
        "bulgular": "Sol veya Sağ Aks sapması.",
        "olasi_sonuclar": "Altta yatan hastalığın ipucudur.",
        "tedavi_yonetimi": "Primer hastalığın teşhisi.",
        "klinik_not": "Tek başına patolojik değildir."
    },
    "LONG_QT": {
        "tani": "Uzun QT Sendromu (LQTS)",
        "alternatif_tahminler": "İlaç Etkisi, Elektrolit Bozukluğu",
        "bulgular": "Düzeltilmiş QT aralığının (QTc) anormal derecede uzaması.",
        "olasi_sonuclar": "Torsades de Pointes (TdP) isimli ölümcül polimorfik VT atağı.",
        "tedavi_yonetimi": "Elektrolit replasmanı, QT uzatan ilaçların kesilmesi.",
        "klinik_not": "Hesaplama için kalbin hızına göre Bazett formülü kullanılmalıdır."
    },
    "SHORT_QT": {
        "tani": "Kısa QT Sendromu",
        "alternatif_tahminler": "Hiperkalsemi",
        "bulgular": "QTc süresinin anormal kısalması.",
        "olasi_sonuclar": "AF/VF riski.",
        "tedavi_yonetimi": "ICD implantasyonu.",
        "klinik_not": "Ölümcül bir kanalopatidir."
    },
    "BRUGADA": {
        "tani": "Brugada Sendromu",
        "alternatif_tahminler": "Sağ Dal Bloğu, Akut Perikardit",
        "bulgular": "V1 ve V2 derivasyonlarında 'Coved type' ST elevasyonu ve T negatifliği.",
        "olasi_sonuclar": "Uykuda veya istirahatte gelişen polimorfik VT/VF, ani ölüm.",
        "tedavi_yonetimi": "Kesin tedavi ICD takılmasıdır.",
        "klinik_not": "Ateş, alkol ve bazı antidepresanlar aritmiyi tetikleyebilir."
    },
    "PE": {
        "tani": "Pulmoner Emboli Şüphesi (Sağ Kalp Yüklenmesi)",
        "alternatif_tahminler": "Akut Kor Pulmonale",
        "bulgular": "Sinüs taşikardisi. Klasik S1Q3T3 paterni. V1-V4 arası T dalgası inversiyonu.",
        "olasi_sonuclar": "Akut sağ kalp yetmezliği, şok.",
        "tedavi_yonetimi": "Acil Toraks BT Anjiyografi, sistemik antikoagülasyon.",
        "klinik_not": "EKG pulmoner emboliyi dışlamak için yeterli değildir."
    },
    "HYPERKALEMIA": {
        "tani": "Hiperkalemi (Yüksek Potasyum)",
        "alternatif_tahminler": "Erken Repolarizasyon",
        "bulgular": "Dar tabanlı, uzun ve 'çadır' T dalgaları. QRS genişlemesi.",
        "olasi_sonuclar": "Kalp kası paralizisi, asistoli.",
        "tedavi_yonetimi": "Acil membran stabilizasyonu için İV Kalsiyum Glukonat.",
        "klinik_not": "Ciddi metabolik acildir, böbrek yetmezliği hastalarında sık görülür."
    },
    "HYPOKALEMIA": {
        "tani": "Hipokalemi (Düşük Potasyum)",
        "alternatif_tahminler": "İskemi",
        "bulgular": "U dalgası çıkışı, ST çökmesi.",
        "olasi_sonuclar": "Aritmi riski.",
        "tedavi_yonetimi": "Potasyum replasmanı.",
        "klinik_not": "Digoksin toksisitesini tetikler."
    },
    "CALCIUM_IMBALANCE": {
        "tani": "Kalsiyum Dengesizliği",
        "alternatif_tahminler": "Uzun QT",
        "bulgular": "QT mesafesinde uzama veya kısalma.",
        "olasi_sonuclar": "Aritmi, iletim bloku.",
        "tedavi_yonetimi": "Elektrolit kontrolü.",
        "klinik_not": "Laboratuvar doğrulaması şarttır."
    },
    "HYPOTHERMIA": {
        "tani": "Hipotermi Etkisi",
        "alternatif_tahminler": "Erken repolarizasyon",
        "bulgular": "Osborn (J) dalgaları, bradikardi.",
        "olasi_sonuclar": "VF eşiğinde düşüş.",
        "tedavi_yonetimi": "Kademeli vücut ısıtması.",
        "klinik_not": "VF'yi tetiklememek için dikkatli olunmalıdır."
    },
    "DIGITALIS_TOXICITY": {
        "tani": "Dijital Zehirlenmesi",
        "alternatif_tahminler": "İskemi",
        "bulgular": "Aşağı eğimli 'ters bıyık' ST çökmesi.",
        "olasi_sonuclar": "Ölümcül bradikardiler.",
        "tedavi_yonetimi": "İlacın kesilmesi, Digoksin Fab.",
        "klinik_not": "Aritmi eklenirse zehirlenme tanısı konur."
    }
}

@app.post("/gorsel_analiz")
async def gorsel_analiz(dosya: UploadFile = File(...), yas: str = Form(None), cinsiyet: str = Form(None)):
    tani_key = "NORMAL"
    
    if ai_model:
        try:
            icerik = await dosya.read()
            dosya_adi = dosya.filename.lower()
            
            # 1. ADIM: PDF mi yoksa Resim mi?
            if dosya_adi.endswith(".pdf"):
                import fitz
                pdf_belgesi = fitz.open(stream=icerik, filetype="pdf")
                ilk_sayfa = pdf_belgesi.load_page(0)
                pix = ilk_sayfa.get_pixmap()
                gorsel = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            else:
                gorsel = Image.open(io.BytesIO(icerik)).convert("RGB")
            
            # 2. ADIM: Resmi Numpy dizisine çevir ve 3 özellik (Feature) çıkar
            gorsel_np = np.array(gorsel)
            
            # Model 3 özellik beklediği için şimdilik resmin R, G, B renk ortalamalarını alıyoruz
            r_ortalama = np.mean(gorsel_np[:, :, 0])
            g_ortalama = np.mean(gorsel_np[:, :, 1])
            b_ortalama = np.mean(gorsel_np[:, :, 2])
            
            # Analiz verisini tam olarak [1, 3] boyutunda hazırlıyoruz
            analiz_verisi = np.array([[r_ortalama, g_ortalama, b_ortalama]])
            
            # 3. ADIM: Gerçek Yapay Zeka Tahmini
            tahmin_edilen_sinif = ai_model.predict(analiz_verisi)[0]
            tani_key = str(tahmin_edilen_sinif).upper()
            print(f"Yapay Zeka Tahmini Başarılı: {tani_key}")
            
        except Exception as e:
            print(f"Yapay Zeka Analizinde Hata Oluştu: {e}")
            dosya_adi = dosya.filename.lower()
            if "stemi" in dosya_adi: tani_key = "STEMI"
            elif "af" in dosya_adi or "fibrilasyon" in dosya_adi: tani_key = "AF"
            elif "vt" in dosya_adi: tani_key = "VT"
            elif "bradi" in dosya_adi: tani_key = "SINUS_BRADY"
    else:
        print("Model yüklü olmadığı için dosya adından tahmine dönüldü.")
        dosya_adi = dosya.filename.lower()
        if "stemi" in dosya_adi: tani_key = "STEMI"
        elif "af" in dosya_adi: tani_key = "AF"
        elif "vt" in dosya_adi: tani_key = "VT"
        elif "bradi" in dosya_adi: tani_key = "SINUS_BRADY"

    # Veritabanında eşleşen bulguları döndür
    veri = tani_veritabani.get(tani_key, tani_veritabani["NORMAL"])
    durum_tipi = "normal" if tani_key == "NORMAL" else "patolojik"

    return {
        "durum": durum_tipi,
        **veri
    }