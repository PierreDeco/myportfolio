# import json
# import requests
import pandas as pd
import yfinance as yf
from tkinter import *
from tkinter import ttk, messagebox as tk_messagebox
import numpy as np
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import mplfinance as mpf


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
    interval_combobox = ttk.Combobox(
        root, values=["1d", "1wk", "1mo", "1y"], state="readonly"
    )

    # Starting the plot type part

    plot_type = ttk.Combobox(
        root, values=["candle", "line", "pnf", "renko"], state="readonly"
    )
    plot_type_label = ttk.Label(root, text="Select plot type:")

    # Now the moving average part
    possible_mav = ["5", "10", "20", "50", "100"]
    selected_mav = ()
    mav = Listbox(
        root,
        listvariable=StringVar(value=possible_mav),
        selectmode="multiple",
        height=5,
    )
    mav.bind(
        "<<ListboxSelect>>",
        lambda event: (  # FIXME : the following function is not working
            update_mav_tuple(mav, possible_mav, selected_mav)
        ),
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

    # The analysis button that will trigger the stock analysis when clicked

    analysis_button = ttk.Button(
        root,
        text="Analyze",
        command=lambda: analyze_stock(
            symbol_entry.get(),
            start_date_entry.get(),
            end_date_entry.get(),
            plot_type.get(),
            selected_mav,
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
    plot_type.grid(row=4, column=1, sticky="w")
    mav_label.grid(row=5, column=0, sticky="w")
    mav.grid(row=5, column=1, sticky="w")
    root.mainloop()

    # This simple analyse_stock function will plot the chart with the specified
    # parameters using yfinance to fetch the data and mplfinance to plot the
    # chart.
    #


def analyze_stock(symbol, start, end, type, mav):
    ochl_data = yf.Ticker(symbol).history(start=start, end=end)
    if ochl_data.empty:
        print(f"No data found for symbol: {symbol}")
        return 1
    print(ochl_data)
    mpf.plot(
        ochl_data,
        type=type,
        mav=mav,
        style="charles",
        title=f"{symbol} Candlestick Chart",
        ylabel="Price",
        volume=True,
    )
    return ochl_data


# FIXME : the following function is not working
def update_mav_tuple(mav, possible_mav, selected_mav):
    for i in mav.curselection():
        selected_mav.append(int(possible_mav[i]))
        print(possible_mav[i])
    return selected_mav


# The following function calculates moving average. They are utilities not used
# for now.


def mm5m(data):
    mm5 = 0.0
    data = dict(list(data.items())[1:6])
    for serie in data.values():
        mm5 += float(serie["4. close"])
    mm5 = mm5 / 5
    return round(mm5, 2)


def mm20m(data):
    mm20 = 0.0
    data = dict(list(data.items())[1:21])
    for serie in data.values():
        mm20 += float(serie["4. close"])
    mm20 = mm20 / 20
    return round(mm20, 2)


def mm100d(data):
    mm100 = 0.0
    data = dict(list(data.items())[1:101])
    for serie in data.values():
        mm100 += float(serie["4. close"])
    mm100 = mm100 / 100
    return round(mm100, 2)


if __name__ == "__main__":
    main()
