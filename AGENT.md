# AGENT CONTEXT — Portfolio Optimizer Project

## Identitas Project
Kamu adalah asisten coding untuk proyek **Portfolio Optimizer**, sebuah aplikasi yang membantu orang awam mengalokasikan uang ke instrumen investasi terbaik menggunakan Genetic Algorithm yang dipercepat dengan PySpark dan CUDA.

---

## Tujuan Proyek
1. **Akademis:** Buktikan komputasi paralel (PySpark & CUDA) lebih cepat dari sekuensial untuk evaluasi portfolio, dengan hasil yang tetap sama.
2. **End User:** Bantu orang awam menjawab "Punya Rp 5 juta, taruh dimana?" dengan rekomendasi alokasi yang mudah dipahami.

---

## Stack Teknologi

| Layer | Teknologi |
|---|---|
| Data fetching | `yfinance`, `requests`, `BeautifulSoup` |
| Data processing | PySpark (SparkSession + SparkContext RDD) |
| GPU computing | CUDA C / CuPy |
| Optimizer | Genetic Algorithm (Python) |
| Backend | Flask (Python) |
| Frontend | HTML + CSS + Vanilla JS |

---

## Aturan Pengembangan

### PySpark — WAJIB gunakan 4 pendekatan ini:
```python
# 1. SparkSession SQL Query
spark.sql("SELECT ...")

# 2. RDD map
rdd.map(lambda x: ...)

# 3. RDD filter
rdd.filter(lambda x: ...)

# 4. RDD reduce
rdd.reduce(lambda a, b: ...)
```
Setiap pendekatan HARUS diukur execution time-nya dan dibandingkan.

### CUDA — WAJIB gunakan grid & thread eksplisit:
```c
int blocks  = (n + 255) / 256;
int threads = 256;
kernel<<<blocks, threads>>>(args);
```
Kernel yang wajib ada: `covarianceMatrix`, `evaluateAllPortfolios`.

### Genetic Algorithm:
- Individu = array bobot alokasi per aset (sum = 1.0)
- Fitness = Sharpe Ratio
- Populasi = 1000, Generasi = 500
- Fitness function dipercepat via CUDA

### Benchmark Runner — WAJIB ada 6 perbandingan:
```
1. Sekuensial Python    → baseline
2. PySpark SQL          → paralel CPU
3. PySpark RDD map      → paralel CPU
4. PySpark filter+reduce→ paralel CPU
5. CUDA murni           → paralel GPU
6. PySpark + CUDA       → hybrid (scalable)
```
Operasi yang dibandingkan HARUS identik (Sharpe Ratio 1000 portfolio).

---

## Aset yang Dioptimasi

```python
ASSET_UNIVERSE = {
    "fixed": [
        {"name": "Deposito",  "source": "bi_rate"},
        {"name": "SBN ORI",   "source": "djppr_api"},
    ],
    "dynamic": [
        {"name": "Saham IDX", "source": "yfinance", "index": "LQ45"},
        {"name": "Emas",      "source": "yfinance", "ticker": "ANTM.JK"},
    ]
}
```

### Validasi Data — WAJIB:
- Hanya saham dengan listing > 3 tahun
- Coverage data ≥ 95%
- Periode: 2022-01-01 s/d 2024-12-31 (post-COVID)
- Auto-reject saham dengan data tidak lengkap

---

## Struktur Folder

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
│   ├── sequential.py
│   ├── pyspark_bench.py
│   ├── cuda_bench.cu
│   └── runner.py
└── results/
    ├── benchmark.csv
    ├── optimal_weights.json
    └── charts/
```

---

## Output Format untuk End User

Selalu konversi output teknis ke bahasa awam:

| Jangan (teknis) | Gunakan (awam) |
|---|---|
| `weight: 0.40` | "Taruh Rp 2 juta di Deposito" |
| `return: 8.3%` | "Estimasi 3 tahun jadi Rp 6.4 juta" |
| `max_drawdown: 6%` | "Paling berat bisa turun Rp 300rb" |
| `500 generasi GA` | "Komputer coba 100.000 kombinasi" |
| `Sharpe Ratio` | "Seberapa worth it risikonya" |
| `volatilitas` | "Seberapa naik-turun harganya" |

---

## Constraint GA berdasarkan Profil Risiko

```python
RISK_PROFILES = {
    "aman": {
        "max_saham"   : 0.20,   # maks 20% di saham
        "min_fixed"   : 0.60,   # min 60% deposito/SBN
        "max_drawdown": 0.05,
    },
    "seimbang": {
        "max_saham"   : 0.50,
        "min_fixed"   : 0.30,
        "max_drawdown": 0.15,
    },
    "agresif": {
        "max_saham"   : 0.80,
        "min_fixed"   : 0.10,
        "max_drawdown": 0.30,
    }
}
```

---

## Ekspektasi Benchmark

```
Sekuensial Python     : ~45 detik  (1x)
PySpark SQL           : ~8 detik   (5.6x)
PySpark RDD map       : ~5 detik   (8.7x)
PySpark filter+reduce : ~4.8 detik (9.4x)
CUDA murni            : ~0.3 detik (150x)
PySpark + CUDA        : ~1.5 detik (30x)
```

Angka ini adalah estimasi — hasil aktual dicatat di `results/benchmark.csv`.

---

## Catatan Penting

1. **Data TIDAK boleh hardcoded** — semua fetch dinamis dari API/yfinance
2. **CUDA + PySpark gabungan** bukan yang tercepat, tapi paling scalable — jelaskan ini di video
3. **Walk-forward validation** — validasi GA di beberapa periode berbeda
4. **Video 5 menit** — buka dengan hook orang awam, bukan jargon teknis
5. **Survivorship bias** — jangan masukkan saham yang baru IPO < 3 tahun

---

## Checklist Sebelum Submit

- [ ] PySpark: SQL query, map, reduce, filter semua ada
- [ ] Execution time semua metode tercatat
- [ ] CUDA kernel dengan grid & thread eksplisit
- [ ] GA konvergen (grafik Sharpe per generasi naik)
- [ ] Data divalidasi (coverage ≥ 95%)
- [ ] UI bisa dipakai tanpa penjelasan teknis
- [ ] Video 5 menit, 720p, suara jelas / ada subtitle
- [ ] Link video di-paste ke assignment
