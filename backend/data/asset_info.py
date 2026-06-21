# Database of detailed descriptions and fallback metrics for assets
# This ensures instant loading and robust fallbacks if external yfinance calls fail or rate-limit.

ASSET_DATABASE = {
    "DEPOSITO": {
        "official_name": "Deposito Berjangka Rupiah",
        "ticker": "DEPOSITO",
        "asset_type": "Pendapatan Tetap (Sangat Aman)",
        "description": "Tabungan berjangka dengan bunga tetap yang dijamin penuh oleh Lembaga Penjamin Simpanan (LPS) hingga Rp 2 Miliar per nasabah. Aset ini bebas dari risiko pasar, menjadikannya jangkar pengaman portofolio Anda.",
        "metrics": {
            "Suku Bunga": "6.25% per tahun (BI-Rate)",
            "Tingkat Risiko": "Sangat Rendah",
            "Likuiditas": "Rendah (Penalti pencairan sebelum jatuh tempo)",
            "Penjamin": "LPS (Lembaga Penjamin Simpanan)"
        }
    },
    "OBLIGASI SBN": {
        "official_name": "Surat Berharga Negara (SBN Ritel)",
        "ticker": "OBLIGASI SBN",
        "asset_type": "Pendapatan Tetap (Aman & Dijamin Negara)",
        "description": "Instrumen utang yang diterbitkan oleh Pemerintah Republik Indonesia untuk warga negara ritel (seperti ORI, SR, SBR, ST). Pembayaran pokok dan kupon dijamin 100% oleh Undang-Undang APBN, memberikan return menarik dengan keamanan tertinggi.",
        "metrics": {
            "Imbal Hasil (Yield)": "6.75% per tahun",
            "Tingkat Risiko": "Rendah (Risiko gagal bayar nol)",
            "Likuiditas": "Sedang (Ada opsi Early Redemption atau Pasar Sekunder)",
            "Jaminan Pokok": "Pemerintah Republik Indonesia (100%)"
        }
    },
    "EMAS (ANTM)": {
        "official_name": "Emas Batangan ANTM (Logam Mulia)",
        "ticker": "EMAS",
        "asset_type": "Komoditas (Hedge Inflasi)",
        "description": "Emas fisik batangan bersertifikasi LBMA yang diproduksi oleh PT Aneka Tambang (Antam) Tbk. Emas bertindak sebagai pelindung nilai portofolio terbaik terhadap inflasi, pelemahan mata uang Rupiah, dan ketidakpastian geopolitik global.",
        "metrics": {
            "Yield/Bunga": "0% (Keuntungan dari capital gain)",
            "Tingkat Risiko": "Moderat (Harga emas berfluktuasi harian)",
            "Likuiditas": "Sangat Tinggi (Mudah dijual kembali / buyback)",
            "Penyimpanan": "Fisik / Safe Deposit Box / Rekening Emas digital"
        }
    },
    
    # 25 Stocks fallbacks
    "BBCA": {
        "official_name": "PT Bank Central Asia Tbk",
        "ticker": "BBCA",
        "asset_type": "Saham Perbankan (LQ45)",
        "description": "Bank swasta terbesar di Indonesia yang memiliki fokus kuat pada perbankan transaksi dan penyaluran kredit secara prudent. Terkenal dengan efisiensi tinggi, likuiditas kuat, dan pertumbuhan dividen stabil.",
        "metrics": {
            "P/E Ratio": "24.5x",
            "Market Cap": "~Rp 1.150 Triliun",
            "Dividend Yield": "1.8%",
            "Industri": "Perbankan (Jasa Keuangan)"
        }
    },
    "BBRI": {
        "official_name": "PT Bank Rakyat Indonesia (Persero) Tbk",
        "ticker": "BBRI",
        "asset_type": "Saham Perbankan (LQ45)",
        "description": "Bank BUMN terbesar dengan spesialisasi kredit mikro, kecil, dan menengah (UMKM) terbesar di Indonesia. Memiliki jaringan cabang fisik terluas serta penyalur program bantuan pemerintah terbesar.",
        "metrics": {
            "P/E Ratio": "13.2x",
            "Market Cap": "~Rp 740 Triliun",
            "Dividend Yield": "4.5%",
            "Industri": "Perbankan (BUMN)"
        }
    },
    "BMRI": {
        "official_name": "PT Bank Mandiri (Persero) Tbk",
        "ticker": "BMRI",
        "asset_type": "Saham Perbankan (LQ45)",
        "description": "Bank BUMN terbesar dari sisi total aset, melayani segmen korporasi hingga ritel dengan platform digital Kopra dan Livin'. Unggul dalam bisnis pinjaman korporasi dan transaksi ekspor-impor.",
        "metrics": {
            "P/E Ratio": "11.8x",
            "Market Cap": "~Rp 570 Triliun",
            "Dividend Yield": "4.2%",
            "Industri": "Perbankan (BUMN)"
        }
    },
    "TLKM": {
        "official_name": "PT Telkom Indonesia (Persero) Tbk",
        "ticker": "TLKM",
        "asset_type": "Saham Telekomunikasi (LQ45)",
        "description": "Perusahaan telekomunikasi terbesar di Indonesia yang menguasai pangsa pasar seluler (Telkomsel) dan internet kabel (IndiHome). Infrastruktur serat optik dan menara BTS terluas di seluruh kepulauan Indonesia.",
        "metrics": {
            "P/E Ratio": "14.5x",
            "Market Cap": "~Rp 350 Triliun",
            "Dividend Yield": "5.1%",
            "Industri": "Telekomunikasi (Infrastruktur)"
        }
    },
    "ASII": {
        "official_name": "PT Astra International Tbk",
        "ticker": "ASII",
        "asset_type": "Saham Konglomerasi (LQ45)",
        "description": "Konglomerat multinasional Indonesia dengan bisnis utama otomotif (pemegang pangsa pasar mobil roda 4 terbesar via Toyota, Daihatsu, Isuzu), alat berat tambang (United Tractors), agribisnis, dan keuangan.",
        "metrics": {
            "P/E Ratio": "7.8x",
            "Market Cap": "~Rp 210 Triliun",
            "Dividend Yield": "7.2%",
            "Industri": "Konglomerasi Otomotif & Alat Berat"
        }
    },
    "UNVR": {
        "official_name": "PT Unilever Indonesia Tbk",
        "ticker": "UNVR",
        "asset_type": "Saham Barang Konsumsi (LQ45)",
        "description": "Produsen barang konsumen cepat saji (FMCG) terkemuka dengan portofolio produk pembersih rumah, kosmetik, sabun, sampo, kecap, dan es krim. Merek-mereknya sangat lekat dengan konsumsi harian masyarakat.",
        "metrics": {
            "P/E Ratio": "22.1x",
            "Market Cap": "~Rp 110 Triliun",
            "Dividend Yield": "5.5%",
            "Industri": "Consumer Non-Durables (FMCG)"
        }
    },
    "ADRO": {
        "official_name": "PT Adaro Energy Indonesia Tbk",
        "ticker": "ADRO",
        "asset_type": "Saham Energi & Tambang (LQ45)",
        "description": "Salah satu produsen batu bara termal terbesar dan paling efisien di Indonesia. Perusahaan ini sedang gencar bertransformasi ke bisnis energi hijau (PLTA/PLTS) dan hilirisasi mineral (aluminium smelter).",
        "metrics": {
            "P/E Ratio": "4.2x",
            "Market Cap": "~Rp 90 Triliun",
            "Dividend Yield": "11.2%",
            "Industri": "Pertambangan Batu Bara & Energi"
        }
    },
    "PGAS": {
        "official_name": "PT Perusahaan Gas Negara Tbk",
        "ticker": "PGAS",
        "asset_type": "Saham Energi & Utilitas (LQ45)",
        "description": "Sub-holding gas bumi di bawah Pertamina yang mengoperasikan infrastruktur pipa gas dan distribusi gas bumi ke sektor industri, pembangkit listrik, komersial, dan rumah tangga nasional.",
        "metrics": {
            "P/E Ratio": "7.5x",
            "Market Cap": "~Rp 35 Triliun",
            "Dividend Yield": "8.5%",
            "Industri": "Utilitas Gas Alam & Distribusi"
        }
    },
    "PTBA": {
        "official_name": "PT Bukit Asam Tbk",
        "ticker": "PTBA",
        "asset_type": "Saham Energi & Tambang (LQ45)",
        "description": "BUMN anggota holding pertambangan MIND ID yang mengelola tambang batu bara nasional. Terkenal memiliki biaya produksi rendah serta konsistensi membagikan dividen payout ratio sangat tinggi.",
        "metrics": {
            "P/E Ratio": "5.1x",
            "Market Cap": "~Rp 32 Triliun",
            "Dividend Yield": "15.4%",
            "Industri": "Pertambangan Batu Bara (BUMN)"
        }
    },
    "INDF": {
        "official_name": "PT Indofood Sukses Makmur Tbk",
        "ticker": "INDF",
        "asset_type": "Saham Barang Konsumsi (LQ45)",
        "description": "Perusahaan solusi pangan total dengan operasional terintegrasi dari agribisnis perkebunan, produk konsumen bermerek, bogasari tepung terigu, hingga logistik distribusi ritel.",
        "metrics": {
            "P/E Ratio": "6.8x",
            "Market Cap": "~Rp 58 Triliun",
            "Dividend Yield": "4.1%",
            "Industri": "Pengolahan Makanan & Distribusi"
        }
    },
    "ICBP": {
        "official_name": "PT Indofood CBP Sukses Makmur Tbk",
        "ticker": "ICBP",
        "asset_type": "Saham Barang Konsumsi (LQ45)",
        "description": "Anak usaha Indofood yang memproduksi mi instan terpopuler di dunia (Indomie) serta makanan ringan, penyedap rasa, susu (Indomilk), minuman jus, dan nutrisi khusus.",
        "metrics": {
            "P/E Ratio": "13.5x",
            "Market Cap": "~Rp 130 Triliun",
            "Dividend Yield": "2.8%",
            "Industri": "Makanan Kemasan & FMCG"
        }
    },
    "KLBF": {
        "official_name": "PT Kalbe Farma Tbk",
        "ticker": "KLBF",
        "asset_type": "Saham Kesehatan & Farmasi (LQ45)",
        "description": "Perusahaan farmasi terbesar di Asia Tenggara dengan spesialisasi obat resep, obat bebas (OTC), produk nutrisi premium, serta jaringan distribusi logistik dan klinik kesehatan nasional.",
        "metrics": {
            "P/E Ratio": "23.4x",
            "Market Cap": "~Rp 72 Triliun",
            "Dividend Yield": "2.4%",
            "Industri": "Farmasi & Pelayanan Kesehatan"
        }
    },
    "CPIN": {
        "official_name": "PT Charoen Pokphand Indonesia Tbk",
        "ticker": "CPIN",
        "asset_type": "Saham Pangan & Agribisnis (LQ45)",
        "description": "Produsen pakan ternak, anak ayam usia sehari (DOC), dan makanan olahan (Fiesta Chicken Nugget) terbesar di Indonesia. Memiliki posisi pangsa pasar dominan di industri unggas domestik.",
        "metrics": {
            "P/E Ratio": "28.5x",
            "Market Cap": "~Rp 80 Triliun",
            "Dividend Yield": "1.9%",
            "Industri": "Pakan Ternak & Pengolahan Unggas"
        }
    },
    "JSMR": {
        "official_name": "PT Jasa Marga (Persero) Tbk",
        "ticker": "JSMR",
        "asset_type": "Saham Infrastruktur (LQ45)",
        "description": "BUMN pengembang dan operator jalan tol pertama dan terbesar di Indonesia. Menguasai mayoritas konsesi jalan tol di seluruh Indonesia dengan volume transaksi harian terbesar nasional.",
        "metrics": {
            "P/E Ratio": "9.2x",
            "Market Cap": "~Rp 36 Triliun",
            "Dividend Yield": "3.2%",
            "Industri": "Konstruksi & Operator Jalan Tol"
        }
    },
    "BRPT": {
        "official_name": "PT Barito Pacific Tbk",
        "ticker": "BRPT",
        "asset_type": "Saham Holding & Kimia (LQ45)",
        "description": "Perusahaan induk milik konglomerat Prajogo Pangestu dengan portofolio utama di sektor petrokimia (via Chandra Asri) dan pembangkit listrik panas bumi terbesar Indonesia (Star Energy Geothermal).",
        "metrics": {
            "P/E Ratio": "85.2x",
            "Market Cap": "~Rp 92 Triliun",
            "Dividend Yield": "0.2%",
            "Industri": "Holding Investasi, Kimia, & Geotermal"
        }
    },
    "AKRA": {
        "official_name": "PT AKR Corporindo Tbk",
        "ticker": "AKRA",
        "asset_type": "Saham Logistik & Distribusi (LQ45)",
        "description": "Penyedia jasa logistik, perdagangan, dan distribusi BBM swasta serta bahan kimia dasar terintegrasi. Pengembang kawasan industri pelabuhan raksasa JIIPE Gresik.",
        "metrics": {
            "P/E Ratio": "11.2x",
            "Market Cap": "~Rp 30 Triliun",
            "Dividend Yield": "5.4%",
            "Industri": "Distribusi Energi & Logistik Industri"
        }
    },
    "EXCL": {
        "official_name": "PT XL Axiata Tbk",
        "ticker": "EXCL",
        "asset_type": "Saham Telekomunikasi (LQ45)",
        "description": "Penyedia layanan seluler swasta terkemuka di Indonesia dengan jangkauan internet cepat 4G/5G nasional. Aktif berinvestasi pada fiberisasi jaringan dan konvergensi layanan data internet.",
        "metrics": {
            "P/E Ratio": "18.5x",
            "Market Cap": "~Rp 28 Triliun",
            "Dividend Yield": "2.5%",
            "Industri": "Layanan Telekomunikasi Seluler"
        }
    },
    "INCO": {
        "official_name": "PT Vale Indonesia Tbk",
        "ticker": "INCO",
        "asset_type": "Saham Pertambangan Logam (LQ45)",
        "description": "Salah satu produsen nikel matte terbesar di dunia dengan komitmen ramah lingkungan tinggi (peleburan bertenaga PLTA). Memiliki cadangan nikel laterit melimpah di Sorowako, Sulawesi Selatan.",
        "metrics": {
            "P/E Ratio": "10.5x",
            "Market Cap": "~Rp 38 Triliun",
            "Dividend Yield": "3.8%",
            "Industri": "Pertambangan Bijih Nikel"
        }
    },
    "TPIA": {
        "official_name": "PT Chandra Asri Pacific Tbk",
        "ticker": "TPIA",
        "asset_type": "Saham Kimia & Infrastruktur (LQ45)",
        "description": "Produsen petrokimia terintegrasi terbesar di Indonesia yang memproduksi monomer, olefin, dan polimer plastik. Kini melebarkan sayap ke sektor energi dan logistik pelabuhan.",
        "metrics": {
            "P/E Ratio": "N/A (Rugi bersih)",
            "Market Cap": "~Rp 780 Triliun",
            "Dividend Yield": "0.0%",
            "Industri": "Petrokimia & Infrastruktur Industri"
        }
    },
    "SMGR": {
        "official_name": "PT Semen Indonesia (Persero) Tbk",
        "ticker": "SMGR",
        "asset_type": "Saham Bahan Bangunan (LQ45)",
        "description": "Perusahaan induk BUMN semen terbesar di Indonesia dengan merek terkemuka Semen Gresik, Semen Padang, Semen Tonasa, dan Dynamix. Memiliki kapasitas produksi terluas di Asia Tenggara.",
        "metrics": {
            "P/E Ratio": "12.4x",
            "Market Cap": "~Rp 33 Triliun",
            "Dividend Yield": "4.8%",
            "Industri": "Pengolahan Semen & Material Bangunan"
        }
    },
    "ANJT": {
        "official_name": "PT Austindo Nusantara Jaya Tbk",
        "ticker": "ANJT",
        "asset_type": "Saham Pertanian & CPO",
        "description": "Perusahaan agribisnis yang berfokus pada perkebunan kelapa sawit lestari (CPO) tersertifikasi ISPO/RSPO, penanaman sagu berkelanjutan di Papua, dan pengolahan sayuran.",
        "metrics": {
            "P/E Ratio": "15.2x",
            "Market Cap": "~Rp 2.5 Triliun",
            "Dividend Yield": "3.5%",
            "Industri": "Perkebunan Kelapa Sawit & Agribisnis"
        }
    },
    "ADHI": {
        "official_name": "PT Adhi Karya (Persero) Tbk",
        "ticker": "ADHI",
        "asset_type": "Saham Konstruksi & Infrastruktur",
        "description": "Perusahaan BUMN jasa konstruksi terintegrasi yang mengerjakan berbagai proyek infrastruktur strategis seperti kereta layang LRT Jabodebek, bendungan, bandara, pelabuhan, dan gedung bertingkat.",
        "metrics": {
            "P/E Ratio": "19.5x",
            "Market Cap": "~Rp 2.8 Triliun",
            "Dividend Yield": "0.0%",
            "Industri": "Jasa Konstruksi & Rekayasa Industri"
        }
    },
    "PWON": {
        "official_name": "PT Pakuwon Jati Tbk",
        "ticker": "PWON",
        "asset_type": "Saham Properti & Real Estate",
        "description": "Pengembang properti terkemuka dengan model bisnis pendapatan berulang (recurring income) terkuat di Indonesia dari portofolio pusat perbelanjaan superblok (Tunjungan Plaza, Gandaria City, Kokas).",
        "metrics": {
            "P/E Ratio": "10.8x",
            "Market Cap": "~Rp 20 Triliun",
            "Dividend Yield": "1.5%",
            "Industri": "Pengembangan Properti & Mal Retail"
        }
    },
    "CTRA": {
        "official_name": "PT Ciputra Development Tbk",
        "ticker": "CTRA",
        "asset_type": "Saham Properti & Real Estate",
        "description": "Pelopor pengembangan perumahan skala kota terintegrasi dengan diversifikasi geografis terluas di Indonesia (lebih dari 30 kota besar), lengkap dengan mal, rumah sakit, dan lapangan golf.",
        "metrics": {
            "P/E Ratio": "11.5x",
            "Market Cap": "~Rp 22 Triliun",
            "Dividend Yield": "1.2%",
            "Industri": "Real Estate & Urban Development"
        }
    },
    "MEDC": {
        "official_name": "PT Medco Energi Internasional Tbk",
        "ticker": "MEDC",
        "asset_type": "Saham Eksplorasi Minyak & Gas (LQ45)",
        "description": "Perusahaan eksplorasi dan produsen migas swasta terbesar di Indonesia yang memiliki portofolio tambang tembaga dan emas skala dunia (AMMAN), ketenagalistrikan swasta, serta proyek panas bumi.",
        "metrics": {
            "P/E Ratio": "5.8x",
            "Market Cap": "~Rp 30 Triliun",
            "Dividend Yield": "3.5%",
            "Industri": "Eksplorasi Minyak, Gas, & Pertambangan"
        }
    }
}
