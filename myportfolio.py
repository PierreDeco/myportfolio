# import json
# import requests
from matplotlib import text
import pandas as pd
import yfinance as yf
from tkinter import StringVar, Tk, Listbox, ttk, messagebox as tk_messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mplfinance as mpf
import customtkinter as ctk

# ___
# Defining constants

POSSIBLE_MAV = ["10", "20", "50", "100", "200"]
POSSIBLE_INTERVALS = ["1d", "1wk", "1mo", "6mo", "1y"]
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
        lambda event: update_mav_tuple(mav_listbox),
    )
    mav_label = ttk.Label(frame, text="Select moving average:")

    # Drawing the canvas using matplotlib's explicit method

    fig, ax = plt.subplots(figsize=(7, 3.3))
    canvas = FigureCanvasTkAgg(fig, plot_frame)
    toolbar = NavigationToolbar2Tk(canvas, plot_frame, pack_toolbar=False)
    toolbar.update()
    # TODO: putting a legend on the graphs, especially for the MAV
    # TODO: adding the MACD
    # TODO: adding the infos of the company
    # TODO: adding the technical indicators such as RSI, Bollinger Bands, with tooltips

    # The analysis button that will trigger the stock analysis when clicked

    analysis_button = ttk.Button(
        frame,
        text="Analyze",
        command=lambda: analyze_stock(
            canvas,
            symbol_entry.get(),
            start_date.get(),
            end_date.get(),
            interval.get(),
            plot_type.get(),
            intervalswitch.get(),
            update_mav_tuple(mav_listbox),
        ),
    )

    # Positioning the widgets in the grid

    frame.grid(row=0, column=0, sticky="nsew")
    plot_frame.grid(row=1, column=0, sticky="nsew")
    start_date_label.grid(row=1, column=0, sticky="w")
    start_date_entry.grid(row=1, column=1, sticky="w")
    end_date_label.grid(row=2, column=0, sticky="w")
    end_date_entry.grid(row=2, column=1, sticky="w")
    intervalswitch.grid(row=1, column=2, sticky="w")
    symbol_entry.grid(row=0, column=1, sticky="w")
    symbol_label.grid(row=0, column=0, sticky="w")
    interval_label.grid(row=0, column=2, sticky="w")
    interval_combobox.grid(row=0, column=3, sticky="w")
    quit_button.grid(row=6, column=1, sticky="w")
    analysis_button.grid(row=6, column=0, sticky="w")
    plot_type_label.grid(row=2, column=2, sticky="w")
    plot_type_box.grid(row=2, column=3, sticky="w")
    mav_label.grid(row=0, column=4, sticky="w")
    mav_listbox.grid(row=0, column=5, sticky="w", rowspan=3)
    toolbar.grid(row=0, column=0, sticky="w")
    canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
    symbol_entry.focus()
    root.mainloop()

    # This simple analyse_stock function will plot the chart with the specified
    # parameters using yfinance to fetch the data and matplotlib to plot the
    # chart.


def analyze_stock(canvas, symbol, start, end, interval, style, switch, mav):
    # TODO : All the sanity checks for the inputs
    if symbol == "":
        tk_messagebox.showerror(title="Error", message="Invalid symbol")
        return 1
    if style == "":
        tk_messagebox.showerror(title="Error", message="Invalid plot type")
        return 1
    if switch == 1:
        if interval == "":
            tk_messagebox.showerror("Error", message="Invalid interval")
            return 1
        ochl_data = yf.Ticker(symbol).history(period=interval)
    else:
        if start == "" or end == "":
            tk_messagebox.showerror("Error", message="Invalid start and/or end dates")
            return 1
        ochl_data = yf.Ticker(symbol).history(start=start, end=end)
    if ochl_data.empty:
        tk_messagebox.showerror(title="Error", message=f"No data found for {symbol}")
        print(f"No data found for symbol: {symbol}")
        return 1
    print(ochl_data)
    canvas.figure.clear()
    axe = canvas.figure.subplots()
    if style == "candle":
        plot_candle(axe, ochl_data)
    elif style == "line":
        plot_line(axe, ochl_data)
    for mean in mav:
        plot_mav(axe, ochl_data, mean)
    canvas.draw()
    return


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
    axe.plot(
        ochl_data.index,
        ochl_data["Close"],
    )


def plot_mav(axe, ochl_data, mav):
    axe.plot(ochl_data.index, mm(ochl_data, mav))


def update_mav_tuple(mav):
    selected_mav = []
    for i in mav.curselection():
        selected_mav.append(int(mav.get(i)))
    print(f"Selected moving averages: {selected_mav}")
    return tuple(selected_mav)


def invert_activation(w1, w2, w3):

    if w1.instate(["disabled"]):
        w2.config(state="disabled")
        w3.config(state="disabled")
        w1.config(state="normal")
    else:
        w2.config(state="normal")
        w3.config(state="normal")
        w1.config(state="disabled")


# The following functions calculate moving average.


def mm(data, period):
    print(data["Close"].rolling(period).mean())
    return data["Close"].rolling(period).mean()


def mm5(data):
    mm5 = 0.0
    data = dict(list(data.items())[1:6])
    for serie in data.values():
        mm5 += float(serie["Close"])
    mm5 = mm5 / 5
    return round(mm5, 2)


def mm20(data):
    mm20 = 0.0
    data = dict(list(data.items())[1:21])
    for serie in data.values():
        mm20 += float(serie["Close"])
    mm20 = mm20 / 20
    return round(mm20, 2)


def mm100(data):
    mm100 = 0.0
    data = dict(list(data.items())[1:101])
    for serie in data.values():
        mm100 += float(serie["Close"])
    mm100 = mm100 / 100
    return round(mm100, 2)


if __name__ == "__main__":
    main()
