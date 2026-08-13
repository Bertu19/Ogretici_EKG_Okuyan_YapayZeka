Cardiology EKG Analysis System 🩺
Klinik Karar Destek ve Tıp Eğitimi Modülü

Geliştiren: Bertu Deler

- Proje Hakkında
Cardiology EKG Analiz Sistemi, 12 derivasyonlu EKG (Elektrokardiyografi) görsellerini veya PDF raporlarını yapay zeka ve kapsamlı bir tıbbi karar destek veritabanı ile analiz ederek öğrencilere ve sağlık profesyonellerine hızlı, yapılandırılmış ve akademik düzeyde geri bildirim sunan modern bir web uygulamasıdır.

Frontend tarafında React, TypeScript, Vite ve Tailwind CSS kullanılarak modern bir arayüz tasarlanmış; backend tarafında ise Python FastAPI ile güçlendirilmiş, genişletilmiş bir tıbbi tanı ve tedavi motoru entegre edilmiştir.

- Kullanılan Teknolojiler
Frontend (Arayüz)
React 18 & TypeScript: Bileşen tabanlı modern ve güvenli mimari.

Vite: Hızlı geliştirme ve optimize edilmiş üretim (production) derlemesi.

Tailwind CSS: Koyu tema (Dark Mode) odaklı, modern tıp arayüzü tasarımı.

Lucide / SVG Icons: Klinik göstergeler ve arayüz ikonografisi.

Backend & Yapay Zeka Motoru
Python & FastAPI: Yüksek performanslı, asenkron API altyapısı.

Joblib / Scikit-Learn: Model entegrasyonu ve veri işleme altyapısı.

Kapsamlı Tıbbi Veritabanı: Ritim bozuklukları, iskemik hastalıklar, iletim blokları, elektrolit bozuklukları ve kanalopatileri içeren detaylı kural tabanlı ve yapay zeka destekli karar motoru.

- Kapsamlı Tıbbi Tanı Yelpazesi
Sistem, literatürdeki en kritik EKG bulgularını ve hastalık gruplarını eksiksiz olarak tanıyıp raporlayabilir:

Ritim ve İleti Bozuklukları:

Sinüs Taşikardisi / Bradikardisi / Aritmisi

Atriyal Fibrilasyon (AF) & Atriyal Flutter

Supraventriküler Taşikardi (SVT) & Atriyal Taşikardi

Ventriküler Taşikardi (VT) & Ventriküler Fibrilasyon (VF)

Prematür Atriyal (PAC) ve Ventriküler (PVC) Kompleksler

1., 2. Derece (Mobitz I / II) ve 3. Derece (Tam) AV Bloklar

Sağ / Sol Dal Blokları (RBBB / LBBB) & Fasiküler Hemibloklar

WPW (Wolff-Parkinson-White) / Preeksitasyon Sendromu

Kalp Krizi ve Koroner Hastalıklar:

ST-Elevasyonlu Miyokard İnfarktüsü (STEMI)

ST-Elevasyonsuz Miyokard İnfarktüsü / İskemi (NSTEMI / USAP)

Miyokard İskemisi & Geçirilmiş MI İzleri (Patolojik Q Dalgaları)

Hipertrofi ve Yüklenme Bulguları:

Sol ve Sağ Ventrikül Hipertrofisi (LVH / RVH)

Atriyal Genişleme Bulguları (P Mitrale / P Pulmonale)

Elektriksel Eksen Anormallikleri

Repolarizasyon, QT ve Kanalopatiler:

Uzun QT (LQTS) & Kısa QT Sendromları

Brugada Sendromu (Tip 1 ve Tip 2)

Metabolik ve Sistemik Durumlar:

Pulmoner Emboli Şüphesi (S1Q3T3 Paterni)

Hiperkalemi & Hipokalemi Bulguları

Kalsiyum Dengesizlikleri & Hipotermi Etkileri

Dijital (Digoksin) Etkisi ve Zehirlenmesi

- Raporlama Özellikleri
Her analiz sonucunda sistem kullanıcıya şu yapılandırılmış detayları sunar:

Birincil Tanı: Net ve akademik tanı başlığı.

Model Güven Oranı: Yüzdesel doğruluk/güven skoru.

Ayırıcı Tanılar (Alternatifler): Olası diğer klinik durumlar ve olasılık yüzdeleri.

Bulgular & Klinik Değerlendirme: Maddeler halinde EKG okuma bulguları.

Olası Sonuçlar & Riskler: Hastanın karşılaşabileceği klinik riskler.

Tedavi & Yönetim Yaklaşımı: Acil ve rutin tıbbi yönetim adımları.

Öğrenci / Klinik Notu: Pratik ipuçları ve artefakt uyarıları.

- Kurulum ve Yerel Çalıştırma
Projeyi kendi bilgisayarınızda çalıştırmak için sırasıyla şu adımları izleyebilirsiniz:

1. Projeyi Klonlayın
Bash
git clone https://github.com/Bertu19/Ogretici_EKG_Okuyan_YapayZeka.git
cd EKG_Egitim_Projesi
2. Backend Kurulumu
Bash
cd backend_ai
pip install -r requirements.txt
uvicorn main:app --reload
3. Frontend Kurulumu (Yeni bir terminal penceresinde)
Bash
cd frontend_app
npm install
npm run build
npm run dev
- Canlı Yayın (Deployment)
Proje, Render platformu üzerinde tam entegre (Python Backend + Static React Frontend) bir servis olarak canlıya alınmıştır. Otomatik build ve dağıtım işlemleri kök dizindeki render.yaml dosyası üzerinden yönetilmektedir.

⚠ Yasal Uyarı & Sorumluluk Reddi
Eğitim Amaçlıdır: Bu sistem yalnızca tıp eğitimi, akademik çalışmalar ve klinik karar destek modülü olarak geliştirilmiştir. Üretilen çıktılar kesinlikle tek başına klinik tanı koymak veya acil müdaheleyi yönlendirmek amacıyla kullanılamaz. Tıbbi durumlarda her zaman sertifikalı bir kardiyoloğa danışılmalıdır.

© 2026 — Developed with ❤️ by BertuDeler
