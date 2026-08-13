# -*- coding: utf-8 -*-
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import joblib

app = FastAPI(title="EKG Analiz Asistani")

# Model yolu kontrolü
MODEL_YOLU = "modeller/ekg_rf_modeli.pkl"
ai_model = joblib.load(MODEL_YOLU) if os.path.exists(MODEL_YOLU) else None

# React build klasörünün yolu (ana dizindeki frontend_app/dist klasörünü gösterir)
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend_app/dist"))

if os.path.exists(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

@app.get("/", response_class=HTMLResponse)
def anasayfa():
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return "<h1>Frontend build dosyası bulunamadı! Lütfen önce 'npm run build' çalıştırın.</h1>"

@app.post("/gorsel_analiz")
async def gorsel_analiz(dosya: UploadFile = File(...), yas: str = Form(None), cinsiyet: str = Form(None)):
    # Burası sizin yapay zeka modelinizin teşhis koyduğu yerdir.
    # Şimdilik örnek olarak bir 'tani_kodu' üzerinden dinamik yapı kuralım:
    
    tani_veritabani = {
    # ─── NORMAL VE FİZYOLOJİK DURUMLAR ──────────────────────────────────────
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
        "bulgular": "Solunumla ilişkili R-R mesafesinde değişkenlik (inspiryumda hızlanma, ekspiryumda yavaşlama).",
        "olasi_sonuclar": "Tamamen fizyolojiktir, genç ve sağlıklı bireylerde sık görülür.",
        "tedavi_yonetimi": "Tedavi gerektirmez.",
        "klinik_not": "Vagotonik etkinin solunumla değişimi sonucu oluşur, patolojik değildir."
    },

    # ─── RİTİM BOZUKLUKLARI (TAŞİKARDİ VE BRADİKARDİLER) ────────────────────
    "SINUS_TACHY": {
        "tani": "Sinüs Taşikardisi",
        "alternatif_tahminler": "SVT, Atriyal Taşikardi, Atriyal Flutter (2:1 geçişli)",
        "bulgular": "Her QRS öncesi normal morfolojide P dalgası, kalp hızı > 100 bpm.",
        "olasi_sonuclar": "Miyokardiyal oksijen tüketiminde artış, altta yatan strese sekonder yüklenme.",
        "tedavi_yonetimi": "Altta yatan sekonder nedenin (ateş, anemi, anksiyete, hipovolemi, hipertiroidi) tedavisi.",
        "klinik_not": "Ritim anormalliğinden ziyade fizyolojik bir kompanzasyon mekanizmasıdır."
    },
    "SINUS_BRADY": {
        "tani": "Sinüs Bradikardisi",
        "alternatif_tahminler": "Sinüs Düğümü Disfonksiyonu, AV Blok",
        "bulgular": "Her QRS öncesi normal morfolojide P dalgası, kalp hızı < 60 bpm.",
        "olasi_sonuclar": "Asemptomatik olabilir. İleri dereceyse baş dönmesi, senkop, yorgunluk.",
        "tedavi_yonetimi": "Asemptomatikse izlem. Semptomatikse atropin, dopamin veya pacemaker değerlendirmesi.",
        "klinik_not": "Sporcularda ve uyku sırasında vagal tonus artışına bağlı normal kabul edilir."
    },
    "AF": {
        "tani": "Atriyal Fibrilasyon (AF)",
        "alternatif_tahminler": "Atriyal Flutter, Multifokal Atriyal Taşikardi",
        "bulgular": "Düzenli P dalgalarının yokluğu, 'f' (fibrilasyon) dalgaları, düzensiz düzensiz R-R aralıkları.",
        "olasi_sonuclar": "Atriyal staz, tromboemboli, inme riski, taşikardi kaynaklı kardiyomiyopati.",
        "tedavi_yonetimi": "Hız kontrolü (Beta bloker/Kalsiyum kanal blokeri), ritim kontrolü, inme profilaksisi için antikoagülasyon (OAK).",
        "klinik_not": "İnme risk değerlendirmesi için CHA2DS2-VASc skoru mutlak suretle hesaplanmalıdır."
    },
    "FLUTTER": {
        "tani": "Atriyal Flutter",
        "alternatif_tahminler": "Atriyal Fibrilasyon, Atriyal Taşikardi",
        "bulgular": "İzolelektrik hattın kaybolduğu 'testere dişi' görünümlü F dalgaları (genellikle 250-350/dk atriyal hız).",
        "olasi_sonuclar": "Yüksek ventrikül hızı durumunda hemodinamik bozulma, tromboemboli.",
        "tedavi_yonetimi": "Farmakolojik veya elektriksel kardiyoversiyon, ablasyon, antikoagülan tedavi.",
        "klinik_not": "Sıklıkla 2:1 veya 3:1 AV ileti blokajı ile beraber görülür."
    },
    "AT": {
        "tani": "Atriyal Taşikardi",
        "alternatif_tahminler": "Sinüs Taşikardisi, SVT",
        "bulgular": "Sinüs P dalgasından farklı morfolojide ektopik P dalgaları. Hız genelde 150-250 bpm.",
        "olasi_sonuclar": "Çarpıntı, nadiren kalp yetmezliği tetiklenmesi.",
        "tedavi_yonetimi": "Vagal manevralar, adenozin, kalsiyum kanal blokerleri veya beta blokerler.",
        "klinik_not": "Dijital toksisitesine bağlı gelişen atriyal taşikardiye sıklıkla AV blok eşlik eder."
    },
    "SVT": {
        "tani": "Supraventriküler Taşikardi (SVT)",
        "alternatif_tahminler": "Atriyal Taşikardi, Atriyal Flutter, Ventriküler Taşikardi (Geniş QRS ise)",
        "bulgular": "Dar QRS kompleksli (<120ms), düzenli, genellikle P dalgasının QRS içine gizlendiği taşikardi (AVNRT/AVRT).",
        "olasi_sonuclar": "Çarpıntı, dispne, göğüs ağrısı, senkop.",
        "tedavi_yonetimi": "Vagal manevralar, Adenozin (hızlı IV pule), kalsiyum kanal blokerleri. Dirençli ise kardiyoversiyon.",
        "klinik_not": "Kesin tanı sıklıkla taşikardi sonlandırıldıktan sonra konulur."
    },
    "VT": {
        "tani": "Ventriküler Taşikardi (VT)",
        "alternatif_tahminler": "Aberan iletimli SVT, Antidromik AVRT (WPW)",
        "bulgular": "Geniş QRS (>120ms) taşikardi (hız >100 bpm). AV disosiyasyon, yakalama (capture) veya füzyon vuruşları.",
        "olasi_sonuclar": "Hemodinamik instabilite, Ventriküler Fibrilasyona dejenerasyon, kardiyak arrest.",
        "tedavi_yonetimi": "İnstabil hastada acil senkronize kardiyoversiyon. Stabil hastada Amiodaron veya Lidokain.",
        "klinik_not": "Yapısal kalp hastalığı olanlarda geniş QRS'li taşikardi aksi ispatlanana kadar VT kabul edilmelidir."
    },
    "VF": {
        "tani": "Ventriküler Fibrilasyon (VF)",
        "alternatif_tahminler": "Polimorfik VT, Ciddi EKG Artefaktı",
        "bulgular": "Tanımlanabilir P, QRS veya T dalgası yokluğu. Kaotik, düzensiz, dalgalanan temel hat.",
        "olasi_sonuclar": "Kardiyak arrest (dolaşım durması), saniyeler içinde bilinç kaybı, ölüm.",
        "tedavi_yonetimi": "Acil asenkron defibrilasyon, kesintisiz CPR, ileri kardiyak yaşam desteği (ACLS).",
        "klinik_not": "Gecikilen her dakika sağ kalım şansını %7-10 oranında azaltır."
    },
    "PAC": {
        "tani": "Prematür Atriyal Kompleks (PAC)",
        "alternatif_tahminler": "Erken Ventriküler Vuru (PVC), Normal Sinüs Aritmisi",
        "bulgular": "Erken gelen ve sinüs P dalgasından farklı morfolojiye sahip P dalgası. Genellikle dar QRS.",
        "olasi_sonuclar": "Çoğunlukla zararsızdır, hastalarda 'kalpte atlama' hissi yaratır.",
        "tedavi_yonetimi": "Genellikle tedavi gerektirmez. Tetikleyicilerden (kafein, stres, alkol) kaçınma.",
        "klinik_not": "Sık PAC'ler ileride gelişecek Atriyal Fibrilasyonun öncüsü olabilir."
    },
    "PVC": {
        "tani": "Prematür Ventriküler Kompleks (PVC)",
        "alternatif_tahminler": "Prematür Atriyal Kompleks (aberan iletimli)",
        "bulgular": "Öncesinde P dalgası olmayan, erken gelen, geniş ve deforme QRS kompleksi (>120ms). Tam kompansatuvar duraklama.",
        "olasi_sonuclar": "Genelde benign. Ancak sık, polimorfik veya 'R-on-T' fenomeni varsa malign aritmi (VT/VF) riski.",
        "tedavi_yonetimi": "Asemptomatikse izlem. Semptomatikse beta blokerler veya kalsiyum kanal blokerleri.",
        "klinik_not": "Yapısal kalp hastalığı (örn. düşük EF) varlığında sık PVC'ler yüksek risk göstergesidir."
    },

    # ─── İLETİM BOZUKLUKLARI (AV BLOKLAR VE DAL BLOKLARI) ───────────────────
    "AV_BLOCK_1": {
        "tani": "1. Derece AV Blok",
        "alternatif_tahminler": "Normal varyasyon (sporcularda)",
        "bulgular": "PR mesafesinin uzaması (>0.20 sn / 5 küçük kare). Her P dalgasını bir QRS takip eder.",
        "olasi_sonuclar": "Genellikle asemptomatiktir ve iyi huyludur.",
        "tedavi_yonetimi": "Özel bir tedavi gerektirmez, klinik izlem yeterlidir.",
        "klinik_not": "AV düğüm seviyesinde iletimin fizyolojik veya ilaca sekonder (beta bloker) yavaşlamasıdır."
    },
    "AV_BLOCK_2_MOBITZ1": {
        "tani": "2. Derece AV Blok (Mobitz Tip I / Wenckebach)",
        "alternatif_tahminler": "Mobitz Tip II AV Blok",
        "bulgular": "PR mesafesinin vuruşlar arası giderek uzaması ve nihayetinde bir P dalgasının (QRS'siz) düşmesi.",
        "olasi_sonuclar": "Genelde selimdir, senkop nadirdir.",
        "tedavi_yonetimi": "Asemptomatikse takip. Bradikardi ve semptom varsa ilaçların kesilmesi, nadiren atropin.",
        "klinik_not": "İletim engeli genellikle AV düğüm seviyesindedir ve kalıcı kalp pili nadiren gerekir."
    },
    "AV_BLOCK_2_MOBITZ2": {
        "tani": "2. Derece AV Blok (Mobitz Tip II)",
        "alternatif_tahminler": "Mobitz Tip I (Wenckebach), Tam AV Blok",
        "bulgular": "PR mesafesi sabittir (uzamış veya normal). Rastgele veya düzenli aralıklarla P dalgaları iletilemez (QRS düşer).",
        "olasi_sonuclar": "Senkop riski yüksektir. Hızla 3. derece (Tam) AV bloğa ilerleyebilir.",
        "tedavi_yonetimi": "Kalıcı kalp pili (Pacemaker) endikasyonu vardır.",
        "klinik_not": "İletim engeli His-Purkinje sistemi seviyesindedir (AV düğüm altı), tehlikelidir."
    },
    "AV_BLOCK_3": {
        "tani": "3. Derece (Tam) AV Blok",
        "alternatif_tahminler": "İleri Derece AV Blok, AV tam disosiyasyon (VT ile)",
        "bulgular": "P dalgaları ve QRS kompleksleri arasında tamamen bağımsız ritimler. P hızı QRS hızından büyüktür.",
        "olasi_sonuclar": "Kalp debisinde ciddi düşüş, Adams-Stokes atakları (senkop), kalp yetmezliği, ani ölüm.",
        "tedavi_yonetimi": "Acil geçici pacemaker, sonrasında kalıcı pacemaker implantasyonu.",
        "klinik_not": "Kaçış ritmi dar QRS ise düğüm seviyesinde, geniş QRS ise ventrikül seviyesindedir (daha riskli)."
    },
    "LBBB": {
        "tani": "Sol Dal Bloğu (LBBB)",
        "alternatif_tahminler": "Ventriküler Paced Ritim, İskemi/İnfarktüs",
        "bulgular": "Geniş QRS (>120ms). V1'de derin S dalgası (QS veya rS). V5, V6, I, aVL'de geniş, çentikli veya kalın R dalgası.",
        "olasi_sonuclar": "Kalp yetmezliği (sekonder dissenkroni), altta yatan iskemik veya yapısal hastalık işareti.",
        "tedavi_yonetimi": "Altta yatan hastalığın (Hipertansiyon, KAH) tedavisi. Gerekirse KRT (Kardiyak Resenkronizasyon Tedavisi).",
        "klinik_not": "Yeni gelişmiş LBBB, aksine ispat edilene kadar akut miyokard infarktüsü (STEMI eşdeğeri) kabul edilebilir."
    },
    "RBBB": {
        "tani": "Sağ Dal Bloğu (RBBB)",
        "alternatif_tahminler": "Brugada Sendromu, Sağ Ventrikül Hipertrofisi",
        "bulgular": "Geniş QRS (>120ms). V1-V2'de 'tavşan kulağı' (rsR' veya rSR') görünümü. I, aVL, V5-V6'da geniş, yavaş inen S dalgası.",
        "olasi_sonuclar": "Sağ kalpli yüklenme (Korpulmonale, Pulmoner Emboli) işareti olabilir; ancak sağlıklı bireylerde de görülebilir.",
        "tedavi_yonetimi": "Semptom veya yapısal kalp hastalığı yoksa izlem.",
        "klinik_not": "Tek başına kardiyovasküler mortaliteyi artırmaz, klinik tabloyla korelasyon şarttır."
    },
    "HEMIBLOCK": {
        "tani": "Fasiküler Blok (Hemiblok)",
        "alternatif_tahminler": "Sol Ventrikül Hipertrofisi, İnfarktüs İzleri",
        "bulgular": "Sol anterior hemiblokta (LAFB) belirgin sol aks sapması; sol posterior hemiblokta (LPFB) belirgin sağ aks sapması. Normal QRS süresi.",
        "olasi_sonuclar": "RBBB ile birleşirse (Bifasiküler blok) tam AV bloğa ilerleme riski taşır.",
        "tedavi_yonetimi": "İzlem. Bifasiküler blok + semptom varsa pacemaker değerlendirmesi.",
        "klinik_not": "Aks sapmasının diğer nedenleri dışlandıktan sonra tanı konulur."
    },
    "WPW": {
        "tani": "Wolff-Parkinson-White (WPW) Sendromu / Preeksitasyon",
        "alternatif_tahminler": "Lown-Ganong-Levine Sendromu, Sol Ventrikül Hipertrofisi",
        "bulgular": "Kısa PR mesafesi (<120ms), QRS kompleksinin başlangıcında eğim (Delta dalgası), QRS genişlemesi.",
        "olasi_sonuclar": "Atriyoventriküler Reentran Taşikardi (AVRT) atakları, WPW + AF durumunda VF'ye dönüşüm ve ani ölüm.",
        "tedavi_yonetimi": "Asemptomatikse izlem. Taşikardi öyküsü varsa aksesuar yolun kateter ablasyonu.",
        "klinik_not": "WPW zemininde gelişen Atriyal Fibrilasyonda AV düğümü bloke eden ilaçlar (beta bloker, digoksin, verapamil) kontrendikedir!"
    },

    # ─── İSKEMİ VE İNFARKTÜS (KORONER HASTALIKLAR) ──────────────────────────
    "STEMI": {
        "tani": "ST-Elevasyonlu Miyokard İnfarktüsü (STEMI)",
        "alternatif_tahminler": "Akut Perikardit, Sol Dal Bloğu, Benign Erken Repolarizasyon",
        "bulgular": "Birbirini izleyen en az 2 derivasyonda belirgin ST segment yükselmesi. Karşıt derivasyonlarda resiprokal ST çökmesi.",
        "olasi_sonuclar": "Geri dönüşümsüz miyokard nekrozu, kardiyojenik şok, kapak rüptürü, malign aritmi.",
        "tedavi_yonetimi": "Sıfırıncı dakika: Acil Koroner Anjiyografi (Primer PKG) veya Trombolitik tedavi. Antiplatelet ve antikoagülan yüklemesi.",
        "klinik_not": "Kritik Acil! Resiprokal değişiklikler tanıyı doğrular ve lokalizasyonu netleştirir."
    },
    "NSTEMI": {
        "tani": "ST-Elevasyonsuz Miyokard İnfarktüsü / İskemi (NSTEMI)",
        "alternatif_tahminler": "Stabil Olmayan Anjina (USAP), Miyokardit, Digoksin Etkisi",
        "bulgular": "ST segmentinde yatay veya aşağı eğimli çökme (depresyon). Dinamik T dalgası inversiyonu. ST yükselmesi YOK.",
        "olasi_sonuclar": "Akut koroner sendrom tablosu, kardiyak hasarın ilerlemesi.",
        "tedavi_yonetimi": "Agresif anti-iskemik tedavi, dual antiplatelet, düşük molekül ağırlıklı heparin. Erken invaziv strateji (24-72 saat).",
        "klinik_not": "USAP ile NSTEMI ayrımı kardiyak biyobelirteç (Troponin I/T) yüksekliği ile yapılır."
    },
    "ISCHEMIA": {
        "tani": "Miyokard İskemisi",
        "alternatif_tahminler": "Elektrolit bozukluğu, Ventriküler hipertrofi suşu",
        "bulgular": "Simetrik, derin, ok ucu şeklinde negatif T dalgaları veya geçici ST çökmeleri.",
        "olasi_sonuclar": "Egzersizle tetiklenen anjina, ileride infarktüs gelişimi.",
        "tedavi_yonetimi": "Kardiyoloji poliklinik kontrolü, efor testi, tıbbi tedavi optimizasyonu.",
        "klinik_not": "Wellens Sendromu (V2-V3'te bifazik/derin T) LAD (sol ön inen arter) proksimal darlığının spesifik işaretidir."
    },
    "OLD_MI": {
        "tani": "Geçirilmiş (Eski) Miyokard İnfarktüsü Bulguları",
        "alternatif_tahminler": "Sol Ventrikül Hipertrofisi pseudo-infarktüs paterni, WPW",
        "bulgular": "Patolojik Q dalgaları (genişliği >40ms ve derinliği R dalgasının %25'inden fazla). ST segmenti genelde izoelektrik hatta inmiştir.",
        "olasi_sonuclar": "Bölgesel duvar hareket bozukluğu, düşük ejeksiyon fraksiyonu (kalp yetmezliği).",
        "tedavi_yonetimi": "Kalp yetmezliği protokolüne göre kılavuz destekli medikal tedavi (GDMT).",
        "klinik_not": "ST elevasyonu haftalar sonra hala devam ediyorsa sol ventrikül anevrizması düşünülmelidir."
    },

    # ─── HİPERTROFİ VE KALBE YÜKLENME DURUMLARI ─────────────────────────────
    "LVH": {
        "tani": "Sol Ventrikül Hipertrofisi (LVH)",
        "alternatif_tahminler": "Sol Dal Bloğu, Genç İnce Yapılı Hasta Varyasyonu",
        "bulgular": "Artmış QRS voltajı (Sokolow-Lyon: V1'deki S + V5/V6'daki R > 35 mm). V5-V6'da strain paterni (ST çökmesi, asimetrik T negatifliği).",
        "olasi_sonuclar": "Diyastolik disfonksiyon, kalp yetmezliği, artmış kardiyovasküler olay riski.",
        "tedavi_yonetimi": "Ekokardiyografi ile doğrulama, agresif kan basıncı kontrolü, RAAS blokerleri.",
        "klinik_not": "Kronik basınç yüklenmesinin (Örn: Hipertansiyon, Aort Darlığı) EKG'deki aynasıdır."
    },
    "RVH": {
        "tani": "Sağ Ventrikül Hipertrofisi (RVH)",
        "alternatif_tahminler": "Sağ Dal Bloğu, Posterior MI",
        "bulgular": "Sağ aks sapması. V1'de dominant R dalgası (R > S). V5-V6'da derin S dalgası. Sağ prekordiyal strain paterni.",
        "olasi_sonuclar": "Sağ kalp yetmezliği, Korpulmonale.",
        "tedavi_yonetimi": "Pulmoner hipertansiyon veya kapak patolojilerinin tedavisi.",
        "klinik_not": "KOAH, Pulmoner Emboli veya mitral darlığı gibi akciğer/sağ kalp yüklenmesi nedenleri araştırılmalıdır."
    },
    "ATRIAL_ENLARGEMENT": {
        "tani": "Atriyal Genişleme (Büyüme) Bulguları",
        "alternatif_tahminler": "Normal Varyasyon, P mitrale/P pulmonale",
        "bulgular": "Sağ Atriyal (P pulmonale): D2'de sivri, uzun P dalgası (>2.5mm). Sol Atriyal (P mitrale): D2'de çentikli, geniş P dalgası (>120ms), V1'de derin negatif terminal komponent.",
        "olasi_sonuclar": "Atriyal fibrilasyon gelişme riskinde belirgin artış.",
        "tedavi_yonetimi": "Kapak hastalıkları (Örn: Mitral darlığı) veya akciğer hastalıklarının tespiti ve tedavisi.",
        "klinik_not": "Kardiyak atriyumların hacim veya basınç yüklenmesine sekonder gelişir."
    },
    "AXIS_DEVIATION": {
        "tani": "Elektriksel Eksen (Aks) Anormalliği",
        "alternatif_tahminler": "Fasiküler Bloklar, Ventrikül Hipertrofileri, Normal Varyant",
        "bulgular": "I ve aVF derivasyonlarındaki QRS polaritelerine göre Sol Aks Sapması (-30° ila -90°) veya Sağ Aks Sapması (+90° ila +180°).",
        "olasi_sonuclar": "Tek başına patolojik değildir, altta yatan hastalığın ipucudur.",
        "tedavi_yonetimi": "Aks sapmasına neden olan primer hastalığın teşhisi.",
        "klinik_not": "İzole sol aks sapması sıklıkla sol anterior hemiblok (LAFB) ile ilişkilidir."
    },

    # ─── REPOLARİZASYON BOZUKLUKLARI, QT VE KANALOPATİLER ──────────────────
    "LONG_QT": {
        "tani": "Uzun QT Sendromu (LQTS)",
        "alternatif_tahminler": "İlaç Etkisi (Makrolidler, Antipsikotikler), Elektrolit Bozukluğu",
        "bulgular": "Düzeltilmiş QT aralığının (QTc) erkeklerde >450ms, kadınlarda >460-470ms olması.",
        "olasi_sonuclar": "Torsades de Pointes (TdP) isimli ölümcül polimorfik VT atağı, senkop, ani kardiyak ölüm.",
        "tedavi_yonetimi": "Elektrolit replasmanı, QT uzatan ilaçların acilen kesilmesi, uzun vadede beta-bloker veya ICD.",
        "klinik_not": "Hesaplama için kalbin hızına göre Bazett formülü kullanılmalıdır."
    },
    "SHORT_QT": {
        "tani": "Kısa QT Sendromu",
        "alternatif_tahminler": "Hiperkalsemi, Dijital Etkisi",
        "bulgular": "QTc süresinin anormal derecede kısa olması (< 340-360 ms). Dar, sivri T dalgaları.",
        "olasi_sonuclar": "Atriyal ve ventriküler fibrilasyon (AF/VF), ani kardiyak ölüm riski.",
        "tedavi_yonetimi": "Semptomatik olgularda ICD implantasyonu.",
        "klinik_not": "Çok nadir görülen, genellikle ailesel geçişli ölümcül bir kanalopatidir."
    },
    "BRUGADA": {
        "tani": "Brugada Sendromu",
        "alternatif_tahminler": "Sağ Dal Bloğu, Akut Perikardit, Erken Repolarizasyon",
        "bulgular": "V1 ve V2 derivasyonlarında 'Coved type' (Kubbe tarzı, Tip 1) veya 'Saddle-back' (Eyer tarzı, Tip 2) ST elevasyonu ve T negatifliği.",
        "olasi_sonuclar": "Uykuda veya istirahatte gelişen polimorfik VT/VF, ani kardiyak ölüm.",
        "tedavi_yonetimi": "Kesin tedavi İmplante Edilebilir Kardiyoverter Defibrilatör (ICD) takılmasıdır.",
        "klinik_not": "Ateş, alkol ve bazı antidepresanlar aritmiyi tetikleyebilir. Sodyum kanalı (SCN5A) mutasyonu sık görülür."
    },

    # ─── METABOLİK, TOKSİK VE SİSTEMİK ETKİLER (DİĞER) ───────────────────────
    "PE": {
        "tani": "Pulmoner Emboli Şüphesi (Sağ Kalp Yüklenmesi)",
        "alternatif_tahminler": "Akut Kor Pulmonale, İnferior MI",
        "bulgular": "Sinüs taşikardisi (En sık). Klasik S1Q3T3 paterni (D1'de derin S, D3'te patolojik Q ve negatif T). V1-V4 arası T dalgası inversiyonu.",
        "olasi_sonuclar": "Akut sağ kalp yetmezliği, şok, kardiyovasküler kollaps.",
        "tedavi_yonetimi": "Acil Toraks BT Anjiyografi, sistemik antikoagülasyon, ağır tabloda trombolitik tedavi.",
        "klinik_not": "EKG pulmoner emboliyi dışlamak için yeterli değildir, D-Dimer ve görüntüleme şarttır."
    },
    "HYPERKALEMIA": {
        "tani": "Hiperkalemi (Yüksek Potasyum)",
        "alternatif_tahminler": "Erken Repolarizasyon, Hiperakut T dalgaları (MI)",
        "bulgular": "Dar tabanlı, uzun ve 'çadır/sivri' T dalgaları. İlerleyen evrede PR uzaması, P dalgası kaybı, QRS genişlemesi ve sinüs dalgası (sine wave).",
        "olasi_sonuclar": "Kalp kası paralizisi, asistoli, ventriküler fibrilasyon.",
        "tedavi_yonetimi": "Acil membran stabilizasyonu için İntravenöz Kalsiyum Glukonat. Potasyum düşürücü ajanlar (İnsülin/Glukoz, Salbutamol).",
        "klinik_not": "Böbrek yetmezliği hastalarında sık görülür, kardiyak arrestin geri döndürülebilir '4H-4T' nedenlerinden biridir."
    },
    "HYPOKALEMIA": {
        "tani": "Hipokalemi (Düşük Potasyum)",
        "alternatif_tahminler": "Hipomagnezemi, İskemi",
        "bulgular": "ST çökmesi, T dalgası düzleşmesi/inversiyonu ve belirgin 'U dalgası' çıkışı. QT(U) uzaması.",
        "olasi_sonuclar": "Aritmilere (özellikle Torsades de Pointes ve VF) yatkınlık artışı.",
        "tedavi_yonetimi": "Potasyum replasmanı (oral veya kontrollü İV).",
        "klinik_not": "Digoksin kullanan hastalarda hipokalemi, ölümcül digoksin toksisitesini tetikler."
    },
    "CALCIUM_IMBALANCE": {
        "tani": "Kalsiyum Dengesizliği (Hipo/Hiperkalsemi)",
        "alternatif_tahminler": "Uzun QT (Kalıtsal), Kısa QT",
        "bulgular": "Hipokalsemide: QT mesafesinde belirgin uzama (ST segmenti uzar, T dalgası normal). Hiperkalsemide: QT mesafesinde kısalma, ST segmenti yokluğu, bazen Osborn dalgaları.",
        "olasi_sonuclar": "Hipokalsemi aritmi riskini artırır; hiperkalsemi iletim bloklarına ve kardiak arreste yol açabilir.",
        "tedavi_yonetimi": "Kalsiyum seviyelerinin düzeltilmesi (Altta yatan tiroid/paratiroid, renal nedenin tedavisi).",
        "klinik_not": "EKG tek başına tanı koydurmaz, elektrolit paneli ile laboratuvar doğrulama şarttır."
    },
    "HYPOTHERMIA": {
        "tani": "Hipotermi Etkisi",
        "alternatif_tahminler": "Erken repolarizasyon, Brugada",
        "bulgular": "Sinüs bradikardisi, tüm aralıkların (PR, QRS, QT) uzaması. QRS sonu ile ST başlangıcında belirgin Osborn (J) dalgaları.",
        "olasi_sonuclar": "Vücut ısısı 30°C altına düştüğünde Ventriküler Fibrilasyon eşiğinde dramatik düşüş.",
        "tedavi_yonetimi": "Dikkatli, kademeli ve aktif vücut ısıtması.",
        "klinik_not": "Isıtma sırasında sert müdahaleler (kalp pili teli takmak vb.) dirençli VF'yi tetikleyebilir."
    },
    "DIGITALIS_TOXICITY": {
        "tani": "Dijital (Digoksin) Etkisi / Zehirlenmesi Şüphesi",
        "alternatif_tahminler": "Miyokard İskemisi, Sağ Ventrikül Hipertrofisi Straini",
        "bulgular": "ST segmentinde karakteristik aşağı eğimli 'ters dönmüş bıyık' veya 'Salvador Dali bıyığı' şeklinde çökme. PR uzaması, T dalga düzleşmesi.",
        "olasi_sonuclar": "Toksisite seviyesine ulaşırsa; ölümcül bradikardiler, AV bloklar, atriyal taşikardiler ve çift yönlü (bidirectional) VT.",
        "tedavi_yonetimi": "İlacın kesilmesi, potasyum ve magnezyum kontrolü, şiddetli aritmilerde 'Digoksin spesifik Fab fragmanı' (panzehir).",
        "klinik_not": "ST çökmesi zehirlenmeyi değil 'ilaç etkisini' gösterir, ancak aritmi eklenirse toksisite tanısı kesinleşir."
    }
}