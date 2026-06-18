"use client";

import React, { useState } from "react";
import { 
  Dna, Wallet, Shield, Scale, Bolt, Sliders, Calendar, 
  Cpu, Play, BarChart3, AlertTriangle, ShieldCheck, 
  TrendingUp, BarChart, Trophy, Activity, RefreshCw, Info,
  Gauge
} from "lucide-react";
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from "chart.js";
import { Doughnut, Bar } from "react-chartjs-2";

// Register Chart.js elements
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

export default function Home() {
  // Input States
  const [capital, setCapital] = useState(5000000);
  const [riskProfile, setRiskProfile] = useState("aman");
  const [duration, setDuration] = useState(3);
  const [engineMode, setEngineMode] = useState("numpy_vectorized");
  
  // Loading & View States
  const [loading, setLoading] = useState(false);
  const [benchmarking, setBenchmarking] = useState(false);
  const [portfolioData, setPortfolioData] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);

  // Asset chart colors palette
  const palette = [
    "#10b981", // Time Deposit (Emerald)
    "#06b6d4", // Government Bonds SBN (Cyan)
    "#f59e0b", // Gold (Amber)
    "#8b5cf6", // Violet
    "#ec4899", // Pink
    "#f97316", // Orange
    "#84cc16", // Lime
    "#d946ef", // Fuchsia
    "#3b82f6", // Blue
    "#a855f7", // Purple
    "#eab308", // Yellow
    "#14b8a6", // Teal
    "#ef4444"  // Red
  ];

  // Portfolio optimization handler
  const handleOptimize = async (e) => {
    e.preventDefault();
    setLoading(true);
    setPortfolioData(null);

    try {
      const response = await fetch("/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          capital,
          profile: riskProfile,
          duration,
          mode: engineMode,
        }),
      });

      const result = await response.json();
      if (result.status === "success") {
        setPortfolioData(result.data);
      } else {
        alert("Error: " + result.message);
      }
    } catch (error) {
      console.error("Optimization failed:", error);
      alert("Failed to connect to the API server. Please make sure the FastAPI server is running.");
    } finally {
      setLoading(false);
    }
  };

  // Benchmark execution handler
  const handleBenchmark = async () => {
    setBenchmarking(true);
    setBenchmarkData(null);

    try {
      const response = await fetch("/api/benchmark", {
        method: "POST",
      });
      const result = await response.json();
      if (result.status === "success") {
        setBenchmarkData(result.data);
      } else {
        alert("Error: " + result.message);
      }
    } catch (error) {
      console.error("Benchmark failed:", error);
      alert("An error occurred while running the performance benchmark.");
    } finally {
      setBenchmarking(false);
    }
  };

  // Setup data for Asset Allocation Doughnut Chart
  const getAllocationChartData = () => {
    if (!portfolioData) return null;
    
    const labels = portfolioData.allocation.map(item => item.asset);
    const data = portfolioData.allocation.map(item => parseFloat(item.percentage.replace("%", "")));
    const backgroundColors = portfolioData.allocation.map((_, idx) => palette[idx % palette.length]);

    return {
      labels,
      datasets: [
        {
          data,
          backgroundColor: backgroundColors,
          borderWidth: 2,
          borderColor: "#0f172a", // Slate-900
          hoverOffset: 4
        }
      ]
    };
  };

  // Setup data for Benchmark Bar Chart
  const getBenchmarkChartData = () => {
    if (!benchmarkData) return null;
    
    const labels = benchmarkData.map(item => item.Method);
    const data = benchmarkData.map(item => item["Time (s)"] || 0);

    const barColors = [
      "rgba(239, 68, 68, 0.75)",  // Red (Sequential)
      "rgba(59, 130, 246, 0.75)",  // Blue (Spark SQL)
      "rgba(234, 179, 8, 0.75)",   // Yellow (Spark RDD map)
      "rgba(16, 185, 129, 0.75)",  // Green (Spark RDD filter/reduce)
      "rgba(139, 92, 246, 0.75)",  // Purple (CUDA GPU)
      "rgba(249, 115, 22, 0.75)"   // Orange (Spark + CUDA Hybrid)
    ];

    const borderColors = [
      "rgba(239, 68, 68, 1)",
      "rgba(59, 130, 246, 1)",
      "rgba(234, 179, 8, 1)",
      "rgba(16, 185, 129, 1)",
      "rgba(139, 92, 246, 1)",
      "rgba(249, 115, 22, 1)"
    ];

    return {
      labels,
      datasets: [
        {
          label: "Execution Time (Seconds)",
          data,
          backgroundColor: barColors.slice(0, labels.length),
          borderColor: borderColors.slice(0, labels.length),
          borderWidth: 1.5
        }
      ]
    };
  };

  // Get the fastest method execution time
  const getFastestBenchmarkTime = () => {
    if (!benchmarkData) return null;
    const validTimes = benchmarkData.filter(d => d["Time (s)"] !== null && !isNaN(d["Time (s)"]));
    return Math.min(...validTimes.map(d => d["Time (s)"]));
  };

  const fastestTime = getFastestBenchmarkTime();

  return (
    <div className="relative min-h-screen">
      {/* Background Orbs */}
      <div className="glow-orb orb-1 top-[-10%] right-[-10%] w-[50vw] h-[50vw] bg-purple-600"></div>
      <div className="glow-orb orb-2 bottom-[-20%] left-[-10%] w-[60vw] h-[60vw] bg-cyan-600"></div>
      <div className="glow-orb orb-3 top-[40%] left-[45%] w-[35vw] h-[35vw] bg-emerald-600"></div>

      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-gray-800 bg-[#030712]/85 backdrop-blur-md px-6 py-4">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <Dna className="h-8 w-8 text-purple-500 animate-pulse" />
            <span className="text-2xl font-black tracking-tight">
              Opti<span className="text-purple-500">Gene</span>
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-purple-500/10 border border-purple-500/30 rounded-full text-purple-400 text-xs font-semibold">
            <Cpu className="h-4 w-4" /> GPU & CPU Parallel Engine
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto px-4 py-8 flex flex-col gap-10">
        
        {/* Input Configuration Panel */}
        <section className="glass-panel rounded-2xl p-6 md:p-8">
          <h2 className="text-xl font-bold flex items-center gap-3 mb-6">
            <Sliders className="h-5 w-5 text-purple-500" /> Portfolio Settings
          </h2>
          
          <form onSubmit={handleOptimize} className="flex flex-col gap-6">
            {/* Capital & Risk Profile */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Nominal Modal */}
              <div className="md:col-span-1 flex flex-col gap-2">
                <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <Wallet className="h-4 w-4 text-purple-400" /> Investment Capital
                </label>
                <div className="relative flex items-center">
                  <span className="absolute left-4 text-gray-500 font-bold text-lg">IDR</span>
                  <input 
                    type="number" 
                    value={capital}
                    onChange={(e) => setCapital(parseFloat(e.target.value))}
                    min="100000"
                    step="100000"
                    className="w-full bg-[#090d16] border border-gray-700/60 rounded-xl py-3 pl-14 pr-4 text-lg font-bold text-gray-100 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition-all"
                    required
                  />
                </div>
                <span className="text-xs text-gray-500">E.g., 5,000,000 (Five Million Rupiah)</span>
              </div>

              {/* Profil Risiko */}
              <div className="md:col-span-2 flex flex-col gap-2">
                <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-purple-400" /> Risk Profile
                </label>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Card Conservative */}
                  <div 
                    onClick={() => setRiskProfile("aman")}
                    className={`flex flex-col p-4 rounded-xl cursor-pointer border transition-all hover:-translate-y-0.5 ${
                      riskProfile === "aman" 
                        ? "bg-slate-800/80 border-emerald-500 shadow-md shadow-emerald-500/5" 
                        : "bg-[#090d16]/40 border-gray-700/50 hover:bg-[#090d16]/75 hover:border-emerald-500/40"
                    }`}
                  >
                    <Shield className="h-6 w-6 text-emerald-500 mb-2" />
                    <span className="font-bold text-sm">Conservative</span>
                    <span className="text-xs text-gray-400 mt-1">Stocks max 20%, Cash/Bonds min 60%</span>
                  </div>

                  {/* Card Moderate */}
                  <div 
                    onClick={() => setRiskProfile("seimbang")}
                    className={`flex flex-col p-4 rounded-xl cursor-pointer border transition-all hover:-translate-y-0.5 ${
                      riskProfile === "seimbang" 
                        ? "bg-slate-800/80 border-amber-500 shadow-md shadow-amber-500/5" 
                        : "bg-[#090d16]/40 border-gray-700/50 hover:bg-[#090d16]/75 hover:border-amber-500/40"
                    }`}
                  >
                    <Scale className="h-6 w-6 text-amber-500 mb-2" />
                    <span className="font-bold text-sm">Moderate</span>
                    <span className="text-xs text-gray-400 mt-1">Stocks max 50%, Cash/Bonds min 30%</span>
                  </div>

                  {/* Card Aggressive */}
                  <div 
                    onClick={() => setRiskProfile("agresif")}
                    className={`flex flex-col p-4 rounded-xl cursor-pointer border transition-all hover:-translate-y-0.5 ${
                      riskProfile === "agresif" 
                        ? "bg-slate-800/80 border-red-500 shadow-md shadow-red-500/5" 
                        : "bg-[#090d16]/40 border-gray-700/50 hover:bg-[#090d16]/75 hover:border-red-500/40"
                    }`}
                  >
                    <Bolt className="h-6 w-6 text-red-500 mb-2" />
                    <span className="font-bold text-sm">Aggressive</span>
                    <span className="text-xs text-gray-400 mt-1">Stocks max 80%, Cash/Bonds min 10%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Duration & Engine */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-purple-400" /> Investment Duration
                </label>
                <select 
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="w-full bg-[#090d16] border border-gray-700/60 rounded-xl p-3 font-semibold text-gray-100 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition-all cursor-pointer"
                >
                  <option value="1">1 Year</option>
                  <option value="3">3 Years</option>
                  <option value="5">5 Years</option>
                </select>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-purple-400" /> Computation Engine
                </label>
                <select 
                  value={engineMode}
                  onChange={(e) => setEngineMode(e.target.value)}
                  className="w-full bg-[#090d16] border border-gray-700/60 rounded-xl p-3 font-semibold text-gray-100 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition-all cursor-pointer"
                >
                  <option value="numpy_vectorized">Vectorized CPU (NumPy)</option>
                  <option value="cuda">GPU CUDA (CuPy)</option>
                  <option value="pyspark_cpu">Parallel CPU (PySpark RDD)</option>
                  <option value="pyspark_cuda">Parallel Hybrid (PySpark + CUDA)</option>
                </select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 mt-4">
              <button 
                type="submit" 
                disabled={loading}
                className="flex-2 bg-purple-600 hover:bg-purple-500 active:bg-purple-700 text-white font-bold py-3 px-6 rounded-xl shadow-lg shadow-purple-600/20 hover:shadow-purple-600/35 flex items-center justify-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? (
                  <>
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    <span>Optimizing Portfolio...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 fill-current" />
                    <span>Optimize Portfolio</span>
                  </>
                )}
              </button>

              <button 
                type="button" 
                onClick={handleBenchmark}
                disabled={benchmarking}
                className="flex-1 bg-slate-800 hover:bg-slate-700 active:bg-slate-900 border border-gray-700 text-gray-200 font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {benchmarking ? (
                  <>
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    <span>Benchmarking...</span>
                  </>
                ) : (
                  <>
                    <BarChart3 className="h-5 w-5" />
                    <span>Run 6-Method Benchmark</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        {/* Loading GA State */}
        {loading && (
          <div className="glass-panel rounded-2xl p-10 flex flex-col items-center justify-center text-center gap-4 animate-pulse">
            <Dna className="h-16 w-16 text-purple-500 animate-spin" />
            <h3 className="text-xl font-bold">Genetic Algorithm Processing...</h3>
            <p className="text-sm text-gray-400 max-w-md">Simulating and evaluating thousands of portfolio configurations using parallel execution.</p>
          </div>
        )}

        {/* Results Panel */}
        {portfolioData && (
          <section className="flex flex-col gap-6">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-gray-800 pb-4">
              <h2 className="text-2xl font-extrabold flex items-center gap-3">
                <BarChart className="h-6 w-6 text-emerald-500" /> Recommended Portfolio Allocation
              </h2>
              <span className="px-4 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 font-bold text-lg">
                Capital: {portfolioData.capital}
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Metrics cards list */}
              <div className="flex flex-col gap-4">
                
                {/* Expected Return */}
                <div className="glass-panel rounded-xl p-5 flex items-start gap-4 hover:border-emerald-500/30 transition-all">
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-500">
                    <TrendingUp className="h-6 w-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Projected Return</span>
                    <h4 className="text-2xl font-black text-emerald-400 mt-1">{portfolioData.return.percentage}</h4>
                    <p className="text-sm text-gray-400 mt-2 leading-relaxed">{portfolioData.return.description}</p>
                  </div>
                </div>

                {/* Volatility */}
                <div className="glass-panel rounded-xl p-5 flex items-start gap-4 hover:border-amber-500/30 transition-all">
                  <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-500">
                    <Activity className="h-6 w-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Portfolio Risk (Volatility)</span>
                    <h4 className="text-2xl font-black text-amber-400 mt-1">
                      {portfolioData.volatility.percentage} <span className="text-sm font-bold text-gray-500">({portfolioData.volatility.label})</span>
                    </h4>
                    <p className="text-sm text-gray-400 mt-2 leading-relaxed">{portfolioData.volatility.description}</p>
                  </div>
                </div>

                {/* Drawdown */}
                <div className="glass-panel rounded-xl p-5 flex items-start gap-4 hover:border-red-500/30 transition-all">
                  <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500">
                    <AlertTriangle className="h-6 w-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Worst-case Drop (Drawdown)</span>
                    <h4 className="text-2xl font-black text-red-400 mt-1">
                      {portfolioData.drawdown.percentage} <span className="text-sm font-bold text-gray-500">({portfolioData.drawdown.nominal})</span>
                    </h4>
                    <p className="text-sm text-gray-400 mt-2 leading-relaxed">{portfolioData.drawdown.description}</p>
                  </div>
                </div>

                {/* Sharpe Ratio */}
                <div className="glass-panel rounded-xl p-5 flex items-start gap-4 hover:border-cyan-500/30 transition-all">
                  <div className="p-3 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-500">
                    <Trophy className="h-6 w-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Investment Efficiency (Sharpe)</span>
                    <h4 className="text-2xl font-black text-cyan-400 mt-1">
                      {portfolioData.sharpe.value} <span className="text-sm font-bold text-gray-500">({portfolioData.sharpe.label})</span>
                    </h4>
                    <p className="text-sm text-gray-400 mt-2 leading-relaxed">{portfolioData.sharpe.description}</p>
                  </div>
                </div>

              </div>

              {/* Chart card */}
              <div className="glass-panel rounded-xl p-6 flex flex-col gap-6">
                <h3 className="text-lg font-bold">Recommended Allocation Breakdown</h3>
                <div className="relative h-64 w-full flex justify-center items-center">
                  <Doughnut 
                    data={getAllocationChartData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          callbacks: {
                            label: (context) => ` ${context.label}: ${context.raw.toFixed(2)}%`
                          }
                        }
                      },
                      cutout: "68%"
                    }}
                  />
                </div>
                
                {/* List Legend items */}
                <div className="flex flex-col gap-2">
                  {portfolioData.allocation.map((item, idx) => {
                    const color = palette[idx % palette.length];
                    return (
                      <div key={idx} className="flex justify-between items-center p-3 bg-slate-900/30 border border-gray-800/80 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="h-3 w-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }}></div>
                          <div>
                            <div className="text-sm font-semibold">{item.asset}</div>
                            <div className="text-xs text-gray-500">{item.description}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-gray-200">{item.percentage}</div>
                          <div className="text-xs text-gray-400">{item.nominal}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* GA Insight */}
            <div className="glass-panel rounded-xl p-6 bg-purple-950/10 border-purple-500/25 flex items-center gap-5 mt-4">
              <Dna className="h-10 w-10 text-purple-400 flex-shrink-0 animate-pulse" />
              <div>
                <h4 className="font-bold text-purple-400 text-sm">Genetic Algorithm Insight</h4>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">{portfolioData.ga_insight.insight}</p>
              </div>
            </div>
          </section>
        )}

        {/* Benchmark Results */}
        {benchmarkData && (
          <section className="flex flex-col gap-6">
            <div className="border-b border-gray-800 pb-4">
              <h2 className="text-2xl font-extrabold flex items-center gap-3">
                <Gauge className="h-6 w-6 text-purple-500" /> Computation Speed Benchmark
              </h2>
              <p className="text-sm text-gray-500 mt-1">Comparing computational times of Sharpe Ratio evaluations for a population of 1,000 portfolios.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Table */}
              <div className="glass-panel rounded-xl p-4 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-gray-800">
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Execution Method</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Execution Time</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Speedup Factor</th>
                        <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Optimal Sharpe</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmarkData.map((item, idx) => {
                        const isBest = item["Time (s)"] === fastestTime;
                        return (
                          <tr 
                            key={idx} 
                            className={`border-b border-gray-800/50 last:border-0 ${
                              isBest ? "bg-emerald-500/5 text-emerald-400 font-semibold" : ""
                            }`}
                          >
                            <td className="py-3 px-4 text-sm flex items-center gap-2">
                              {isBest && <Trophy className="h-4 w-4 text-amber-500" />}
                              {item.Method}
                            </td>
                            <td className="py-3 px-4 text-sm font-mono">
                              {item["Time (s)"] !== null ? `${item["Time (s)"].toFixed(4)} s` : "N/A"}
                            </td>
                            <td className="py-3 px-4 text-sm font-mono">
                              {item["Speedup"] !== null ? `${item["Speedup"].toFixed(2)}x` : "N/A"}
                            </td>
                            <td className="py-3 px-4 text-sm font-mono">
                              {item["Best Sharpe"] !== null ? item["Best Sharpe"].toFixed(4) : "N/A"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Bar Chart */}
              <div className="glass-panel rounded-xl p-6 flex flex-col justify-between min-h-[300px]">
                <h3 className="text-md font-bold mb-4">Execution Time Comparison (Seconds)</h3>
                <div className="relative flex-1">
                  <Bar 
                    data={getBenchmarkChartData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          grid: { color: "rgba(255, 255, 255, 0.05)" },
                          ticks: { color: "#9ca3af" }
                        },
                        x: {
                          grid: { display: false },
                          ticks: { color: "#9ca3af", font: { size: 9 } }
                        }
                      }
                    }}
                  />
                </div>
                <div className="text-center text-xs text-gray-500 mt-4 flex items-center justify-center gap-1.5">
                  <Info className="h-3.5 w-3.5" /> * Lower execution times indicate faster parallel computation.
                </div>
              </div>
            </div>
          </section>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-[#030712] py-8 text-center text-xs text-gray-500 mt-16">
        <p>© 2026 OptiGene Project — Parallel Computing Research. Created with Next.js & Tailwind CSS.</p>
      </footer>
    </div>
  );
}
