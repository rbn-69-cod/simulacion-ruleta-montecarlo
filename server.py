#!/usr/bin/env python3
"""
Servidor web interactivo para la presentación del proyecto de simulación Monte Carlo en ruleta europea.
Basado en Sarnecki (2026).
"""
import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import ctypes
import numpy as np
import pandas as pd

PORT = 8000
HERE = os.path.dirname(os.path.abspath(__file__))

# Cargar biblioteca compartida C
SO = os.path.join(HERE, "sim_kernel.so")
if not os.path.exists(SO):
    import subprocess
    subprocess.check_call(["gcc", "-O2", "-shared", "-fPIC", "-o", SO, os.path.join(HERE, "sim_kernel.c")])

lib = ctypes.CDLL(SO)
lib.run_scenario.argtypes = [ctypes.c_int] * 5 + [ctypes.c_uint64, ctypes.POINTER(ctypes.c_double)]

STRATS = ["Flat betting", "Martingale", "Fibonacci", "D'Alembert",
          "Labouchere", "Fixed-fractional", "Fractional Kelly"]

PAPER_DATA = {
    "Flat betting": {"mean": -24.1, "p_ruin": 1.8, "p_win": 23.0, "cvar95": -115, "cvar99": -149, "drawdown": 45},
    "Martingale": {"mean": -67.3, "p_ruin": 39.5, "p_win": 39.2, "cvar95": -636, "cvar99": -1000, "drawdown": 284},
    "Fibonacci": {"mean": -58.0, "p_ruin": 32.5, "p_win": 53.3, "cvar95": -634, "cvar99": -1000, "drawdown": 214},
    "D'Alembert": {"mean": -161.8, "p_ruin": 54.2, "p_win": 31.1, "cvar95": -1000, "cvar99": -1000, "drawdown": 362},
    "Labouchere": {"mean": -153.8, "p_ruin": 64.6, "p_win": 26.6, "cvar95": -1000, "cvar99": -1000, "drawdown": 479},
    "Fixed-fractional": {"mean": -150.1, "p_ruin": 5.1, "p_win": 17.7, "cvar95": -854, "cvar99": -945, "drawdown": 307},
    "Fractional Kelly": {"mean": -150.1, "p_ruin": 5.1, "p_win": 17.7, "cvar95": -854, "cvar99": -945, "drawdown": 307}
}

# Cargar resultados agregados existentes
agg_path = os.path.join(HERE, "resultados_agregados.csv")
if os.path.exists(agg_path):
    df_agg = pd.read_csv(agg_path)
else:
    df_agg = None

def simulate_trajectory(strat_idx, B0, limit, nspins, seed_val=42):
    """Simula una sola sesión y devuelve el vector paso a paso de Bankroll y Apuesta."""
    np.random.seed(seed_val)
    bankrolls = [B0]
    stakes = []
    outcomes = []
    B = float(B0)
    mart = 1
    da = 1
    fi = 0
    fib = [1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987]
    lab = [1, 2, 3, 4, 5, 6]
    ruined = False

    pwin = 18.0 / 37.0

    for t in range(nspins):
        if B < 1:
            ruined = True
            break
        if strat_idx == 0:
            s = 1
        elif strat_idx == 1:
            s = mart
        elif strat_idx == 2:
            s = fib[min(fi, 15)]
        elif strat_idx == 3:
            s = da
        elif strat_idx == 4:
            if len(lab) == 0:
                lab = [1, 2, 3, 4, 5, 6]
            s = lab[0] if len(lab) == 1 else lab[0] + lab[-1]
        else: # Fixed fractional / Kelly
            s = int(B * 0.02)
            if s < 1:
                s = 1
        
        if s > limit:
            s = limit
        if s > B:
            s = int(B)
        if s < 1:
            ruined = True
            break

        stakes.append(s)
        win = (np.random.rand() < pwin)
        outcomes.append(1 if win else 0)
        B += s if win else -s
        bankrolls.append(B)

        if strat_idx == 1:
            mart = 1 if win else mart * 2
        elif strat_idx == 2:
            if win:
                fi = max(0, fi - 2)
            else:
                fi = min(15, fi + 1)
        elif strat_idx == 3:
            if win:
                da = max(1, da - 1)
            else:
                da += 1
        elif strat_idx == 4:
            if win:
                if len(lab) >= 2:
                    lab = lab[1:-1]
                else:
                    lab = []
            else:
                if len(lab) < 100:
                    lab.append(s)

    return {
        "bankrolls": bankrolls,
        "stakes": stakes,
        "outcomes": outcomes,
        "ruined": ruined,
        "final_profit": B - B0
    }

class RouletteRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path == "/api/metrics":
            data = []
            if df_agg is not None:
                for _, row in df_agg.iterrows():
                    name = row["strategy"]
                    paper = PAPER_DATA.get(name, {})
                    data.append({
                        "strategy": name,
                        "mean_profit": float(row["mean_profit"]),
                        "median_profit": float(row["median_profit"]),
                        "p_profit": float(row["p_profit"]),
                        "p_ruin": float(row["p_ruin"]),
                        "VaR95": float(row["VaR95"]),
                        "CVaR95": float(row["CVaR95"]),
                        "VaR99": float(row["VaR99"]),
                        "CVaR99": float(row["CVaR99"]),
                        "avg_drawdown": float(row["avg_drawdown"]),
                        "avg_stake": float(row["avg_stake"]),
                        "paper_mean": paper.get("mean", 0),
                        "paper_p_ruin": paper.get("p_ruin", 0),
                        "paper_p_win": paper.get("p_win", 0),
                        "paper_cvar95": paper.get("cvar95", 0),
                        "paper_drawdown": paper.get("drawdown", 0)
                    })
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": data}).encode('utf-8'))
            return

        elif path == "/api/trajectory":
            qs = urllib.parse.parse_qs(url.query)
            strat = int(qs.get("strat", [0])[0])
            b0 = int(qs.get("b0", [500])[0])
            limit = int(qs.get("limit", [128])[0])
            spins = int(qs.get("spins", [200])[0])
            seed = int(qs.get("seed", [np.random.randint(1, 100000)])[0])

            traj = simulate_trajectory(strat, b0, limit, spins, seed)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "strategy": STRATS[strat], "data": traj}).encode('utf-8'))
            return

        elif path == "/api/simulate_custom":
            qs = urllib.parse.parse_qs(url.query)
            strat = int(qs.get("strat", [0])[0])
            b0 = int(qs.get("b0", [200])[0])
            limit = int(qs.get("limit", [64])[0])
            spins = int(qs.get("spins", [500])[0])
            nsess = int(qs.get("nsess", [2000])[0])

            out = np.empty((nsess, 4), dtype=np.float64)
            lib.run_scenario(strat, b0, limit, spins, nsess, np.random.randint(1, 1000000),
                             out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
            profits = out[:, 0]
            ruined = out[:, 1]
            drawdowns = out[:, 2]
            stakes = out[:, 3]

            v95 = float(np.quantile(profits, 0.05))
            c95 = float(profits[profits <= v95].mean())
            
            # Histograma para gráfico
            hist, bin_edges = np.histogram(profits, bins=30)
            bin_centers = [(bin_edges[i] + bin_edges[i+1])/2 for i in range(len(hist))]

            res = {
                "strategy": STRATS[strat],
                "mean_profit": round(float(profits.mean()), 2),
                "median_profit": round(float(np.median(profits)), 2),
                "p_win": round(float((profits > 0).mean() * 100), 2),
                "p_ruin": round(float(ruined.mean() * 100), 2),
                "avg_drawdown": round(float(drawdowns.mean()), 2),
                "avg_stake": round(float(stakes.mean()), 2),
                "var95": round(v95, 2),
                "cvar95": round(c95, 2),
                "hist_counts": hist.tolist(),
                "hist_bins": [round(b, 1) for b in bin_centers],
                "sample_size": nsess
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "data": res}).encode('utf-8'))
            return

        super().do_GET()

def run_server():
    os.chdir(HERE)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RouletteRequestHandler) as httpd:
        print(f"\n========================================================")
        print(f" Servidor iniciado con éxito para la exposición:")
        print(f" URL: http://localhost:{PORT}")
        print(f" Directorio: {HERE}")
        print(f"========================================================\n", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")

if __name__ == "__main__":
    run_server()

