"""MACD (Moving Average Convergence Divergence) sur cloture journaliere.

La ligne MACD est l'ecart entre deux moyennes mobiles exponentielles (EMA
rapide - EMA lente). Elle est encadree par sa propre EMA (la ligne de
signal), et leur ecart forme l'histogramme. Contrairement aux modeles
precedents, le MACD n'est pas dans l'unite du prix : il est destine a un
panneau separe, pas a une superposition directe sur le cours.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------
# Donnees (usage autonome)
# --------------------------------------------------------------------------


def load_closes(symbol: str, start=None, end=None, period: str = "2y") -> pd.Series:
    """Renvoie une Series de clotures indexee par date, sans MultiIndex."""
    df = yf.download(
        symbol,
        start=start,
        end=end,
        period=None if start else period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df["Close"].dropna()


# --------------------------------------------------------------------------
# Modele
# --------------------------------------------------------------------------


def compute_macd(
    closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> dict | None:
    """Ligne MACD (EMA rapide - EMA lente), sa ligne de signal (EMA de la
    ligne MACD) et leur ecart (histogramme).

    Renvoie None si les periodes sont invalides ou la serie trop courte.
    """
    closes = closes.dropna()
    if fast <= 0 or slow <= 0 or signal <= 0 or len(closes) < slow:
        return None

    fast_ema = closes.ewm(span=fast, adjust=False).mean()
    slow_ema = closes.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "dates": closes.index,
        "macd": macd_line.to_numpy(),
        "signal": signal_line.to_numpy(),
        "histogram": histogram.to_numpy(),
        "fast": fast,
        "slow": slow,
        "signal_period": signal,
    }


# --------------------------------------------------------------------------
# Integration (GUI)
# --------------------------------------------------------------------------


def plot_macd_on_axe(axe, macd: dict | None):
    """Trace le MACD (histogramme + ligne MACD + ligne signal) sur un axe
    existant. Pense pour un panneau dedie, pas une superposition sur le prix.
    """
    if macd is None:
        return

    dates = macd["dates"]
    histogram = macd["histogram"]
    colors = np.where(histogram >= 0, "tab:green", "tab:red")

    axe.axhline(0, color="black", linewidth=0.6, alpha=0.5)
    axe.bar(dates, histogram, width=0.8, color=colors, alpha=0.5, label="Histogramme")
    axe.plot(
        dates,
        macd["macd"],
        color="tab:blue",
        linewidth=1.0,
        label=f"MACD ({macd['fast']},{macd['slow']})",
    )
    axe.plot(
        dates,
        macd["signal"],
        color="tab:orange",
        linewidth=1.0,
        label=f"Signal ({macd['signal_period']})",
    )
    axe.set_ylabel("MACD")


# --------------------------------------------------------------------------
# Trace (usage autonome)
# --------------------------------------------------------------------------


def plot_macd(closes: pd.Series, macd: dict | None):
    fig, (ax_price, ax_macd) = plt.subplots(
        2, 1, figsize=(13, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    ax_price.plot(closes.index, closes.values, linewidth=1, color="black", label="Cloture")
    ax_price.legend()
    ax_price.grid(alpha=0.3)
    plot_macd_on_axe(ax_macd, macd)
    ax_macd.legend()
    ax_macd.grid(alpha=0.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    closes = load_closes("AFX.DE", period="2y")
    macd = compute_macd(closes, fast=12, slow=26, signal=9)
    plot_macd(closes, macd)
    plt.show()
