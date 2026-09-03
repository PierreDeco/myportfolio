"""Small reusable hover-tooltip helper for Tkinter/ttk widgets.

Standard "balloon help" recipe: bind <Enter>/<Leave> on a widget and show a
borderless Toplevel with a wrapped Label near the cursor while the pointer
stays over the widget. No external dependency, works with both plain
Tkinter and ttk widgets.
"""

from __future__ import annotations

import tkinter as tk


class ToolTip:
    """Attaches a hover tooltip showing `text` to `widget`.

    The tooltip pops up after `delay` ms of hovering (so it doesn't flash on
    a passing mouse) and disappears on <Leave> or any click.
    """

    def __init__(self, widget, text: str, wraplength: int = 320, delay: int = 400):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.delay = delay
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, event=None):
        self._cancel_pending()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel_pending(self):
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self):
        if self._tip is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        try:
            self._tip.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        self._tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            background="#ffffe0",
            foreground="#000000",
            relief="solid",
            borderwidth=1,
            wraplength=self.wraplength,
            padx=6,
            pady=4,
            font=("TkDefaultFont", 9),
        )
        label.pack()

    def _hide(self, event=None):
        self._cancel_pending()
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


def add_tooltip(widget, text: str, **kwargs) -> ToolTip:
    """Convenience wrapper: attaches a ToolTip to `widget` and returns it
    (kept alive by the widget's own event bindings, no need to hold a ref)."""
    return ToolTip(widget, text, **kwargs)
