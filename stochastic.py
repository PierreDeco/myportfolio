"""Oscillateur stochastique sur cloture journaliere.

Le %K brut situe la cloture du jour dans l'amplitude (plus haut - plus bas)
des `k_period` dernieres seances : 100 % si la cloture est sur le plus haut
de la fenetre, 0 % si elle est sur le plus bas. Le %K affiche est ce %K brut
lisse par une moyenne mobile simple sur `smooth_k` seances (stochastique
"lent", convention la plus repandue), et le %D est la moyenne mobile simple
du %K sur `d_period` seances. L'oscillateur n'est pas dans l'unite du prix
(il est borne entre 0 et 100) : superpose au cours, il l'est via son propre
axe secondaire.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


# --------------------------------------------------------------------------
# Donnees (usage autonome)
# --------------------------------------------------------------------------


def load_ohlc(symbol: str, start=None, end=None, period: str = "2y") -> pd.DataFrame:
    """Renvoie un DataFrame High/Low/Close indexe par date, sans MultiIndex."""
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
    return df[["High", "Low", "Close"]].dropna()


# --------------------------------------------------------------------------
# Modele
# --------------------------------------------------------------------------


def compute_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    smooth_k: int = 3,
    d_period: int = 3,
) -> dict | None:
    """%K lisse (stochastique lent) et sa moyenne mobile %D.

    `k_period` est la fenetre glissante du plus haut/plus bas servant au %K
    brut, `smooth_k` lisse ce %K brut, et `d_period` moyenne le %K lisse pour
    obtenir le %D. Renvoie None si les periodes sont invalides ou la serie
    trop courte.
    """
    if k_period <= 0 or smooth_k <= 0 or d_period <= 0 or len(close) < k_period:
        return None

    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    percent_k = raw_k.rolling(smooth_k).mean() if smooth_k > 1 else raw_k
    percent_d = percent_k.rolling(d_period).mean()

    return {
        "dates": close.index,
        "percent_k": percent_k.to_numpy(),
        "percent_d": percent_d.to_numpy(),
        "k_period": k_period,
        "smooth_k": smooth_k,
        "d_period": d_period,
    }


# --------------------------------------------------------------------------
# Integration (GUI)
# --------------------------------------------------------------------------


def plot_stochastic_on_axe(axe, stoch: dict | None):
    """Superpose %K et %D (avec les seuils 20/80) sur un axe existant, via
    un axe secondaire (echelle 0-100, sans rapport avec l'unite du prix) —
    meme principe que l'overlay de volume. Ne cree pas sa propre figure.
    Renvoie l'axe secondaire (pour fusionner sa legende avec celle du prix),
    ou None si `stoch` est vide.
    """
    if stoch is None:
        return None

    dates = stoch["dates"]
    stoch_axe = axe.twinx()
    stoch_axe.axhline(80, color="tab:red", linewidth=0.6, linestyle="--", alpha=0.5)
    stoch_axe.axhline(20, color="tab:green", linewidth=0.6, linestyle="--", alpha=0.5)
    stoch_axe.plot(
        dates,
        stoch["percent_k"],
        color="tab:blue",
        linewidth=1.0,
        label=f"%K ({stoch['k_period']},{stoch['smooth_k']})",
    )
    stoch_axe.plot(
        dates,
        stoch["percent_d"],
        color="tab:orange",
        linewidth=1.0,
        label=f"%D ({stoch['d_period']})",
    )
    stoch_axe.set_ylim(0, 100)
    stoch_axe.set_ylabel("Stochastique")
    return stoch_axe


# --------------------------------------------------------------------------
# Trace (usage autonome)
# --------------------------------------------------------------------------


def plot_stochastic(ohlc: pd.DataFrame, stoch: dict | None):
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(ohlc.index, ohlc["Close"], linewidth=1, color="black", label="Cloture")
    stoch_axe = plot_stochastic_on_axe(ax, stoch)
    handles, labels = ax.get_legend_handles_labels()
    if stoch_axe is not None:
        extra_handles, extra_labels = stoch_axe.get_legend_handles_labels()
        handles += extra_handles
        labels += extra_labels
    ax.legend(handles, labels)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    ohlc = load_ohlc("AFX.DE", period="2y")
    stoch = compute_stochastic(
        ohlc["High"], ohlc["Low"], ohlc["Close"], k_period=14, smooth_k=3, d_period=3
    )
    plot_stochastic(ohlc, stoch)
    plt.show()
