# import json
# import requests
from matplotlib import text
import pandas as pd
import yfinance as yf
from tkinter import BooleanVar, StringVar, Tk, Listbox, ttk, messagebox as tk_messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
from matplotlib.ticker import AutoMinorLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mplfinance as mpf
import customtkinter as ctk

import regression_channel
import bollinger_bands
import macd as macd_module

# ___
# Defining constants

POSSIBLE_MAV = ["10", "20", "50", "100", "200"]
POSSIBLE_INTERVALS = ["1d", "1wk", "1mo", "6mo", "1y", "2y", "5y", "10y"]
POSSIBLE_PLOT_TYPES = ["candle", "line", "pnf", "renko"]


def main():
    # User interface setup, starting with the basic widgets
    root = Tk()
    symbol = StringVar()
    start_date = StringVar()
    end_date = StringVar()
    interval = StringVar()
    plot_type = StringVar()
    mav = StringVar(value=POSSIBLE_MAV)
    show_regression_channel = BooleanVar(value=False)
    regression_lookback = StringVar(value="60")
    regression_k = StringVar(value="2.0")
    show_bollinger_bands = BooleanVar(value=False)
    bollinger_period = StringVar(value="20")
    bollinger_k = StringVar(value="2.0")
    show_volume = BooleanVar(value=False)
    show_macd = BooleanVar(value=False)
    macd_fast = StringVar(value="12")
    macd_slow = StringVar(value="26")
    macd_signal = StringVar(value="9")
    root.title("MyPortfolio : Personal Stock Technical Analysis")
    frame = ttk.Frame(root, relief="ridge", padding=5)
    plot_frame = ttk.Frame(root, padding=5)
    quit_button = ttk.Button(frame, text="Quit", command=root.destroy)
    symbol_label = ttk.Label(frame, text="Enter stock symbol:")
    symbol_entry = ttk.Entry(frame, textvariable=symbol)
    start_date_label = ttk.Label(frame, text="Start date (YYYY-MM-DD):")
    start_date_entry = ttk.Entry(frame, state="disabled", textvariable=start_date)
    end_date_label = ttk.Label(frame, text="End date (YYYY-MM-DD):")
    end_date_entry = ttk.Entry(frame, state="disabled", textvariable=end_date)
    interval_label = ttk.Label(frame, text="Select interval:")
    interval_combobox = ttk.Combobox(
        frame, values=POSSIBLE_INTERVALS, state="readonly", textvariable=interval
    )
    intervalswitch = ctk.CTkSwitch(
        frame,
        text="Interval ?",
        command=lambda: invert_activation(
            interval_combobox, start_date_entry, end_date_entry
        ),
    )
    intervalswitch.select()

    # ___
    # Starting the plot type part

    plot_type_box = ttk.Combobox(
        frame, values=POSSIBLE_PLOT_TYPES, state="readonly", textvariable=plot_type
    )
    plot_type_label = ttk.Label(frame, text="Select plot type:")

    # Now the moving average part
    mav_listbox = Listbox(
        frame,
        listvariable=mav,
        selectmode="multiple",
        height=5,
    )
    mav_listbox.bind(
        "<<ListboxSelect>>",
        lambda event: (update_mav_tuple(mav_listbox), render()),
    )
    mav_label = ttk.Label(frame, text="Select moving average:")

    # Trend line model : linear regression channel
    regression_channel_frame = ttk.LabelFrame(frame, text="Tendance")
    regression_channel_checkbox = ttk.Checkbutton(
        regression_channel_frame, text="Activer", variable=show_regression_channel
    )
    regression_lookback_label = ttk.Label(regression_channel_frame, text="lookback :")
    regression_lookback_spin = ttk.Spinbox(
        regression_channel_frame,
        from_=5,
        to=500,
        increment=5,
        width=5,
        textvariable=regression_lookback,
    )
    regression_k_label = ttk.Label(regression_channel_frame, text="k (canal) :")
    regression_k_spin = ttk.Spinbox(
        regression_channel_frame,
        from_=0.1,
        to=5.0,
        increment=0.1,
        width=5,
        textvariable=regression_k,
    )

    # Bollinger bands model : SMA +/- k*sigma glissant
    bollinger_bands_frame = ttk.LabelFrame(frame, text="Bandes de Bollinger")
    bollinger_bands_checkbox = ttk.Checkbutton(
        bollinger_bands_frame, text="Activer", variable=show_bollinger_bands
    )
    bollinger_period_label = ttk.Label(bollinger_bands_frame, text="période (MM) :")
    bollinger_period_spin = ttk.Spinbox(
        bollinger_bands_frame,
        from_=2,
        to=200,
        increment=1,
        width=5,
        textvariable=bollinger_period,
    )
    bollinger_k_label = ttk.Label(bollinger_bands_frame, text="k (bandes) :")
    bollinger_k_spin = ttk.Spinbox(
        bollinger_bands_frame,
        from_=0.1,
        to=5.0,
        increment=0.1,
        width=5,
        textvariable=bollinger_k,
    )

    # Volume overlay : no tunable parameter, plain checkbox
    volume_checkbox = ttk.Checkbutton(
        frame, text="Afficher les volumes", variable=show_volume
    )

    # MACD model : EMA(fast) - EMA(slow), signal EMA, drawn in its own panel
    macd_frame = ttk.LabelFrame(frame, text="MACD")
    macd_checkbox = ttk.Checkbutton(macd_frame, text="Activer", variable=show_macd)
    macd_fast_label = ttk.Label(macd_frame, text="rapide :")
    macd_fast_spin = ttk.Spinbox(
        macd_frame, from_=1, to=100, increment=1, width=5, textvariable=macd_fast
    )
    macd_slow_label = ttk.Label(macd_frame, text="lente :")
    macd_slow_spin = ttk.Spinbox(
        macd_frame, from_=2, to=300, increment=1, width=5, textvariable=macd_slow
    )
    macd_signal_label = ttk.Label(macd_frame, text="signal :")
    macd_signal_spin = ttk.Spinbox(
        macd_frame, from_=1, to=100, increment=1, width=5, textvariable=macd_signal
    )

    # Drawing the canvas using matplotlib's explicit method

    fig, ax = plt.subplots(figsize=(7, 3.3))
    canvas = FigureCanvasTkAgg(fig, plot_frame)
    toolbar = NavigationToolbar2Tk(canvas, plot_frame, pack_toolbar=False)
    toolbar.update()
    # TODO: adding the MACD
    # TODO: adding the infos of the company
    # TODO: adding the technical indicators such as RSI, Bollinger Bands, with tooltips

    # Last successfully fetched data, kept around so display-only changes
    # (checkboxes, spinboxes, plot type, moving averages) can redraw the
    # chart without hitting yfinance again.
    state = {"ochl_data": None, "symbol": None}

    def render():
        """Redraws the chart from cached data. No-op before the first
        successful Analyze click, since there is nothing to draw yet."""
        if state["ochl_data"] is None:
            return
        render_chart(
            canvas,
            state["ochl_data"],
            state["symbol"],
            plot_type.get(),
            update_mav_tuple(mav_listbox),
            show_regression_channel.get(),
            {
                "lookback": regression_lookback.get(),
                "k": regression_k.get(),
            },
            show_bollinger_bands.get(),
            {
                "period": bollinger_period.get(),
                "k": bollinger_k.get(),
            },
            show_volume.get(),
            show_macd.get(),
            {
                "fast": macd_fast.get(),
                "slow": macd_slow.get(),
                "signal": macd_signal.get(),
            },
        )

    def do_analyze():
        """Fetches fresh data from yfinance, caches it, then renders."""
        if plot_type.get() == "":
            tk_messagebox.showerror(title="Error", message="Invalid plot type")
            return
        ochl_data = fetch_ochl_data(
            symbol_entry.get(),
            start_date.get(),
            end_date.get(),
            interval.get(),
            intervalswitch.get(),
        )
        if ochl_data is None:
            return
        state["ochl_data"] = ochl_data
        state["symbol"] = symbol_entry.get()
        render()

    # The analysis button that will trigger the stock analysis when clicked

    analysis_button = ttk.Button(frame, text="Analyze", command=do_analyze)

    # Once data has been fetched at least once, any display-option change
    # refreshes the chart immediately, without needing another Analyze click.
    regression_channel_checkbox.configure(command=render)
    bollinger_bands_checkbox.configure(command=render)
    volume_checkbox.configure(command=render)
    macd_checkbox.configure(command=render)
    plot_type_box.bind("<<ComboboxSelected>>", lambda event: render())
    for spin in (
        regression_lookback_spin,
        regression_k_spin,
        bollinger_period_spin,
        bollinger_k_spin,
        macd_fast_spin,
        macd_slow_spin,
        macd_signal_spin,
    ):
        spin.configure(command=render)
        spin.bind("<Return>", lambda event: render())
        spin.bind("<FocusOut>", lambda event: render())

    # Positioning the widgets in the grid

    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    frame.grid(row=0, column=0, sticky="nsew")
    plot_frame.grid(row=1, column=0, sticky="nsew")
    plot_frame.rowconfigure(1, weight=1)
    plot_frame.columnconfigure(0, weight=1)
    start_date_label.grid(row=1, column=0, sticky="w")
    start_date_entry.grid(row=1, column=1, sticky="w")
    end_date_label.grid(row=2, column=0, sticky="w")
    end_date_entry.grid(row=2, column=1, sticky="w")
    intervalswitch.grid(row=1, column=2, sticky="w")
    symbol_entry.grid(row=0, column=1, sticky="w")
    symbol_label.grid(row=0, column=0, sticky="w")
    interval_label.grid(row=0, column=2, sticky="w")
    interval_combobox.grid(row=0, column=3, sticky="w")
    quit_button.grid(row=7, column=1, sticky="w")
    analysis_button.grid(row=7, column=0, sticky="w")
    plot_type_label.grid(row=2, column=2, sticky="w")
    plot_type_box.grid(row=2, column=3, sticky="w")
    regression_channel_frame.grid(row=3, column=0, columnspan=4, sticky="w")
    regression_channel_checkbox.grid(row=0, column=0, sticky="w")
    regression_lookback_label.grid(row=0, column=1, sticky="w")
    regression_lookback_spin.grid(row=0, column=2, sticky="w")
    regression_k_label.grid(row=0, column=3, sticky="w")
    regression_k_spin.grid(row=0, column=4, sticky="w")
    bollinger_bands_frame.grid(row=4, column=0, columnspan=4, sticky="w")
    bollinger_bands_checkbox.grid(row=0, column=0, sticky="w")
    bollinger_period_label.grid(row=0, column=1, sticky="w")
    bollinger_period_spin.grid(row=0, column=2, sticky="w")
    bollinger_k_label.grid(row=0, column=3, sticky="w")
    bollinger_k_spin.grid(row=0, column=4, sticky="w")
    volume_checkbox.grid(row=5, column=0, sticky="w")
    macd_frame.grid(row=6, column=0, columnspan=4, sticky="w")
    macd_checkbox.grid(row=0, column=0, sticky="w")
    macd_fast_label.grid(row=0, column=1, sticky="w")
    macd_fast_spin.grid(row=0, column=2, sticky="w")
    macd_slow_label.grid(row=0, column=3, sticky="w")
    macd_slow_spin.grid(row=0, column=4, sticky="w")
    macd_signal_label.grid(row=0, column=5, sticky="w")
    macd_signal_spin.grid(row=0, column=6, sticky="w")
    mav_label.grid(row=0, column=4, sticky="w")
    mav_listbox.grid(row=0, column=5, sticky="w", rowspan=3)
    toolbar.grid(row=0, column=0, sticky="w")
    canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
    symbol_entry.focus()
    root.mainloop()

    # This analyse_stock function will plot the chart with the specified
    # parameters using yfinance to fetch the data and matplotlib to plot the
    # chart.


def fetch_ochl_data(symbol, start, end, interval, switch):
    """Fetches OHLCV data from yfinance. This is the only step that hits the
    network ; returns None (after showing an error) on invalid input or no
    data found, so the caller can bail out without touching the chart.
    """
    # TODO : All the sanity checks for the inputs
    if symbol == "":
        tk_messagebox.showerror(title="Error", message="Invalid symbol")
        return None
    if switch == 1:
        if interval == "":
            tk_messagebox.showerror("Error", message="Invalid interval")
            return None
        ochl_data = yf.Ticker(symbol).history(period=interval)
    else:
        if start == "" or end == "":
            tk_messagebox.showerror("Error", message="Invalid start and/or end dates")
            return None
        ochl_data = yf.Ticker(symbol).history(start=start, end=end)
    if ochl_data.empty:
        tk_messagebox.showerror(title="Error", message=f"No data found for {symbol}")
        print(f"No data found for symbol: {symbol}")
        return None
    print(ochl_data)
    return ochl_data


def render_chart(
    canvas,
    ochl_data,
    symbol,
    style,
    mav,
    show_regression_channel=False,
    regression_params=None,
    show_bollinger_bands=False,
    bollinger_params=None,
    show_volume=False,
    show_macd=False,
    macd_params=None,
):
    """Draws the chart from already-fetched data. Does no network call, so
    it can be re-run on every display-option change (checkboxes, spinboxes,
    plot type, moving averages) without re-fetching from yfinance.
    """
    canvas.figure.clear()
    if show_macd:
        axe, macd_axe = canvas.figure.subplots(
            2, 1, sharex=True, gridspec_kw={"height_ratios": [3, 1]}
        )
    else:
        axe = canvas.figure.subplots()
        macd_axe = None

    axe.set_title(f"{symbol}")
    axe.set_ylabel("Price")

    extra_axes = []
    if show_volume:
        extra_axes.append(plot_volume(axe, ochl_data))
    if style == "candle":
        plot_candle(axe, ochl_data)
    elif style == "line":
        plot_line(axe, ochl_data)
    for mean in mav:
        plot_mav(axe, ochl_data, mean)
    if show_regression_channel:
        plot_regression_channel(axe, ochl_data, regression_params or {})
    if show_bollinger_bands:
        plot_bollinger_bands(axe, ochl_data, bollinger_params or {})

    if macd_axe is not None:
        axe.set_xlabel("")
        configure_axes(axe, show_xticklabels=False)
        draw_legend(axe, extra_axes=extra_axes)
        plot_macd(macd_axe, ochl_data, macd_params or {})
        macd_axe.set_xlabel("Date")
        configure_axes(macd_axe, show_xticklabels=True)
        draw_legend(macd_axe)
    else:
        axe.set_xlabel("Date")
        configure_axes(axe, show_xticklabels=True)
        draw_legend(axe, extra_axes=extra_axes)

    canvas.draw()
    return


def configure_axes(axe, show_xticklabels=True):
    """Adds minor ticks (linear scale) on the y-axis, extends both major and
    minor ticks as thin gridlines. When `show_xticklabels` is true (the
    axis is the bottom-most panel), also tilts the x-axis (date) labels by
    30° ; otherwise hides them, since a shared, MACD-panel-style x-axis only
    needs its labels on the bottom panel. The x-axis keeps only its default
    (major) ticks."""
    axe.yaxis.set_minor_locator(AutoMinorLocator())
    axe.grid(which="major", linewidth=0.6, alpha=0.6)
    axe.grid(which="minor", linewidth=0.4, alpha=0.4)
    if show_xticklabels:
        for label in axe.get_xticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment("right")
    else:
        axe.tick_params(labelbottom=False)


def draw_legend(axe, extra_axes=()):
    """Merges legend entries from `axe` and any axis overlaid on top of it
    (e.g. the volume twin axis) into a single legend on `axe`."""
    handles, labels = axe.get_legend_handles_labels()
    for a in extra_axes:
        h, l = a.get_legend_handles_labels()
        handles += h
        labels += l
    axe.legend(handles, labels)


def plot_volume(axe, ochl_data):
    """Overlays exchanged volume as semi-transparent bars on a secondary
    y-axis, anchored to the bottom quarter of the chart so it doesn't
    interfere with the price series. Drawn behind the price axis. Returns
    the twin axis so its legend entry can be merged with the price axis's.
    """
    volume = ochl_data["Volume"]
    vol_axe = axe.twinx()
    vol_axe.set_zorder(axe.get_zorder() - 1)
    axe.patch.set_visible(False)
    vol_axe.bar(
        ochl_data.index,
        volume,
        width=0.8,
        color="tab:gray",
        alpha=0.3,
        label="Volume",
    )
    max_volume = volume.max()
    vol_axe.set_ylim(0, max_volume * 4 if max_volume > 0 else 1)
    vol_axe.set_ylabel("Volume")
    return vol_axe


def plot_candle(axe, ochl_data):
    up = ochl_data[ochl_data.Close >= ochl_data.Open]
    down = ochl_data[ochl_data.Close < ochl_data.Open]
    col1 = "green"
    col2 = "red"
    width = 0.8
    width2 = 0.08
    axe.bar(up.index, up.Close - up.Open, width, bottom=up.Open, color=col1)
    axe.bar(up.index, up.High - up.Close, width2, bottom=up.Close, color=col1)
    axe.bar(up.index, up.Low - up.Open, width2, bottom=up.Open, color=col1)

    axe.bar(down.index, down.Close - down.Open, width, bottom=down.Open, color=col2)
    axe.bar(down.index, down.High - down.Open, width2, bottom=down.Open, color=col2)
    axe.bar(down.index, down.Low - down.Close, width2, bottom=down.Close, color=col2)


def plot_line(axe, ochl_data):
    col = "blue"
    axe.plot(
        ochl_data.index,
        ochl_data["Close"],
        label="Symbol price (line)",
        color=col,
        linewidth=0.8,
    )


def plot_mav(axe, ochl_data, mav):
    axe.plot(
        ochl_data.index, mm(ochl_data, mav), label=f"MAV : {mav} periods", linewidth=0.8
    )


def plot_regression_channel(axe, ochl_data, params):
    """OLS regression channel over a trailing lookback window.
    See regression_channel.py for the full model. Silently draws nothing if
    there is not enough data for the requested lookback.
    """
    closes = ochl_data["Close"]
    try:
        lookback = int(params.get("lookback", 60))
        k = float(params.get("k", 2.0))
    except ValueError:
        tk_messagebox.showerror(
            title="Error", message="Invalid regression channel parameters"
        )
        return
    channel = regression_channel.compute_regression_channel(
        closes, lookback=lookback, k=k
    )
    regression_channel.plot_regression_channel_on_axe(axe, channel)


def plot_bollinger_bands(axe, ochl_data, params):
    """Bollinger bands : SMA +/- k*sigma glissant sur une fenêtre `period`.
    See bollinger_bands.py for the full model. Silently draws nothing if
    there is not enough data for the requested period.
    """
    closes = ochl_data["Close"]
    try:
        period = int(params.get("period", 20))
        k = float(params.get("k", 2.0))
    except ValueError:
        tk_messagebox.showerror(
            title="Error", message="Invalid Bollinger bands parameters"
        )
        return
    bands = bollinger_bands.compute_bollinger_bands(closes, period=period, k=k)
    bollinger_bands.plot_bollinger_bands_on_axe(axe, bands)


def plot_macd(axe, ochl_data, params):
    """MACD : EMA(fast) - EMA(slow), sa ligne de signal et leur histogramme.
    See macd.py for the full model. Silently draws nothing if there is not
    enough data for the requested slow period.
    """
    closes = ochl_data["Close"]
    try:
        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))
    except ValueError:
        tk_messagebox.showerror(title="Error", message="Invalid MACD parameters")
        return
    if fast >= slow:
        tk_messagebox.showerror(
            title="Error", message="La période rapide doit être < période lente"
        )
        return
    macd_result = macd_module.compute_macd(closes, fast=fast, slow=slow, signal=signal)
    macd_module.plot_macd_on_axe(axe, macd_result)


def update_mav_tuple(mav: Listbox) -> tuple:
    selected_mav = []
    for i in mav.curselection():
        selected_mav.append(int(mav.get(i)))
    # print(f"Selected moving averages: {selected_mav}")
    return tuple(selected_mav)


def invert_activation(w1: ttk.Combobox, w2: ttk.Entry, w3: ttk.Entry):
    if w1.instate(["disabled"]):
        w2.config(state="disabled")
        w3.config(state="disabled")
        w1.config(state="normal")
    else:
        w2.config(state="normal")
        w3.config(state="normal")
        w1.config(state="disabled")


# The following functions calculate moving average.


def mm(data: pd.DataFrame, period: int) -> pd.Series:
    """Calculates the simple moving average for the specified period"""

    print(data["Close"].rolling(period).mean())
    return data["Close"].rolling(period).mean()


if __name__ == "__main__":
    main()
