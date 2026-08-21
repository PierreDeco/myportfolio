# import json
# import requests
import pandas as pd
import yfinance as yf
from tkinter import *
from tkinter import ttk, messagebox as tk_messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import mplfinance as mpf

# ___
# Defining constants

POSSIBLE_MAV = ["10", "20", "50", "100", "200"]
POSSIBLE_INTERVALS = ["1d", "1wk", "1mo", "1y"]
POSSIBLE_PLOT_TYPES = ["candle", "line", "pnf", "renko"]

# ___


def main():
    # User interface setup, starting with the basic widgets
    root = Tk()
    root.title("MyPortfolio : Personal Stock Technical Analysis")
    frame = ttk.Frame(root, relief="ridge", padding=5)
    quit_button = ttk.Button(root, text="Quit", command=root.destroy)
    symbol_label = ttk.Label(root, text="Enter stock symbol:")
    symbol_entry = ttk.Entry(root)
    start_date_label = ttk.Label(root, text="Start date (YYYY-MM-DD):")
    start_date_entry = ttk.Entry(root)
    end_date_label = ttk.Label(root, text="End date (YYYY-MM-DD):")
    end_date_entry = ttk.Entry(root)
    interval_label = ttk.Label(root, text="Select interval:")
    interval_combobox = ttk.Combobox(root, values=POSSIBLE_INTERVALS, state="readonly")

    # ___
    # Starting the plot type part

    plot_type_box = ttk.Combobox(root, values=POSSIBLE_PLOT_TYPES, state="readonly")
    plot_type_label = ttk.Label(root, text="Select plot type:")

    # Now the moving average part
    mav = Listbox(
        root,
        listvariable=StringVar(value=POSSIBLE_MAV),
        selectmode="multiple",
        height=5,
    )
    mav.bind(
        "<<ListboxSelect>>",
        lambda event: update_mav_tuple(mav, POSSIBLE_MAV),
    )
    mav_label = ttk.Label(root, text="Select moving average:")

    canvas = FigureCanvasTkAgg(Figure(figsize=(5, 4), dpi=100), master=root)
    canvas.draw()
    toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
    toolbar.update()
    # TODO : the integration part
    canvas.mpl_connect(
        "key_press_event", lambda event: key_press_handler(event, canvas, toolbar)
    )

    # TODO: putting a legend on the graphs, especially for the MAV
    # TODO: adding the MACD
    # TODO: adding the infos of the company
    # TODO: adding the technical indicators such as RSI, Bollinger Bands, with tooltips

    # The analysis button that will trigger the stock analysis when clicked

    analysis_button = ttk.Button(
        root,
        text="Analyze",
        command=lambda: analyze_stock(
            symbol_entry.get(),
            start_date_entry.get(),
            end_date_entry.get(),
            interval_combobox.get(),
            plot_type_box.get(),
        ),
    )

    # Positioning the widgets in the grid

    frame.grid(row=0, column=0, sticky="w")
    start_date_label.grid(row=1, column=0, sticky="w")
    start_date_entry.grid(row=1, column=1, sticky="w")
    end_date_label.grid(row=2, column=0, sticky="w")
    end_date_entry.grid(row=2, column=1, sticky="w")
    symbol_entry.grid(row=0, column=1, sticky="w")
    symbol_label.grid(row=0, column=0, sticky="w")
    interval_label.grid(row=3, column=0, sticky="w")
    interval_combobox.grid(row=3, column=1, sticky="w")
    quit_button.grid(row=6, column=1, sticky="e")
    analysis_button.grid(row=6, column=0, sticky="w")
    plot_type_label.grid(row=4, column=0, sticky="w")
    plot_type_box.grid(row=4, column=1, sticky="w")
    mav_label.grid(row=5, column=0, sticky="w")
    mav.grid(row=5, column=1, sticky="w")
    root.mainloop()

    # This simple analyse_stock function will plot the chart with the specified
    # parameters using yfinance to fetch the data and matplotlib to plot the
    # chart.


def analyze_stock(symbol, start, end, interval, style):
    # TODO : Select between an interval and a custom period (with starting and end dates)
    ochl_data = yf.Ticker(symbol).history(start=start, end=end)
    if ochl_data.empty:
        # TODO:: Messagebox with the error message
        print(f"No data found for symbol: {symbol}")
        return 1
    print(ochl_data)
    if style == "candle":
        plot_candle(ochl_data)
    elif style == "line":
        plot_line(ochl_data)
    return


def plot_candle(ochl_data):
    plt.figure()
    up = ochl_data[ochl_data.Close >= ochl_data.Open]
    down = ochl_data[ochl_data.Close < ochl_data.Open]
    col1 = "green"
    col2 = "red"
    width = 0.8
    width2 = 0.08
    plt.bar(up.index, up.Close - up.Open, width, bottom=up.Open, color=col1)
    plt.bar(up.index, up.High - up.Close, width2, bottom=up.Close, color=col1)
    plt.bar(up.index, up.Low - up.Open, width2, bottom=up.Open, color=col1)

    plt.bar(down.index, down.Close - down.Open, width, bottom=down.Open, color=col2)
    plt.bar(down.index, down.High - down.Open, width2, bottom=down.Open, color=col2)
    plt.bar(down.index, down.Low - down.Close, width2, bottom=down.Close, color=col2)

    plt.xticks(rotation=30)
    plt.show()


def plot_line(ochl_data):
    plt.figure()
    col = "blue"
    plt.plot(ochl_data.index, ochl_data["Close"], color=col)
    plt.xticks(rotation=30)
    plt.show()


def update_mav_tuple(mav, possible_mav):
    selected_mav = []
    for i in mav.curselection():
        selected_mav.append(int(mav.get(i)))
    print(f"Selected moving averages: {selected_mav}")
    return tuple(selected_mav)


if __name__ == "__main__":
    main()
