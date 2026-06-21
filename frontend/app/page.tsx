"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Dna, Banknote, ShieldCheck, Scale, TrendingUp, CalendarDays,
  Cpu, BarChart3, CheckCircle, RefreshCw, Info, Gauge,
  TrendingDown, Zap, ArrowRight, ChevronDown, ChevronUp,
  X, XCircle, Trophy, Activity, AlertTriangle, RotateCcw,
  FlaskConical, Layers, SlidersHorizontal, Network, BadgeCheck,
} from "lucide-react";
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title,
} from "chart.js";
import { Doughnut, Bar } from "react-chartjs-2";

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:5000";

// ── Types ─────────────────────────────────────────────────────────
interface ToastItem { id: number; message: string; type: "success" | "error" | "info" }
interface AllocationItem { asset: string; percentage: string; nominal: string; description: string }
interface PortfolioData {
  capital: string;
  duration_years: number;
  allocation: AllocationItem[];
  return:     { percentage: string; description: string; summary: string };
  volatility: { label: string; percentage: string; description: string };
  drawdown:   { percentage: string; nominal: string; description: string };
  sharpe:     { value: string; label: string; description: string };
  ga_insight: { insight: string };
}
interface BenchmarkRow {
  Method: string;
  "Time (s)": number | null;
  Speedup: number | null;
  "Best Sharpe": number | null;
}
type RiskColor = "emerald" | "amber" | "rose";

// ── Constants ─────────────────────────────────────────────────────
const CAPITAL_PRESETS = [
  { label: "Rp 1 Jt",  value: 1_000_000 },
  { label: "Rp 5 Jt",  value: 5_000_000 },
  { label: "Rp 10 Jt", value: 10_000_000 },
  { label: "Rp 25 Jt", value: 25_000_000 },
  { label: "Rp 50 Jt", value: 50_000_000 },
];

const RISK_PROFILES: {
  id: string; Icon: React.FC<{ className?: string }>;
  label: string; sub: string; desc: string; suitable: string;
  color: RiskColor; riskPos: number;
}[] = [
  {
    id: "aman", Icon: ShieldCheck, label: "Konservatif",
    sub: "Prioritas keamanan modal",
    desc: "Sebagian besar modal di deposito dan obligasi negara. Cocok untuk memulai investasi pertama.",
    suitable: "Pemula · Tidak ingin nilai turun drastis",
    color: "emerald", riskPos: 15,
  },
  {
    id: "seimbang", Icon: Scale, label: "Moderat",
    sub: "Seimbang antara return dan risiko",
    desc: "Campuran saham dan aset stabil. Potensi return lebih besar dengan fluktuasi yang terkelola.",
    suitable: "Investor yang sudah pernah berinvestasi",
    color: "amber", riskPos: 50,
  },
  {
    id: "agresif", Icon: TrendingUp, label: "Agresif",
    sub: "Maksimalkan potensi return",
    desc: "Porsi saham dominan untuk potensi keuntungan tertinggi. Siap menghadapi volatilitas tinggi.",
    suitable: "Investor berpengalaman · Toleransi risiko tinggi",
    color: "rose", riskPos: 83,
  },
];

const DURATION_OPTIONS = [
  { value: 1, label: "1 Tahun", sub: "Jangka pendek" },
  { value: 3, label: "3 Tahun", sub: "Menengah" },
  { value: 5, label: "5 Tahun", sub: "Jangka panjang" },
];

const ENGINE_OPTIONS = [
  { value: "numpy_vectorized", label: "CPU Vectorized", sub: "NumPy · Default" },
  { value: "cuda",             label: "GPU Parallel",   sub: "CUDA · NVIDIA only" },
  { value: "pyspark_cpu",      label: "Cluster CPU",    sub: "PySpark RDD" },
  { value: "pyspark_cuda",     label: "Hybrid",         sub: "PySpark + CUDA" },
];

const LOADING_STEPS = [
  { Icon: Activity,     text: "Mengambil data pasar terkini" },
  { Icon: CheckCircle,  text: "Memvalidasi 25 saham LQ45" },
  { Icon: Layers,       text: "Menginisialisasi 500 portofolio acak" },
  { Icon: FlaskConical, text: "Menjalankan 150 generasi Genetic Algorithm" },
  { Icon: BarChart3,    text: "Memilih alokasi portofolio optimal" },
];

const CHART_PALETTE = [
  "#38bdf8","#34d399","#fbbf24","#a78bfa","#f472b6",
  "#fb923c","#a3e635","#e879f9","#60a5fa","#c084fc",
  "#facc15","#2dd4bf","#f87171",
];

const CM: Record<RiskColor, { border: string; bg: string; text: string; dot: string }> = {
  emerald: { border: "border-emerald-500/50", bg: "bg-emerald-500/8", text: "text-emerald-400", dot: "bg-emerald-400" },
  amber:   { border: "border-amber-500/50",   bg: "bg-amber-500/8",   text: "text-amber-400",   dot: "bg-amber-400" },
  rose:    { border: "border-rose-500/50",    bg: "bg-rose-500/8",    text: "text-rose-400",    dot: "bg-rose-400" },
};

// ── Helpers ───────────────────────────────────────────────────────
const formatIDR = (n: number) =>
  new Intl.NumberFormat("id-ID", { style: "currency", currency: "IDR", minimumFractionDigits: 0 }).format(n);

// ── Sub-components ────────────────────────────────────────────────

function ToastStack({ toasts, onDismiss }: { toasts: ToastItem[]; onDismiss: (id: number) => void }) {
  return (
    <div className="fixed top-4 right-4 z-[200] flex flex-col gap-2 max-w-[320px]">
      {toasts.map((t) => (
        <div key={t.id} className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl animate-slide-in-right backdrop-blur-md
          ${t.type === "error"   ? "bg-rose-950/95 border-rose-500/40 text-rose-200" : ""}
          ${t.type === "success" ? "bg-emerald-950/95 border-emerald-500/40 text-emerald-200" : ""}
          ${t.type === "info"    ? "bg-slate-900/95 border-white/10 text-slate-200" : ""}`}
        >
          {t.type === "error"   && <XCircle     className="h-4 w-4 mt-0.5 shrink-0 text-rose-400" />}
          {t.type === "success" && <CheckCircle className="h-4 w-4 mt-0.5 shrink-0 text-emerald-400" />}
          {t.type === "info"    && <Info        className="h-4 w-4 mt-0.5 shrink-0 text-sky-400" />}
          <p className="text-sm leading-relaxed flex-1">{t.message}</p>
          <button onClick={() => onDismiss(t.id)} className="opacity-40 hover:opacity-90 transition-opacity shrink-0">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

function StepIndicator({ step }: { step: number }) {
  const steps = [{ n: 1, label: "Modal" }, { n: 2, label: "Profil" }, { n: 3, label: "Durasi" }, { n: 4, label: "Hasil" }];
  return (
    <div className="flex items-center gap-0">
      {steps.map((s, i) => (
        <React.Fragment key={s.n}>
          <div className="flex items-center gap-1.5">
            <div className={`h-6 w-6 rounded-full flex items-center justify-center text-[11px] font-black transition-all
              ${step > s.n  ? "bg-sky-500 text-white" :
                step === s.n ? "bg-sky-500/20 border border-sky-500/60 text-sky-400" :
                               "bg-white/[0.04] border border-white/[0.08] text-slate-600"}`}>
              {step > s.n ? <CheckCircle className="h-3.5 w-3.5" /> : s.n}
            </div>
            <span className={`text-xs font-semibold hidden sm:block transition-colors
              ${step === s.n ? "text-slate-200" : step > s.n ? "text-sky-400" : "text-slate-600"}`}>
              {s.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className={`flex-1 h-px mx-2 transition-colors ${step > s.n ? "bg-sky-500/40" : "bg-white/[0.06]"}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

function Label({ Icon, text }: { Icon: React.FC<{ className?: string }>; text: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-2.5">
      <Icon className="h-3 w-3 text-sky-400" />
      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{text}</span>
    </div>
  );
}

function PresetBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick}
      className={`px-3.5 py-1.5 rounded-lg text-sm font-bold border transition-all duration-150
        ${active ? "bg-sky-500/15 border-sky-500/60 text-sky-300"
                 : "bg-white/[0.03] border-white/[0.07] text-slate-400 hover:border-white/20 hover:text-slate-200"}`}>
      {label}
    </button>
  );
}

// ── Benchmark Modal ───────────────────────────────────────────────
function BenchmarkModal({
  data, onClose,
}: { data: BenchmarkRow[]; onClose: () => void }) {
  const fastest = Math.min(...data.filter((d) => d["Time (s)"] != null && !isNaN(d["Time (s)"]!)).map((d) => d["Time (s)"]!));
  const chartData = {
    labels: data.map((d) => d.Method),
    datasets: [{
      label: "Waktu (s)",
      data: data.map((d) => d["Time (s)"] ?? 0),
      backgroundColor: ["rgba(56,189,248,0.65)","rgba(52,211,153,0.65)","rgba(251,191,36,0.65)","rgba(248,113,113,0.65)","rgba(167,139,250,0.65)","rgba(251,146,60,0.65)"].slice(0, data.length),
      borderColor:     ["rgba(56,189,248,1)",   "rgba(52,211,153,1)",   "rgba(251,191,36,1)",   "rgba(248,113,113,1)",   "rgba(167,139,250,1)",   "rgba(251,146,60,1)"].slice(0, data.length),
      borderWidth: 1, borderRadius: 5,
    }],
  };
  return (
    <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-6" onClick={onClose}>
      <div className="panel rounded-2xl p-6 w-full max-w-3xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <Zap className="h-4 w-4 text-sky-400" />
            <h2 className="font-black text-base text-white">Perbandingan Kecepatan Engine</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/[0.06] text-slate-500 hover:text-slate-200 transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  {["Engine", "Waktu", "Speedup", "Sharpe"].map((h) => (
                    <th key={h} className="py-2 px-3 text-[10px] font-bold text-slate-600 uppercase tracking-widest">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((item, i) => {
                  const isBest = item["Time (s)"] === fastest;
                  return (
                    <tr key={i} className={`border-b border-white/[0.04] last:border-0 ${isBest ? "bg-emerald-500/5" : "hover:bg-white/[0.02]"}`}>
                      <td className="py-2.5 px-3 text-sm">
                        <div className="flex items-center gap-1.5">
                          {isBest && <Trophy className="h-3.5 w-3.5 text-amber-400 shrink-0" />}
                          <span className={isBest ? "text-emerald-300 font-semibold" : "text-slate-300"}>{item.Method}</span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3 text-sm font-mono text-slate-400">{item["Time (s)"] != null ? `${item["Time (s)"]!.toFixed(4)}s` : "N/A"}</td>
                      <td className="py-2.5 px-3 text-sm font-mono text-slate-400">{item.Speedup != null ? `${item.Speedup.toFixed(2)}×` : "N/A"}</td>
                      <td className="py-2.5 px-3 text-sm font-mono text-slate-400">{item["Best Sharpe"] != null ? item["Best Sharpe"].toFixed(4) : "N/A"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="h-52">
            <Bar data={chartData} options={{
              responsive: true, maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: {
                y: { beginAtZero: true, grid: { color: "rgba(255,255,255,0.04)" }, ticks: { color: "#64748b", font: { size: 11 } } },
                x: { grid: { display: false }, ticks: { color: "#64748b", font: { size: 9 } } },
              },
            }} />
          </div>
        </div>
        <p className="text-xs text-slate-600 mt-4">Semua engine menghasilkan nilai identik — perbedaan hanya waktu komputasi.</p>
      </div>
    </div>
  );
}

interface AssetDetailModalProps {
  assetName: string;
  details: {
    official_name: string;
    ticker: string;
    asset_type: string;
    description: string;
    metrics: Record<string, string>;
  } | null;
  loading: boolean;
  onClose: () => void;
}

function AssetDetailModal({ assetName, details, loading, onClose }: AssetDetailModalProps) {
  return (
    <div
      className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-6"
      onClick={onClose}
    >
      <div
        className="panel rounded-2xl p-6 w-full max-w-lg relative animate-slide-up bg-[#0b0f1a]/95 border border-white/[0.08]"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 p-1.5 rounded-lg hover:bg-white/[0.06] text-slate-500 hover:text-slate-200 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <RefreshCw className="h-8 w-8 text-sky-400 animate-spin" />
            <p className="text-xs text-slate-500 font-bold">Mengambil detail {assetName}...</p>
          </div>
        ) : details ? (
          <div className="flex flex-col gap-4">
            <div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 border border-sky-500/25 text-sky-400">
                {details.asset_type}
              </span>
              <h2 className="text-xl font-black text-slate-100 mt-2 leading-tight">
                {details.official_name}
              </h2>
              <p className="text-xs text-slate-500 font-mono font-bold mt-1">
                Ticker: {details.ticker}
              </p>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed bg-white/[0.015] border border-white/[0.04] p-3.5 rounded-xl">
              {details.description}
            </p>

            <div>
              <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-2.5">
                Metrik & Informasi Kunci
              </p>
              <div className="grid grid-cols-2 gap-2.5">
                {Object.entries(details.metrics).map(([key, val]) => (
                  <div
                    key={key}
                    className="p-2.5 rounded-xl bg-white/[0.025] border border-white/[0.05] flex flex-col gap-0.5"
                  >
                    <span className="text-[9px] text-slate-500 uppercase tracking-wider font-bold">
                      {key}
                    </span>
                    <span className="text-sm font-black text-slate-200 tabular-nums">
                      {val}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center animate-fade-in">
            <p className="text-sm text-slate-400">Gagal memuat detail aset.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────
export default function Home() {
  const [step,          setStep]          = useState<number>(1);
  const [capital,       setCapital]       = useState<number>(5_000_000);
  const [capitalInput,  setCapitalInput]  = useState<string>("");
  const [riskProfile,   setRiskProfile]   = useState<string>("aman");
  const [duration,      setDuration]      = useState<number>(3);
  const [engineMode,    setEngineMode]    = useState<string>("numpy_vectorized");
  const [showEngine,    setShowEngine]    = useState<boolean>(false);

  const [loading,       setLoading]       = useState<boolean>(false);
  const [loadingStep,   setLoadingStep]   = useState<number>(0);
  const [benchmarking,  setBenchmarking]  = useState<boolean>(false);
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkRow[] | null>(null);
  const [showBenchmark, setShowBenchmark] = useState<boolean>(false);
  const [toasts,        setToasts]        = useState<ToastItem[]>([]);

  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
  const [assetDetails,  setAssetDetails]  = useState<any | null>(null);
  const [loadingAsset,  setLoadingAsset]  = useState<boolean>(false);

  const handleCapitalTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9]/g, "");
    setCapitalInput(raw);
    const num = parseInt(raw, 10);
    if (!isNaN(num) && num >= 100_000) setCapital(num);
  };
  const handleCapitalTextBlur = () => setCapitalInput("");

  const addToast = useCallback((message: string, type: ToastItem["type"] = "info") => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 5000);
  }, []);

  const dismissToast = useCallback((id: number) => setToasts((p) => p.filter((t) => t.id !== id)), []);

  useEffect(() => {
    if (!loading) return;
    setLoadingStep(0);
    const iv = setInterval(() => setLoadingStep((p) => (p < LOADING_STEPS.length - 1 ? p + 1 : p)), 1800);
    return () => clearInterval(iv);
  }, [loading]);

  const handleOptimize = async () => {
    setLoading(true);
    setPortfolioData(null);
    try {
      const res = await fetch(`${API_BASE}/api/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ capital, profile: riskProfile, duration, mode: engineMode }),
      });
      const result = await res.json();
      if (result.status === "success") {
        setPortfolioData(result.data as PortfolioData);
        setStep(4);
        addToast("Portofolio optimal ditemukan.", "success");
      } else {
        addToast("Optimasi gagal: " + result.message, "error");
      }
    } catch {
      addToast("Tidak bisa terhubung ke server (port 5000).", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleBenchmark = async () => {
    setBenchmarking(true);
    try {
      const res = await fetch(`${API_BASE}/api/benchmark`, { method: "POST" });
      const result = await res.json();
      if (result.status === "success") {
        setBenchmarkData(result.data as BenchmarkRow[]);
        setShowBenchmark(true);
        addToast("Benchmark selesai.", "success");
      } else {
        addToast("Benchmark gagal: " + result.message, "error");
      }
    } catch {
      addToast("Benchmark tidak bisa dijalankan.", "error");
    } finally {
      setBenchmarking(false);
    }
  };

  const handleAssetClick = async (assetName: string) => {
    setSelectedAsset(assetName);
    setAssetDetails(null);
    setLoadingAsset(true);
    try {
      const res = await fetch(`${API_BASE}/api/asset/${encodeURIComponent(assetName)}`);
      const result = await res.json();
      if (result.status === "success") {
        setAssetDetails(result.data);
      } else {
        addToast("Gagal mengambil detail aset.", "error");
      }
    } catch (e) {
      addToast("Tidak bisa menghubungi server untuk detail aset.", "error");
    } finally {
      setLoadingAsset(false);
    }
  };

  const sortedAllocation = portfolioData
    ? [...portfolioData.allocation].sort((a, b) => parseFloat(b.percentage) - parseFloat(a.percentage))
    : [];

  const allocationChart = portfolioData ? {
    labels: sortedAllocation.map((a) => a.asset),
    datasets: [{
      data: sortedAllocation.map((a) => parseFloat(a.percentage)),
      backgroundColor: sortedAllocation.map((_, i) => CHART_PALETTE[i % CHART_PALETTE.length]),
      borderWidth: 2,
      borderColor: "#0b0f1a",
      hoverOffset: 6,
    }],
  } : null;

  const activeRisk = RISK_PROFILES.find((r) => r.id === riskProfile)!;
  const riskMeterPos = (() => {
    if (!portfolioData) return activeRisk.riskPos;
    const lbl = portfolioData.volatility.label.toLowerCase();
    if (lbl.includes("low") || lbl.includes("rendah"))    return 15;
    if (lbl.includes("medium") || lbl.includes("sedang")) return 50;
    return 83;
  })();

  // Header height constant (px) for calc
  const HEADER_H = 49;

  // ── Render ─────────────────────────────────────────────────────
  return (
    <div className="relative min-h-screen">
      <ToastStack toasts={toasts} onDismiss={dismissToast} />

      {/* Benchmark modal */}
      {showBenchmark && benchmarkData && (
        <BenchmarkModal data={benchmarkData} onClose={() => setShowBenchmark(false)} />
      )}

      {/* Asset Detail modal */}
      {selectedAsset && (
        <AssetDetailModal
          assetName={selectedAsset}
          details={assetDetails}
          loading={loadingAsset}
          onClose={() => setSelectedAsset(null)}
        />
      )}

      {/* Ambient */}
      <div className="glow-orb top-[-12%] right-[-8%]  w-[40vw] h-[40vw] bg-sky-600" />
      <div className="glow-orb bottom-[-12%] left-[-6%] w-[38vw] h-[38vw] bg-emerald-700" />

      {/* ── Header ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-[#0b0f1a]/90 backdrop-blur-xl">
        <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-sky-500/10 border border-sky-500/25 rounded-lg">
              <Dna className="h-4 w-4 text-sky-400" />
            </div>
            <span className="text-lg font-black tracking-tight">
              Opti<span className="text-sky-400">Gene</span>
            </span>
            <span className="hidden sm:flex items-center gap-1.5 text-[10px] text-slate-600 border border-white/[0.06] px-2 py-0.5 rounded-full">
              <Cpu className="h-3 w-3" /> PySpark · CUDA · Genetic Algorithm
            </span>
          </div>
          {portfolioData && (
            <button
              onClick={() => { setStep(1); setPortfolioData(null); setBenchmarkData(null); setShowBenchmark(false); }}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-200 border border-white/[0.07] px-3 py-1.5 rounded-lg transition-colors"
            >
              <RotateCcw className="h-3 w-3" /> Mulai Ulang
            </button>
          )}
        </div>
      </header>

      {/* ══════════════════════════════════════════════════════════
          RESULTS — full viewport dashboard, no outer scroll
      ══════════════════════════════════════════════════════════ */}
      {portfolioData && (
        <div
          className="max-w-[1600px] mx-auto px-6 grid grid-cols-2 gap-4 animate-slide-up"
          style={{ height: `calc(100vh - ${HEADER_H}px)`, overflow: "hidden", padding: "16px 24px" }}
        >
          {/* ─── LEFT COLUMN ─────────────────────────────────── */}
          <div className="flex flex-col gap-3 h-full overflow-hidden">

            {/* Stats — 2-col: return+sharpe | profit highlight */}
            {(() => {
              const returnPct  = parseFloat(portfolioData.return.percentage) / 100;
              const projected  = capital * Math.pow(1 + returnPct, duration);
              const profit     = projected - capital;
              const growthPct  = ((projected / capital - 1) * 100).toFixed(1);
              return (
                <div className="grid grid-cols-3 gap-2 shrink-0">
                  {/* Return tahunan */}
                  <div className="panel rounded-xl p-3 flex flex-col gap-0.5">
                    <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest flex items-center gap-1">
                      <TrendingUp className="h-2.5 w-2.5 text-emerald-400" /> Return / Tahun
                    </span>
                    <span className="text-3xl font-black text-emerald-400 tabular-nums leading-none mt-1">
                      {portfolioData.return.percentage}
                    </span>
                    <span className="text-[10px] text-slate-500 mt-0.5">estimasi berbasis data historis</span>
                  </div>
                  {/* Sharpe */}
                  <div className="panel rounded-xl p-3 flex flex-col gap-0.5">
                    <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest flex items-center gap-1">
                      <Gauge className="h-2.5 w-2.5 text-sky-400" /> Sharpe Ratio
                    </span>
                    <span className="text-3xl font-black text-sky-400 tabular-nums leading-none mt-1">
                      {portfolioData.sharpe.value}
                    </span>
                    <span className="text-[10px] text-slate-500 mt-0.5">efisiensi portofolio</span>
                  </div>
                  {/* Modal */}
                  <div className="panel rounded-xl p-3 flex flex-col gap-0.5">
                    <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest flex items-center gap-1">
                      <Banknote className="h-2.5 w-2.5 text-slate-400" /> Modal · {duration} Tahun
                    </span>
                    <span className="text-xl font-black text-slate-200 tabular-nums leading-none mt-1">
                      {portfolioData.capital}
                    </span>
                    <span className="text-[10px] text-slate-500 mt-0.5">diinvestasikan</span>
                  </div>
                </div>
              );
            })()}

            {/* Profit Highlight — computed from frontend, full Indonesian */}
            {(() => {
              const returnPct  = parseFloat(portfolioData.return.percentage) / 100;
              const projected  = capital * Math.pow(1 + returnPct, duration);
              const profit     = projected - capital;
              const growthPct  = ((projected / capital - 1) * 100).toFixed(1);
              return (
                <div className="shrink-0 rounded-xl border border-emerald-500/25 bg-gradient-to-r from-emerald-500/10 to-transparent p-4 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-2 bg-emerald-500/15 rounded-lg border border-emerald-500/25 shrink-0">
                      <TrendingUp className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Estimasi Profit dalam {duration} Tahun</p>
                      <p className="text-2xl font-black text-emerald-400 tabular-nums leading-tight">+{formatIDR(profit)}</p>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[10px] text-slate-500">Modal berkembang menjadi</p>
                    <p className="text-base font-black text-slate-100 tabular-nums">{formatIDR(projected)}</p>
                    <p className="text-[10px] text-emerald-400 font-bold mt-0.5">+{growthPct}% total</p>
                  </div>
                </div>
              );
            })()}

            {/* Risk + Drawdown — side by side */}
            <div className="grid grid-cols-2 gap-2 shrink-0">
              <div className="panel rounded-xl p-3 flex flex-col gap-2">
                <Label Icon={Gauge} text="Volatilitas" />
                <div className="relative h-2 rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500">
                  <div
                    className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-4 w-4 rounded-full bg-white shadow border-2 border-[#0b0f1a] transition-all duration-700"
                    style={{ left: `${riskMeterPos}%` }}
                  />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-lg font-black text-amber-400">{portfolioData.volatility.percentage}</span>
                  <span className="text-[10px] text-slate-500">per tahun</span>
                </div>
                <p className="text-[10px] text-slate-600 leading-relaxed">{portfolioData.volatility.description}</p>
              </div>
              <div className="panel rounded-xl p-3 flex flex-col gap-2">
                <Label Icon={AlertTriangle} text="Max Drawdown" />
                <div className="flex items-baseline gap-1.5">
                  <span className="text-lg font-black text-rose-400">{portfolioData.drawdown.percentage}</span>
                  <span className="text-[10px] text-slate-500">historis</span>
                </div>
                <p className="text-sm font-semibold text-rose-400/60">{portfolioData.drawdown.nominal}</p>
                <p className="text-[10px] text-slate-600">Penurunan terbesar dalam data historis. Bersifat sementara.</p>
              </div>

            </div>

            {/* Donut chart — fills remaining space */}
            <div className="panel rounded-xl p-4 flex flex-col flex-1 min-h-0">
              <Label Icon={BarChart3} text="Komposisi Portofolio" />
              <div className="flex flex-1 min-h-0 gap-4">
                {/* Chart */}
                <div className="relative flex-1 min-h-0 min-w-0">
                  {allocationChart && (
                    <Doughnut
                      data={allocationChart}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false },
                          tooltip: { callbacks: { label: (c) => ` ${c.label}: ${(c.raw as number).toFixed(1)}%` } },
                        },
                        cutout: "68%",
                      }}
                    />
                  )}
                  <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                    <span className="text-[9px] text-slate-600">Modal</span>
                    <span className="text-xs font-black text-slate-300">{portfolioData.capital}</span>
                  </div>
                </div>
                {/* Legend grid */}
                <div className="w-36 flex flex-col gap-1 justify-center overflow-hidden shrink-0">
                  {sortedAllocation.slice(0, 10).map((item, i) => (
                    <div key={i} className="flex items-center gap-1.5 min-w-0">
                      <div className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: CHART_PALETTE[i % CHART_PALETTE.length] }} />
                      <span className="text-[10px] text-slate-400 truncate flex-1">{item.asset}</span>
                      <span className="text-[10px] font-bold text-slate-300 shrink-0">{item.percentage}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ─── RIGHT COLUMN ────────────────────────────────── */}
          <div className="flex flex-col gap-3 h-full overflow-hidden">

            {/* Allocation list — takes most of right column */}
            <div className="panel rounded-xl p-4 flex flex-col flex-1 min-h-0">
              <Label Icon={Layers} text="Alokasi Optimal" />
              <div className="flex flex-col gap-1.5 overflow-y-auto flex-1 min-h-0 pr-0.5">
                {sortedAllocation.map((item, i) => {
                  const pct   = parseFloat(item.percentage);
                  const color = CHART_PALETTE[i % CHART_PALETTE.length];
                  return (
                    <div
                      key={i}
                      onClick={() => handleAssetClick(item.asset)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.025] border border-white/[0.05] hover:border-sky-500/30 hover:bg-sky-500/5 cursor-pointer transition-all active:scale-[0.98] shrink-0 group"
                      title="Klik untuk detail aset"
                    >
                      <div className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: color }} />
                      <span className="text-xs font-bold text-slate-100 flex-1 truncate min-w-0">{item.asset}</span>
                      {/* Progress bar */}
                      <div className="w-16 h-1 bg-white/[0.05] rounded-full overflow-hidden shrink-0">
                        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
                      </div>
                      <span className="text-xs font-black tabular-nums shrink-0 w-12 text-right" style={{ color }}>{item.percentage}</span>
                      <span className="text-xs text-slate-400 font-mono shrink-0 w-24 text-right">
                        {item.nominal.startsWith("IDR")
                          ? formatIDR(parseInt(item.nominal.replace(/[^0-9]/g, ""), 10) || 0)
                          : item.nominal}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* GA Insight */}
            <div className="panel rounded-xl p-3 shrink-0">
              <Label Icon={FlaskConical} text="Proses Optimasi AI" />
              <p className="text-xs text-slate-500 leading-relaxed line-clamp-3">{portfolioData.ga_insight.insight}</p>
            </div>

            {/* Aksi + Disclaimer */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => { setStep(1); setPortfolioData(null); setBenchmarkData(null); }}
                className="flex-1 py-2.5 rounded-xl border border-white/[0.07] text-slate-400 hover:text-slate-200 font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                <RotateCcw className="h-3 w-3" /> Ubah Input
              </button>
              <button
                id="btn-benchmark"
                onClick={handleBenchmark}
                disabled={benchmarking}
                className="flex-1 bg-white/[0.04] hover:bg-white/[0.07] border border-white/[0.08] text-slate-300 font-bold py-2.5 rounded-xl
                           flex items-center justify-center gap-1.5 transition-all text-xs disabled:opacity-50"
              >
                {benchmarking
                  ? <><RefreshCw className="h-3 w-3 animate-spin" /> Mengukur…</>
                  : <><Zap className="h-3 w-3" /> Uji Kecepatan Engine</>}
              </button>
              <div className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl border border-amber-500/15 bg-amber-500/5 shrink-0">
                <Info className="h-3 w-3 text-amber-500 shrink-0" />
                <span className="text-[10px] text-slate-600 leading-tight">Simulasi historis<br />Bukan saran investasi</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════
          INPUT & LOADING — Asymmetric 2-Column Desktop Grid
      ══════════════════════════════════════════════════════════ */}
      {!portfolioData && (
        <main className="max-w-5xl mx-auto px-6 py-8 md:py-12 grid grid-cols-1 md:grid-cols-12 gap-8 md:gap-12 items-center min-h-[calc(100vh-120px)] animate-fade-in">
          
          {/* Column 1: Hero & Step Indicator (Takes 5/12 cols) */}
          <div className="md:col-span-5 flex flex-col gap-6 md:gap-8 justify-center">
            {!loading && (
              <section className="animate-fade-in flex flex-col gap-3">
                <div className="flex items-center gap-2 text-[10px] font-bold text-sky-400 uppercase tracking-widest">
                  <BadgeCheck className="h-3.5 w-3.5" /> Data real · Optimasi AI · Gratis
                </div>
                <h1 className="text-3xl md:text-4xl lg:text-5xl font-black tracking-tight leading-[1.1]">
                  Alokasi investasi optimal<br />
                  <span className="text-sky-400">dari ribuan kemungkinan.</span>
                </h1>
                <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
                  Masukkan modal dan profil risiko, lalu biarkan Genetic Algorithm menemukan portofolio terbaik dari data pasar nyata.
                </p>
              </section>
            )}
            {loading && (
              <section className="animate-fade-in flex flex-col gap-3">
                <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-400 uppercase tracking-widest">
                  <Dna className="h-3.5 w-3.5 animate-spin-slow" /> Mengoptimasi Portofolio
                </div>
                <h1 className="text-3xl md:text-4xl lg:text-5xl font-black tracking-tight leading-[1.1] text-slate-100">
                  Memproses<br />
                  <span className="text-emerald-400">Algoritma Genetika.</span>
                </h1>
                <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
                  Harap tunggu selagi sistem kami mensimulasikan dan menganalisis ribuan kombinasi portofolio terbaik.
                </p>
              </section>
            )}

            {/* Step indicator */}
            <div className="pt-2 w-full">
              <StepIndicator step={loading ? 3 : step} />
            </div>
          </div>

          {/* Column 2: Wizard Active Step Cards (Takes 7/12 cols) */}
          <div className="md:col-span-7 w-full flex items-center justify-center">
            <div className="w-full">
              {/* ── STEP 1: MODAL ─────────────────────────────────── */}
              {!loading && step === 1 && (
                <section className="panel rounded-2xl p-6 md:p-8 animate-slide-up">
                  <Label Icon={Banknote} text="Langkah 1 · Modal Investasi" />
                  <h2 className="text-lg font-black text-white mb-5">Berapa modal yang ingin kamu investasikan?</h2>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {CAPITAL_PRESETS.map((p) => (
                      <PresetBtn key={p.value} label={p.label}
                        active={capital === p.value && capitalInput === ""}
                        onClick={() => { setCapital(p.value); setCapitalInput(""); }} />
                    ))}
                  </div>

                  <div className="relative mb-4">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm font-bold pointer-events-none">Rp</span>
                    <input
                      type="text" inputMode="numeric"
                      value={capitalInput}
                      onChange={handleCapitalTextChange}
                      onBlur={handleCapitalTextBlur}
                      placeholder={capital.toLocaleString("id-ID")}
                      className="w-full pl-10 pr-28 py-3 bg-white/[0.03] border border-white/[0.08] rounded-xl
                                 text-slate-200 text-sm font-mono placeholder-slate-600
                                 focus:border-sky-500/50 focus:outline-none focus:bg-white/[0.05] transition-all"
                    />
                    <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-xs text-slate-600">atau ketik sendiri</span>
                  </div>

                  <input
                    type="range" min={500_000} max={100_000_000} step={500_000}
                    value={capital} onChange={(e) => { setCapital(Number(e.target.value)); setCapitalInput(""); }}
                    className="mb-1"
                  />
                  <div className="flex justify-between text-xs text-slate-600 mb-5">
                    <span>Rp 500 Ribu</span><span>Rp 100 Juta</span>
                  </div>

                  <div className="bg-sky-500/8 border border-sky-500/20 rounded-xl p-4 mb-6 flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-500">Modal yang diinvestasikan</p>
                      <p className="text-2xl font-black text-sky-300 tabular-nums mt-0.5">{formatIDR(capital)}</p>
                    </div>
                    <Banknote className="h-8 w-8 text-sky-500/25" />
                  </div>

                  <button onClick={() => setStep(2)}
                    className="w-full bg-sky-500 hover:bg-sky-400 active:scale-[0.98] text-white font-bold py-3.5 rounded-xl
                               flex items-center justify-center gap-2 transition-all shadow-lg shadow-sky-500/20">
                    Pilih Profil Risiko <ArrowRight className="h-4 w-4" />
                  </button>
                </section>
              )}

              {/* ── STEP 2: PROFIL RISIKO ─────────────────────────── */}
              {!loading && step === 2 && (
                <section className="panel rounded-2xl p-6 md:p-7 animate-slide-up">
                  <Label Icon={SlidersHorizontal} text="Langkah 2 · Profil Risiko" />
                  <h2 className="text-lg font-black text-white mb-5">Seberapa berani kamu menghadapi risiko?</h2>

                  <div className="flex flex-col gap-3 mb-6">
                    {RISK_PROFILES.map((p) => {
                      const c   = CM[p.color];
                      const sel = riskProfile === p.id;
                      return (
                        <div key={p.id} onClick={() => setRiskProfile(p.id)}
                          className={`flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all duration-150 select-none
                            ${sel ? `${c.border} ${c.bg}` : "border-white/[0.07] bg-white/[0.02] hover:border-white/[0.12]"}`}>
                          <div className={`p-2 rounded-lg mt-0.5 shrink-0 ${sel ? c.bg + " border " + c.border : "bg-white/[0.04] border border-white/[0.06]"}`}>
                            <p.Icon className={`h-4 w-4 ${sel ? c.text : "text-slate-500"}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className={`font-black text-sm ${sel ? c.text : "text-slate-200"}`}>{p.label}</span>
                              <span className="text-xs text-slate-600">· {p.sub}</span>
                            </div>
                            <p className="text-xs text-slate-400 leading-relaxed mb-1.5">{p.desc}</p>
                            <p className={`text-[11px] font-semibold ${sel ? c.text : "text-slate-600"}`}>{p.suitable}</p>
                          </div>
                          <div className={`h-4 w-4 rounded-full border-2 shrink-0 mt-1 flex items-center justify-center transition-all
                            ${sel ? `${c.dot} border-transparent` : "border-slate-700"}`}>
                            {sel && <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="flex gap-3">
                    <button onClick={() => setStep(1)}
                      className="flex-1 py-3 rounded-xl border border-white/[0.07] text-slate-400 hover:text-slate-200 font-bold text-sm transition-colors">
                      Kembali
                    </button>
                    <button onClick={() => setStep(3)}
                      className="flex-[2] bg-sky-500 hover:bg-sky-400 active:scale-[0.98] text-white font-bold py-3 rounded-xl
                                 flex items-center justify-center gap-2 transition-all text-sm shadow-lg shadow-sky-500/15">
                      Pilih Durasi <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                </section>
              )}

              {/* ── STEP 3: DURASI ────────────────────────────────── */}
              {!loading && step === 3 && (
                <section className="panel rounded-2xl p-6 md:p-7 animate-slide-up flex flex-col gap-5">
                  <div>
                    <Label Icon={CalendarDays} text="Langkah 3 · Jangka Waktu" />
                    <h2 className="text-lg font-black text-white mb-4">Berapa lama rencana investasimu?</h2>
                    <div className="grid grid-cols-3 gap-3">
                      {DURATION_OPTIONS.map((d) => (
                        <button key={d.value} onClick={() => setDuration(d.value)}
                          className={`flex flex-col items-center gap-0.5 py-4 rounded-xl border font-bold transition-all
                            ${duration === d.value
                              ? "bg-sky-500/15 border-sky-500/60 text-sky-300"
                              : "bg-white/[0.02] border-white/[0.07] text-slate-400 hover:border-white/20 hover:text-slate-200"}`}>
                          <span className="text-lg font-black">{d.label}</span>
                          <span className="text-[11px] opacity-60">{d.sub}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="bg-white/[0.02] border border-white/[0.07] rounded-xl p-4">
                    <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-3">Ringkasan</p>
                    <div className="grid grid-cols-3 gap-3 text-center">
                      {[
                        { Icon: Banknote,      label: "Modal",    val: formatIDR(capital) },
                        { Icon: activeRisk.Icon, label: "Profil", val: activeRisk.label },
                        { Icon: CalendarDays,  label: "Durasi",   val: `${duration} Tahun` },
                      ].map((item) => (
                        <div key={item.label} className="flex flex-col items-center gap-1.5">
                          <item.Icon className="h-4 w-4 text-sky-400" />
                          <span className="text-xs text-slate-500">{item.label}</span>
                          <span className="text-sm font-bold text-slate-100">{item.val}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Engine */}
                  <div className="rounded-xl border border-white/[0.07] overflow-hidden">
                    <button onClick={() => setShowEngine((v) => !v)}
                      className="w-full flex items-center justify-between px-4 py-3 text-xs font-semibold text-slate-600 hover:text-slate-400 transition-colors">
                      <span className="flex items-center gap-2"><Network className="h-3.5 w-3.5" /> Engine Komputasi (opsional)</span>
                      {showEngine ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    </button>
                    {showEngine && (
                      <div className="px-4 pb-4 pt-1 border-t border-white/[0.05] grid grid-cols-2 gap-2">
                        {ENGINE_OPTIONS.map((opt) => (
                          <div key={opt.value} onClick={() => setEngineMode(opt.value)}
                            className={`p-3 rounded-lg border cursor-pointer transition-all
                              ${engineMode === opt.value
                                ? "border-sky-500/50 bg-sky-500/8 text-sky-300"
                                : "border-white/[0.06] bg-white/[0.02] text-slate-500 hover:border-white/15 hover:text-slate-300"}`}>
                            <div className="font-semibold text-xs">{opt.label}</div>
                            <div className="text-[10px] text-slate-600 mt-0.5">{opt.sub}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-3">
                    <button onClick={() => setStep(2)}
                      className="flex-1 py-3.5 rounded-xl border border-white/[0.07] text-slate-400 hover:text-slate-200 font-bold text-sm transition-colors">
                      Kembali
                    </button>
                    <button id="btn-optimize" onClick={handleOptimize} disabled={loading}
                      className="flex-[2] bg-sky-500 hover:bg-sky-400 active:scale-[0.98] text-white font-bold py-3.5 rounded-xl
                                 flex items-center justify-center gap-2 transition-all text-sm shadow-lg shadow-sky-500/20
                                 disabled:opacity-50 disabled:cursor-not-allowed">
                      <FlaskConical className="h-4 w-4" /> Jalankan Optimasi
                    </button>
                  </div>
                </section>
              )}

              {/* ── LOADING ───────────────────────────────────────── */}
              {loading && (
                <section className="panel rounded-2xl p-8 flex flex-col items-center gap-6 animate-fade-in">
                  <div className="relative h-14 w-14">
                    <div className="absolute inset-0 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
                    <div className="absolute inset-2.5 flex items-center justify-center">
                      <Dna className="h-5 w-5 text-sky-400 animate-spin-slow" />
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="font-black text-sm text-slate-200 mb-1">Genetic Algorithm sedang berjalan</p>
                    <p className="text-xs text-slate-600">Sekitar 10–15 detik · 500 populasi × 150 generasi</p>
                  </div>
                  <div className="w-full max-w-sm flex flex-col gap-2.5 stagger">
                    {LOADING_STEPS.map((s, i) => (
                      <div key={i} className={`flex items-center gap-3 transition-all duration-500 ${i <= loadingStep ? "opacity-100" : "opacity-15"}`}>
                        <div className={`h-6 w-6 rounded-full border flex-shrink-0 flex items-center justify-center transition-all
                          ${i < loadingStep  ? "bg-emerald-500 border-emerald-500" :
                            i === loadingStep ? "border-sky-400 bg-sky-500/15" :
                                                "border-slate-800"}`}>
                          {i < loadingStep   ? <CheckCircle className="h-3.5 w-3.5 text-white" />
                           : i === loadingStep ? <div className="h-1.5 w-1.5 rounded-full bg-sky-400 animate-pulse" />
                           : null}
                        </div>
                        <span className={`text-sm ${i === loadingStep ? "text-slate-200 font-semibold" : "text-slate-500"}`}>
                          {s.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </div>
        </main>
      )}

      {/* Footer — only on input pages */}
      {!portfolioData && (
        <footer className="border-t border-white/[0.05] bg-[#0b0f1a] py-6 mt-4">
          <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-2 text-xs text-slate-700">
            <div className="flex items-center gap-2"><Dna className="h-3.5 w-3.5" /><span>OptiGene · Parallel Computing Research · 2026</span></div>
            <span className="hidden md:block">PySpark · CUDA · Genetic Algorithm · Next.js</span>
          </div>
        </footer>
      )}
    </div>
  );
}
