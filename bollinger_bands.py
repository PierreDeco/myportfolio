"""Bandes de Bollinger sur cloture journaliere.

La bande centrale est une moyenne mobile simple (SMA) sur `period` seances,
encadree par deux bandes paralleles a +/- k fois l'ecart-type glissant des
clotures sur la meme fenetre (definition standard des bandes de Bollinger).
"""

from __future__ import annotations

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


def compute_bollinger_bands(
    closes: pd.Series, period: int = 20, k: float = 2.0
) -> dict | None:
    """SMA glissante sur `period` seances, encadree par des bandes a +/- k*sigma.

    `sigma` est l'ecart-type glissant des clotures sur la meme fenetre que la
    SMA. Renvoie None si la serie est trop courte pour la fenetre demandee.
    """
    closes = closes.dropna()
    if period <= 1 or len(closes) < period:
        return None

    mid = closes.rolling(period).mean()
    sigma = closes.rolling(period).std()

    return {
        "dates": closes.index,
        "mid": mid.to_numpy(),
        "upper": (mid + k * sigma).to_numpy(),
        "lower": (mid - k * sigma).to_numpy(),
        "period": period,
        "k": k,
    }


# --------------------------------------------------------------------------
# Integration (GUI)
# --------------------------------------------------------------------------


def plot_bollinger_bands_on_axe(axe, bands: dict | None):
    """Trace les bandes de Bollinger (SMA + bandes) sur un axe existant.

    Ne cree pas sa propre figure : pense pour etre superpose au canvas de
    myportfolio.
    """
    if bands is None:
        return

    dates = bands["dates"]
    axe.plot(
        dates,
        bands["mid"],
        linestyle="-",
        linewidth=1.0,
        color="tab:purple",
        label=f"Bollinger MM{bands['period']}",
    )
    axe.plot(
        dates,
        bands["upper"],
        linestyle="--",
        linewidth=0.8,
        color="tab:purple",
        label=f"Bollinger ± {bands['k']:g}σ",
    )
    axe.plot(
        dates,
        bands["lower"],
        linestyle="--",
        linewidth=0.8,
        color="tab:purple",
    )


# --------------------------------------------------------------------------
# Trace (usage autonome)
# --------------------------------------------------------------------------


def plot_bands(closes: pd.Series, bands: dict | None):
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(closes.index, closes.values, linewidth=1, color="black", label="Cloture")
    plot_bollinger_bands_on_axe(ax, bands)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    closes = load_closes("AFX.DE", period="2y")
    bands = compute_bollinger_bands(closes, period=20, k=2.0)
    plot_bands(closes, bands)
    plt.show()
