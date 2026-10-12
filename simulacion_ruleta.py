"""
Replicación: "Comparison of the effectiveness of roulette betting strategies
using Monte Carlo simulation" (Sarnecki, JCSI 40, 2026, 232-238).

Ruleta europea, apuesta rojo/negro (p = 18/37).
7 estrategias x 48 escenarios (4 bankrolls x 4 límites de mesa x 3 duraciones)
x 10 000 sesiones = 3 360 000 sesiones.

Supuestos propios (el artículo no los detalla):
  - Apuesta base = 1 unidad; apuesta limitada por min(límite de mesa, bankroll).
  - Ruina = bankroll < 1 (no puede poner la apuesta mínima).
  - Fixed-fractional: 2 % del bankroll, redondeado a entero, mínimo 1.
  - Fractional Kelly: p_est = 0.52, f = 0.5 * (2p-1) = 0.02 (igual que el paper).
  - Labouchere: secuencia inicial [1,2,3,4,5,6].

El núcleo de simulación está en sim_kernel.c (se compila solo con gcc).
Uso:  python simulacion_ruleta.py [sesiones_por_escenario]
"""
import sys, os, ctypes, subprocess, itertools
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SO = os.path.join(HERE, "sim_kernel.so")
if not os.path.exists(SO):
    subprocess.check_call(["gcc", "-O2", "-shared", "-fPIC", "-o", SO,
                           os.path.join(HERE, "sim_kernel.c")])
_lib = ctypes.CDLL(SO)
_lib.run_scenario.argtypes = [ctypes.c_int] * 5 + [ctypes.c_uint64, ctypes.POINTER(ctypes.c_double)]

STRATS = ["Flat betting", "Martingale", "Fibonacci", "D'Alembert",
          "Labouchere", "Fixed-fractional", "Fractional Kelly"]


def run_scenario(strat, B0, limit, nspins, nsess, seed0):
    out = np.empty((nsess, 4))
    _lib.run_scenario(strat, B0, limit, nspins, nsess, seed0,
                      out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
    return out


def cvar(x, q):
    v = np.quantile(x, 1 - q)
    return v, x[x <= v].mean()


def main(nsess=10_000):
    bankrolls = [100, 200, 500, 1000]; limits = [32, 64, 128, 256]; spins = [200, 500, 2000]
    rows = []; all_profits = {s: [] for s in range(7)}
    for si, name in enumerate(STRATS):
        for sc, (B0, lim, n) in enumerate(itertools.product(bankrolls, limits, spins)):
            o = run_scenario(si, B0, lim, n, nsess, 1_000_000 * (si + 1) + 10_000 * sc)
            all_profits[si].append(o[:, 0])
            rows.append(dict(strategy=name, bankroll=B0, table_limit=lim, max_spins=n,
                             mean_profit=o[:, 0].mean(), median_profit=np.median(o[:, 0]),
                             p_profit=(o[:, 0] > 0).mean(), p_ruin=o[:, 1].mean(),
                             avg_drawdown=o[:, 2].mean(), avg_stake=o[:, 3].mean()))
        print("listo:", name, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv("resultados_por_escenario.csv", index=False)

    agg = []
    for si, name in enumerate(STRATS):
        x = np.concatenate(all_profits[si]); d = df[df.strategy == name]
        v95, c95 = cvar(x, .95); v99, c99 = cvar(x, .99)
        agg.append(dict(strategy=name, mean_profit=x.mean(), median_profit=np.median(x),
                        p_profit=(x > 0).mean() * 100, p_ruin=d.p_ruin.mean() * 100,
                        VaR95=v95, CVaR95=c95, VaR99=v99, CVaR99=c99,
                        avg_drawdown=d.avg_drawdown.mean(), avg_stake=d.avg_stake.mean()))
    agg = pd.DataFrame(agg).round(2)
    agg.to_csv("resultados_agregados.csv", index=False)
    print(agg.to_string(index=False))

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    ax[0].bar(agg.strategy, agg.mean_profit); ax[0].set_title("Ganancia media [u.]")
    ax[1].bar(agg.strategy, agg.p_profit); ax[1].set_title("Prob. de ganancia [%]")
    ax[2].bar(agg.strategy, agg.p_ruin); ax[2].set_title("Prob. de ruina [%]")
    for a in ax:
        a.tick_params(axis="x", rotation=60)
    plt.tight_layout(); plt.savefig("figura_resultados.png", dpi=150)

    from scipy import stats
    flat = np.concatenate(all_profits[0])
    for si in (1, 2, 4):
        x = np.concatenate(all_profits[si])
        u = stats.mannwhitneyu(x, flat)
        print(f"{STRATS[si]} vs Flat: Mann-Whitney U p = {u.pvalue:.3g}")
    for si, name in enumerate(STRATS):
        x = np.concatenate(all_profits[si])
        k2, p = stats.normaltest(x)
        print(f"{name}: skew={stats.skew(x):.2f} kurt={stats.kurtosis(x):.2f} p={p:.3g}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10_000)
