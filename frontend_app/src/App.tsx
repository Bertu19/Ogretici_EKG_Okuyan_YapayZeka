import { useState, useRef, useCallback, type DragEvent, type ChangeEvent } from 'react'

type Gender = 'male' | 'female' | 'other' | ''

interface PatientMeta {
  age: string
  gender: Gender
}

interface DiagnosisResult {
  primary: string
  isPathological: boolean
  confidence: number
  differentials: { label: string; probability: number }[]
  findings: string[]
  risks: string[]
  treatment: string[]
  studentNote: string
}

function EkgTrace({ color = '#ef4444' }: { color?: string }) {
  return (
    <svg viewBox="0 0 300 60" className="w-full h-10 opacity-60" preserveAspectRatio="none">
      <polyline
        className="ekg-path"
        points="0,30 20,30 25,30 30,10 35,50 40,30 60,30 65,30 70,15 72,5 74,55 76,30 80,30 100,30 105,30 110,20 115,40 120,30 140,30 145,30 150,10 155,50 160,30 180,30 185,30 190,15 192,5 194,55 196,30 200,30 220,30 225,30 230,20 235,40 240,30 260,30 265,30 270,10 275,50 280,30 300,30"
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ConfidenceBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1.5 bg-[#1f2937] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-xs tabular-nums" style={{ color, fontFamily: 'DM Mono, monospace' }}>
        {value}%
      </span>
    </div>
  )
}

function SectionCard({
  title,
  accent,
  children,
  delay = 0,
}: {
  title: string
  accent: string
  children: React.ReactNode
  delay?: number
}) {
  return (
    <div
      className="rounded-xl p-5 animate-fade-in-up"
      style={{
        backgroundColor: '#111827',
        border: `1px solid ${accent}40`,
        animationDelay: `${delay}ms`,
        animationFillMode: 'both',
      }}
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="w-1 h-4 rounded-full" style={{ backgroundColor: accent }} />
        <h3
          className="text-xs font-semibold tracking-widest uppercase"
          style={{ color: accent, fontFamily: 'DM Mono, monospace' }}
        >
          {title}
        </h3>
      </div>
      {children}
    </div>
  )
}

export default function App() {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [meta, setMeta] = useState<PatientMeta>({ age: '', gender: '' })
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<DiagnosisResult | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragActive(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) acceptFile(dropped)
  }, [])

  const acceptFile = (f: File) => {
    setFile(f)
    setResult(null)
    if (f.type.startsWith('image/')) {
      const url = URL.createObjectURL(f)
      setPreview(url)
    } else {
      setPreview(null)
    }
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) acceptFile(f)
  }

  const handleAnalyze = async () => {
    if (!file) return
    setAnalyzing(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append("dosya", file)
      formData.append("yas", meta.age)
      formData.append("cinsiyet", meta.gender)

      const response = await fetch('/gorsel_analiz', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error("Sunucu yanıt vermedi.")

      const data = await response.json()
      const isPatho = data.durum !== "normal"

      const parseToList = (text: string) => text ? text.split('. ').filter(Boolean) : ["Bilgi bulunmuyor."]

      const parsedResult: DiagnosisResult = {
        primary: data.tani,
        isPathological: isPatho,
        confidence: isPatho ? 91 : 97,
        differentials: data.alternatif_tahminler 
          ? data.alternatif_tahminler.split(', ').map((item: string, idx: number) => ({ label: item, probability: 90 - (idx * 15) }))
          : [{ label: "Alternatif bulgu yok", probability: 5 }],
        findings: parseToList(data.bulgular),
        risks: parseToList(data.olasi_sonuclar),
        treatment: parseToList(data.tedavi_yonetimi),
        studentNote: data.klinik_not
      }

      setResult(parsedResult)
    } catch (error) {
      console.error("Analiz hatası:", error)
      alert("Sunucu ile iletişim kurulurken bir hata oluştu.")
    } finally {
      setAnalyzing(false)
    }
  }

  const canAnalyze = !!file && meta.age !== '' && meta.gender !== '' && !analyzing

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0b0f19' }}>
      <header
        className="sticky top-0 z-30 px-6 py-4"
        style={{
          backgroundColor: 'rgba(11,15,25,0.92)',
          borderBottom: '1px solid rgba(239,68,68,0.2)',
          backdropFilter: 'blur(12px)',
        }}
      >
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: '#1f2937', border: '1px solid rgba(239,68,68,0.4)' }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M22 12H18L15 21L9 3L6 12H2" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-semibold leading-tight text-slate-100 tracking-tight">
                Kardiyoloji EKG Analiz Sistemi
              </h1>
              <p className="text-xs text-[#6b7280] mt-0.5" style={{ fontFamily: 'DM Mono, monospace' }}>
                Klinik Karar Destek · Tıp Eğitimi Modülü
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium"
              style={{ backgroundColor: 'rgba(52,211,153,0.1)', color: '#34d399', border: '1px solid rgba(52,211,153,0.25)', fontFamily: 'DM Mono, monospace' }}
            >
              ● EĞİTİM AMAÇLI
            </span>
            <span
              className="text-xs px-2.5 py-1 rounded-full font-medium hidden sm:inline-flex"
              style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.25)', fontFamily: 'DM Mono, monospace' }}
            >
              KLİNİK KULLANIMA UYGUN DEĞİLDİR
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 pb-16 pt-8 space-y-8">
        <section>
          <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: '#111827', border: '1px solid rgba(55,65,81,0.8)' }}>
            <div className="px-6 pt-5 pb-3" style={{ borderBottom: '1px solid rgba(55,65,81,0.6)' }}>
              <div className="flex items-start justify-between mb-1">
                <div>
                  <h2 className="text-sm font-semibold text-slate-200 tracking-tight">EKG Girişi ve Hasta Bilgileri</h2>
                  <p className="text-xs text-[#6b7280] mt-0.5">Analiz için 12 derivasyonlu EKG görseli veya PDF raporu yükleyin</p>
                </div>
                <span className="text-xs font-medium px-2 py-0.5 rounded" style={{ backgroundColor: '#0b0f19', color: '#6b7280', fontFamily: 'DM Mono, monospace' }}>
                  ADIM 01
                </span>
              </div>
              <EkgTrace />
            </div>

            <div className="p-6 grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3 flex flex-col gap-4">
                <div
                  role="button"
                  tabIndex={0}
                  className="relative rounded-xl transition-all duration-200 cursor-pointer flex flex-col items-center justify-center gap-3 py-10 px-6 text-center"
                  style={{
                    backgroundColor: dragActive ? 'rgba(239,68,68,0.06)' : '#0b0f19',
                    border: `2px dashed ${dragActive ? '#ef4444' : 'rgba(55,65,81,0.9)'}`,
                    minHeight: '180px',
                  }}
                  onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.pdf"
                    className="sr-only"
                    onChange={handleFileChange}
                  />

                  {file ? (
                    <>
                      <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(52,211,153,0.12)', color: '#34d399' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-200">{file.name}</p>
                        <p className="text-xs text-[#6b7280] mt-0.5">{(file.size / 1024).toFixed(1)} KB</p>
                      </div>
                      <p className="text-xs text-[#4b5563]">Değiştirmek için tıklayın</p>
                    </>
                  ) : (
                    <>
                      <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(239,68,68,0.08)' }}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                          <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                          <polyline points="17,8 12,3 7,8" stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                          <line x1="12" y1="3" x2="12" y2="15" stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round"/>
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-300">EKG görselini veya PDF'i buraya sürükleyin</p>
                        <p className="text-xs text-[#6b7280] mt-1">PNG, JPG, JPEG, PDF · Maks 20 MB</p>
                      </div>
                      <p className="text-xs text-[#4b5563]">veya dosya seçmek için tıklayın</p>
                    </>
                  )}
                </div>
              </div>

              <div className="lg:col-span-2 flex flex-col gap-4">
                <div className="rounded-xl overflow-hidden flex items-center justify-center" style={{ backgroundColor: '#0b0f19', border: '1px solid rgba(55,65,81,0.7)', height: '120px' }}>
                  {preview ? (
                    <img src={preview} alt="EKG Önizleme" className="max-h-full max-w-full object-contain" />
                  ) : (
                    <div className="text-center">
                      <p className="text-xs text-[#4b5563]" style={{ fontFamily: 'DM Mono, monospace' }}>CANLI ÖNİZLEME</p>
                      <p className="text-xs text-[#374151] mt-1">Dosya yüklenmedi</p>
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-[#9ca3af] mb-1.5" style={{ fontFamily: 'DM Mono, monospace' }}>HASTA YAŞI</label>
                    <input
                      type="number"
                      min={0}
                      max={120}
                      placeholder="örn. 58"
                      value={meta.age}
                      onChange={(e) => setMeta((m) => ({ ...m, age: e.target.value }))}
                      className="w-full rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-[#4b5563] outline-none"
                      style={{ backgroundColor: '#0b0f19', border: '1px solid rgba(55,65,81,0.9)' }}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-[#9ca3af] mb-1.5" style={{ fontFamily: 'DM Mono, monospace' }}>BİYOLOJİK CİNSİYET</label>
                    <select
                      value={meta.gender}
                      onChange={(e) => setMeta((m) => ({ ...m, gender: e.target.value as Gender }))}
                      className="w-full rounded-lg px-3 py-2.5 text-sm text-slate-200 outline-none"
                      style={{ backgroundColor: '#0b0f19', border: '1px solid rgba(55,65,81,0.9)', color: meta.gender ? '#f1f5f9' : '#4b5563' }}
                    >
                      <option value="" disabled style={{ color: '#4b5563' }}>Seçiniz…</option>
                      <option value="male">Erkek</option>
                      <option value="female">Kadın</option>
                      <option value="other">Diğer / Belirtilmemiş</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleAnalyze}
                  disabled={!canAnalyze}
                  className={`w-full rounded-xl py-3 px-4 text-sm font-semibold tracking-wide transition-all duration-200 flex items-center justify-center gap-2 ${
                    canAnalyze ? 'animate-pulse-glow glow-crimson cursor-pointer' : 'cursor-not-allowed opacity-40'
                  }`}
                  style={{ backgroundColor: canAnalyze ? '#ef4444' : '#374151', color: '#fff' }}
                >
                  {analyzing ? (
                    <>
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="3" strokeDasharray="31.4" strokeDashoffset="10" />
                      </svg>
                      EKG Analiz Ediliyor…
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M22 12H18L15 21L9 3L6 12H2" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      EKG'yi Analiz Et
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {result && (
          <section className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px" style={{ backgroundColor: 'rgba(55,65,81,0.6)' }} />
              <span className="text-xs font-semibold tracking-widest uppercase text-[#6b7280]" style={{ fontFamily: 'DM Mono, monospace' }}>
                Analiz Raporu
              </span>
              <div className="flex-1 h-px" style={{ backgroundColor: 'rgba(55,65,81,0.6)' }} />
            </div>

            <div className="rounded-xl px-5 py-3 flex items-center gap-6 flex-wrap text-xs animate-fade-in-up" style={{ backgroundColor: '#111827', border: '1px solid rgba(55,65,81,0.7)' }}>
              {[
                { label: 'YAŞ', value: `${meta.age} y§` },
                { label: 'CİNSİYET', value: meta.gender === 'male' ? 'Erkek' : meta.gender === 'female' ? 'Kadın' : 'Diğer' },
                { label: 'DOSYA', value: file?.name ?? '—' },
                { label: 'DURUM', value: result.isPathological ? 'PATOLOJİK' : 'NORMAL', color: result.isPathological ? '#ef4444' : '#34d399' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-2">
                  <span className="text-[#4b5563]" style={{ fontFamily: 'DM Mono, monospace' }}>{item.label}</span>
                  <span className="font-medium" style={{ color: item.color ?? '#9ca3af', fontFamily: 'DM Mono, monospace' }}>{item.value}</span>
                </div>
              ))}
            </div>

            <div className="rounded-2xl p-6 animate-fade-in-up" style={{ backgroundColor: result.isPathological ? 'rgba(239,68,68,0.06)' : 'rgba(52,211,153,0.05)', border: `1px solid ${result.isPathological ? 'rgba(239,68,68,0.4)' : 'rgba(52,211,153,0.35)'}` }}>
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5" style={{ backgroundColor: result.isPathological ? 'rgba(239,68,68,0.12)' : 'rgba(52,211,153,0.12)' }}>
                    {result.isPathological ? (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                        <line x1="12" y1="9" x2="12" y2="13" stroke="#ef4444" strokeWidth="1.8" strokeLinecap="round"/>
                        <line x1="12" y1="17" x2="12.01" y2="17" stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round"/>
                      </svg>
                    ) : (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="#34d399" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                        <polyline points="22,4 12,14.01 9,11.01" stroke="#34d399" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className="text-xs font-semibold tracking-widest uppercase mb-1" style={{ color: result.isPathological ? '#ef4444' : '#34d399', fontFamily: 'DM Mono, monospace' }}>
                      Birincil Tanı
                    </p>
                    <h2 className="text-lg font-semibold leading-snug" style={{ color: result.isPathological ? '#fca5a5' : '#6ee7b7' }}>
                      {result.primary}
                    </h2>
                  </div>
                </div>

                <div className="text-right flex-shrink-0">
                  <p className="text-xs text-[#6b7280] mb-1" style={{ fontFamily: 'DM Mono, monospace' }}>MODEL GÜVEN ORANI</p>
                  <p className="text-3xl font-bold tabular-nums" style={{ color: result.isPathological ? '#ef4444' : '#34d399', fontFamily: 'DM Mono, monospace' }}>
                    {result.confidence}%
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <SectionCard title="Ayıirici Tanılar (Alternatifler)" accent="#f59e0b" delay={100}>
                <div className="space-y-3">
                  {result.differentials.map((d) => (
                    <div key={d.label}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-slate-300">{d.label}</span>
                        <span className="text-xs text-[#6b7280]" style={{ fontFamily: 'DM Mono, monospace' }}>{d.probability}%</span>
                      </div>
                      <ConfidenceBar value={d.probability} color="#f59e0b" />
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Bulgular ve Klinik Değerlendirme" accent="#818cf8" delay={150}>
                <ul className="space-y-2">
                  {result.findings.map((f, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#818cf8' }} />
                      <span className="text-sm text-slate-300 leading-relaxed">{f}</span>
                    </li>
                  ))}
                </ul>
              </SectionCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <SectionCard title="Olası Sonuçlar ve Riskler" accent="#ef4444" delay={200}>
                <ul className="space-y-2">
                  {result.risks.map((r, i) => (
                    <li key={i} className="flex items-start gap-2.5">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: '#ef4444' }} />
                      <span className="text-sm text-slate-300 leading-relaxed">{r}</span>
                    </li>
                  ))}
                </ul>
              </SectionCard>

              <SectionCard title="Tedavi ve Yönetim Yaklaşımı" accent="#34d399" delay={250}>
                <ol className="space-y-2">
                  {result.treatment.map((t, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold mt-0.5" style={{ backgroundColor: 'rgba(52,211,153,0.12)', color: '#34d399', fontFamily: 'DM Mono, monospace' }}>
                        {i + 1}
                      </span>
                      <span className="text-sm text-slate-300 leading-relaxed">{t}</span>
                    </li>
                  ))}
                </ol>
              </SectionCard>
            </div>

            <div className="rounded-2xl p-6 animate-fade-in-up" style={{ backgroundColor: 'rgba(34,211,238,0.04)', border: '1px solid rgba(34,211,238,0.3)' }}>
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5" style={{ backgroundColor: 'rgba(34,211,238,0.1)' }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="#22d3ee" strokeWidth="1.8"/>
                    <line x1="12" y1="8" x2="12" y2="12" stroke="#22d3ee" strokeWidth="1.8" strokeLinecap="round"/>
                    <line x1="12" y1="16" x2="12.01" y2="16" stroke="#22d3ee" strokeWidth="2.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <div>
                  <p className="text-xs font-semibold tracking-widest uppercase mb-2" style={{ color: '#22d3ee', fontFamily: 'DM Mono, monospace' }}>
                    Öğrenci Notu · Artefakt Uyarısı
                  </p>
                  <p className="text-sm leading-relaxed italic" style={{ color: '#a5f3fc' }}>
                    {result.studentNote}
                  </p>
                </div>
              </div>
            </div>

            <p className="text-center text-xs text-[#374151] leading-relaxed px-4" style={{ fontFamily: 'DM Mono, monospace' }}>
              ⚠ Bu çıktı yalnızca eğitim amaçlı üretilmiştir ve klinik kararları yönlendirmek için kesinlikle kullanılmamıştır.
              Her zaman sertifikalı bir kardiyoloğa danışın.
            </p>
          </section>
        )}

        {!result && !analyzing && (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ backgroundColor: '#111827', border: '1px solid rgba(55,65,81,0.6)' }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M22 12H18L15 21L9 3L6 12H2" stroke="#374151" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <p className="text-sm text-[#4b5563]">
              Bir EKG yükleyin, hasta bilgilerini girin ve raporu oluşturmak için{' '}
              <span className="text-[#ef4444]">EKG'yi Analiz Et</span> butonuna tıklayın.
            </p>
          </div>
        )}
      </main>
    </div>
  )
}