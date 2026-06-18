# Product Requirements Document (PRD)
## Portfolio Optimizer — Paralel Computing Project
**Version:** 1.0 | **Date:** June 2026

---

## 1. Overview

### Problem Statement
Orang awam bingung mengalokasikan uang ke instrumen investasi yang tepat (deposito, SBN, saham, emas). Keputusan investasi sering dibuat tanpa analisis kuantitatif karena toolnya terlalu teknis.

### Solution
Aplikasi optimasi portfolio multi-aset menggunakan Genetic Algorithm yang dipercepat dengan komputasi paralel (PySpark & CUDA), dengan output yang dapat dimengerti orang awam.

### Academic Goal
Membuktikan secara empiris bahwa komputasi paralel lebih cepat dari sekuensial untuk evaluasi portfolio masif, dengan hasil yang tetap sama.

---

## 2. Target User

| User | Kebutuhan |
|---|---|
| Mahasiswa (akademik) | Lihat perbandingan sekuensial vs paralel |
| Orang awam (end user) | "Uang 5 juta saya taruh dimana?" |
| Dosen penilai | Bukti teknis GA + PySpark + CUDA terintegrasi |

---

## 3. Scoring Criteria

| Komponen | Poin |
|---|---|
| PySpark (query, map, reduce, filter) | Base score |
| Perbandingan execution time | Wajib |
| CUDA dengan grid & thread | +20 bonus |
| Video 5 menit jelas & subtitle | Wajib |
| **Total maksimal** | **170 poin** |

---

## 4. Data

### Sumber Data (Dynamic, bukan hardcoded)

- **Saham IDX** → yfinance (suffix `.JK`)
- **Emas** → yfinance (`ANTM.JK` / `GC=F`)
- **Deposito** → BI Rate API (real-time)
- **SBN / ORI** → DJPPR API (real-time)

### Universe Aset

- **Saham:** LQ45 / IDX30 (auto-fetch, ~20-30 saham)
- **Fixed:** Deposito, SBN ORI
- **Komoditas:** Emas

### Validasi Data

- Filter saham listing < 5 tahun
- Filter coverage data < 95%
- Periode: 2022–2024 (post-COVID, 3 tahun)
- Exclude periode anomali ekstrem

---

## 5. Arsitektur Sistem

```
USER INPUT
(modal, profil risiko, durasi)
        │
        ▼
DATA LAYER
(yfinance + BI API + DJPPR + Cache)
        │
        ▼
PYSPARK ENGINE
(ETL + SQL + map + reduce + filter)
        │
        ▼
BENCHMARK RUNNER  ← inti akademis
├── Sekuensial Python
├── PySpark CPU
├── CUDA GPU
└── PySpark + CUDA (gabungan)
        │
        ▼
GA OPTIMIZER
(populasi, seleksi, crossover, mutasi)
fitness function → pakai CUDA
        │
        ▼
BACKEND FLASK
(format hasil → bahasa awam)
        │
        ▼
FRONTEND WEB UI
(form input + hasil + grafik)
```

---

## 6. Komponen Teknis

### 6.1 PySpark (Wajib)

| API | Fungsi |
|---|---|
| SparkSession SQL | Query return & statistik historis per aset |
| RDD map | Hitung Sharpe Ratio tiap kombinasi portfolio |
| RDD filter | Buang portfolio tidak memenuhi constraint |
| RDD reduce | Cari portfolio terbaik dari seluruh populasi |

### 6.2 CUDA (Bonus +20)

| Kernel | Fungsi |
|---|---|
| `covarianceMatrix` | Hitung korelasi antar aset (grid 2D) |
| `evaluateAllPortfolios` | Evaluasi 100K portfolio serentak |
| `monteCarloSimulation` | Simulasi return masa depan |

Grid & thread wajib eksplisit:
```c
int blocks  = (n_portfolios + 255) / 256;
int threads = 256;
kernel<<<blocks, threads>>>(args);
```

### 6.3 Genetic Algorithm

| Komponen | Detail |
|---|---|
| Individu | Array bobot alokasi per aset |
| Populasi | 1000 individu |
| Generasi | 500 |
| Fitness | Sharpe Ratio (via CUDA) |
| Crossover | Blend weights dua individu |
| Mutasi | Random shift bobot kecil |
| Constraint | Min invest, max per aset, profil risiko |

### 6.4 PySpark + CUDA (Gabungan, Bonus)

```
PySpark partisi data
    ↓
Tiap partition → CuPy evaluate di GPU
    ↓
Collect & reduce hasil
```

> Catatan: Bukan yang tercepat, tapi paling scalable untuk data sangat besar.

---

## 7. Benchmark (Inti Akademis)

### Operasi yang Dibandingkan
> Evaluasi Sharpe Ratio untuk **1000 kombinasi portfolio** — operasi identik, cara berbeda.

| # | Metode | Ekspektasi Waktu | Speedup |
|---|---|---|---|
| 1 | Sekuensial Python (for loop) | ~45 detik | 1x (baseline) |
| 2 | PySpark SQL Query | ~8 detik | ~5.6x |
| 3 | PySpark RDD map | ~5 detik | ~8.7x |
| 4 | PySpark RDD filter + reduce | ~4.8 detik | ~9.4x |
| 5 | CUDA murni | ~0.3 detik | ~150x |
| 6 | PySpark + CUDA (CuPy) | ~1.5 detik | ~30x |

**Hasil semua metode: SAMA ✅**

---

## 8. User Experience

### Input (Orang Awam)
- Modal investasi (Rp)
- Profil risiko: Aman / Seimbang / Agresif
- Jangka waktu: <1 tahun / 1–3 tahun / >3 tahun

### Output (Bahasa Awam)

| Teknis | Bahasa Awam |
|---|---|
| Bobot 0.40 | "Taruh Rp 2 juta di Deposito" |
| Return 8.3% | "Estimasi 3 tahun jadi Rp 6.4 juta" |
| Max drawdown 6% | "Paling berat bisa turun Rp 300rb" |
| GA 500 generasi | "Komputer coba 100.000 kombinasi" |
| Sharpe Ratio | "Seberapa worth it risikonya" |
| Volatilitas | "Seberapa naik-turun harganya" |

---

## 9. Struktur Folder

```
portfolio-optimizer/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── backend/
│   ├── app.py              # Flask API
│   ├── orchestrator.py     # koordinasi semua layer
│   └── formatter.py        # angka → bahasa awam
├── data/
│   ├── fetcher.py          # yfinance + BI + DJPPR
│   ├── validator.py        # filter data tidak valid
│   └── cache.py
├── pyspark/
│   ├── session.py          # SparkSession SQL
│   └── context.py          # RDD map/reduce/filter
├── cuda/
│   ├── covariance.cu
│   ├── montecarlo.cu
│   └── evaluate.cu
├── ga/
│   ├── optimizer.py
│   ├── fitness.py
│   └── constraints.py
├── benchmark/
│   ├── sequential.py       # Python for loop
│   ├── pyspark_bench.py    # map/reduce/filter
│   ├── cuda_bench.cu       # GPU kernel
│   └── runner.py           # jalankan & bandingkan
└── results/
    ├── benchmark.csv
    ├── optimal_weights.json
    └── charts/
```

---

## 10. Video (5 Menit)

| Waktu | Konten |
|---|---|
| 0:00–0:40 | Hook: "Punya 5 juta, taruh dimana?" |
| 0:40–1:30 | Penjelasan paralel: kenapa perlu? |
| 1:30–2:30 | Demo benchmark: sekuensial vs PySpark vs CUDA |
| 2:30–3:30 | Demo GA optimizer berjalan |
| 3:30–4:30 | Output: rekomendasi alokasi + grafik |
| 4:30–5:00 | Kesimpulan: hasil sama, waktu beda drastis |

**Teknis video:**
- Durasi: tepat 5 menit
- Resolusi: minimal 720p
- Suara: jelas / ada subtitle
- Upload: YouTube atau Google Drive

---

## 11. Metrik Keberhasilan

| Metrik | Target |
|---|---|
| Semua metode hasil sama | ✅ wajib |
| Speedup PySpark vs serial | minimal 3x |
| Speedup CUDA vs serial | minimal 50x |
| GA konvergen | Sharpe Ratio meningkat tiap generasi |
| Data valid | coverage ≥ 95%, periode 2022–2024 |
| UI bisa dipakai orang awam | input < 1 menit |

---

## 12. Timeline

| Minggu | Target |
|---|---|
| Minggu 1 | Data fetcher + validator |
| Minggu 2 | PySpark pipeline + benchmark sekuensial |
| Minggu 3 | CUDA kernel + benchmark |
| Minggu 4 | GA optimizer + integrasi |
| Minggu 5 | Frontend UI + Flask backend |
| Minggu 6 | Video recording + submit |
