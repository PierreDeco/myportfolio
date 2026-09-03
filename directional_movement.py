"""Mouvement directionnel (+DI, -DI, ADX) sur cloture journaliere, methode
de Wilder.

+DM et -DM captent, seance par seance, quel cote (haussier ou baissier) a
domine le mouvement des extremes (plus haut / plus bas) du jour. Lisses par
la moyenne mobile de Wilder sur `period` seances et rapportes au True Range
lui-meme lisse, ils donnent +DI et -DI (0-100) : la part du mouvement
directionnel attribuable a chaque sens. Leur ecart relatif (DX), lisse a son
tour par la moyenne de Wilder, donne l'ADX (0-100), qui mesure la force de
la tendance sans en indiquer le sens — un ADX au-dessus de 25 signale
generalement une tendance etablie. +DI, -DI et l'ADX ne sont pas dans
l'unite du prix.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

ADX_TREND_THRESHOLD = 25


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


def _wilder_smoothing(series: pd.Series, period: int) -> pd.Series:
    """Moyenne mobile de Wilder (RMA) : la generalisation en EMA de facteur
    de lissage 1/period, methode d'origine du DMI/ADX."""
    return series.ewm(alpha=1 / period, adjust=False).mean()


def compute_directional_movement(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> dict | None:
    """+DI, -DI et ADX sur une fenetre de lissage de Wilder `period`.

    Renvoie None si la periode est invalide ou la serie trop courte.
    """
    if period <= 0 or len(close) < period + 1:
        return None

    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=close.index,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=close.index,
    )

    true_range = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    smoothed_tr = _wilder_smoothing(true_range, period)
    smoothed_plus_dm = _wilder_smoothing(plus_dm, period)
    smoothed_minus_dm = _wilder_smoothing(minus_dm, period)

    plus_di = 100 * smoothed_plus_dm / smoothed_tr
    minus_di = 100 * smoothed_minus_dm / smoothed_tr

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = _wilder_smoothing(dx, period)

    return {
        "dates": close.index,
        "plus_di": plus_di.to_numpy(),
        "minus_di": minus_di.to_numpy(),
        "adx": adx.to_numpy(),
        "period": period,
    }


# --------------------------------------------------------------------------
# Integration (GUI)
# --------------------------------------------------------------------------


def plot_directional_movement_on_axe(axe, dmi: dict | None):
    """Superpose +DI (vert), -DI (rouge) et l'ADX (avec le repere a 25) sur
    un axe existant, via un axe secondaire (echelle 0-100, sans rapport avec
    l'unite du prix) — meme principe que l'overlay de volume. Ne cree pas sa
    propre figure. Renvoie l'axe secondaire (pour fusionner sa legende avec
    celle du prix), ou None si `dmi` est vide.
    """
    if dmi is None:
        return None

    dates = dmi["dates"]
    dmi_axe = axe.twinx()
    dmi_axe.plot(
        dates,
        dmi["plus_di"],
        color="green",
        linewidth=1.0,
        label=f"+DI ({dmi['period']})",
    )
    dmi_axe.plot(
        dates,
        dmi["minus_di"],
        color="red",
        linewidth=1.0,
        label=f"-DI ({dmi['period']})",
    )
    dmi_axe.plot(
        dates,
        dmi["adx"],
        color="black",
        linewidth=1.3,
        label=f"ADX ({dmi['period']})",
    )
    dmi_axe.axhline(
        ADX_TREND_THRESHOLD, color="black", linewidth=0.6, linestyle="--", alpha=0.5
    )
    dmi_axe.set_ylim(0, 100)
    dmi_axe.set_ylabel("DMI / ADX")
    return dmi_axe


# --------------------------------------------------------------------------
# Trace (usage autonome)
# --------------------------------------------------------------------------


def plot_directional_movement(ohlc: pd.DataFrame, dmi: dict | None):
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(ohlc.index, ohlc["Close"], linewidth=1, color="black", label="Cloture")
    dmi_axe = plot_directional_movement_on_axe(ax, dmi)
    handles, labels = ax.get_legend_handles_labels()
    if dmi_axe is not None:
        extra_handles, extra_labels = dmi_axe.get_legend_handles_labels()
        handles += extra_handles
        labels += extra_labels
    ax.legend(handles, labels)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    ohlc = load_ohlc("AFX.DE", period="2y")
    dmi = compute_directional_movement(ohlc["High"], ohlc["Low"], ohlc["Close"], period=14)
    plot_directional_movement(ohlc, dmi)
    plt.show()
