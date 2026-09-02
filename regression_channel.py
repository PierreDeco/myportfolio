"""Canal de regression lineaire sur cloture journaliere.

La tendance est une droite des moindres carres (OLS) ajustee sur une fenetre
glissante des N dernieres seances, encadree par deux bandes paralleles a
+/- k fois l'ecart-type des residus (canal de regression classique en
analyse technique).
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


def compute_regression_channel(
    closes: pd.Series, lookback: int = 60, k: float = 2.0
) -> dict | None:
    """Ajuste une droite OLS sur les `lookback` dernieres seances de `closes`.

    Renvoie None si la fenetre est trop petite pour etre ajustee. Sinon un
    dict avec les dates de la fenetre, la droite centrale, les deux bandes
    (centre +/- k*sigma) et les parametres de la droite.
    """
    closes = closes.dropna()
    if lookback <= 1 or len(closes) < 2:
        return None

    window = closes.iloc[-lookback:] if lookback < len(closes) else closes
    x = np.arange(len(window))
    y = window.to_numpy(dtype=float)

    slope, intercept = np.polyfit(x, y, 1)
    center = slope * x + intercept
    sigma = float((y - center).std())

    return {
        "dates": window.index,
        "center": center,
        "upper": center + k * sigma,
        "lower": center - k * sigma,
        "slope": float(slope),
        "intercept": float(intercept),
        "sigma": sigma,
        "k": k,
    }


# --------------------------------------------------------------------------
# Integration (GUI)
# --------------------------------------------------------------------------


def plot_regression_channel_on_axe(axe, channel: dict | None):
    """Trace le canal de regression (droite + bandes) sur un axe existant.

    Ne cree pas sa propre figure : pense pour etre superpose au canvas de
    myportfolio.
    """
    if channel is None:
        return

    dates = channel["dates"]
    axe.plot(
        dates,
        channel["center"],
        linestyle="-",
        linewidth=1.2,
        color="tab:orange",
        label="Régression (tendance)",
    )
    axe.plot(
        dates,
        channel["upper"],
        linestyle="--",
        linewidth=1.0,
        color="tab:orange",
        label=f"Canal ± {channel['k']:g}σ",
    )
    axe.plot(
        dates,
        channel["lower"],
        linestyle="--",
        linewidth=1.0,
        color="tab:orange",
    )


# --------------------------------------------------------------------------
# Trace (usage autonome)
# --------------------------------------------------------------------------


def plot_channel(closes: pd.Series, channel: dict | None):
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(closes.index, closes.values, linewidth=1, color="black", label="Cloture")
    plot_regression_channel_on_axe(ax, channel)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    closes = load_closes("AFX.DE", period="2y")
    channel = compute_regression_channel(closes, lookback=60, k=2.0)
    plot_channel(closes, channel)
    plt.show()
