#!/usr/bin/env python3
"""
Tkinter Visual GUI Designer
----------------------------
A drag‑and‑drop GUI builder for Tkinter.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

import customtkinter as ctk

ctk.set_appearance_mode("light")  # force light theme regardless of OS setting
ctk.set_default_color_theme("blue")

import json
import copy
import subprocess
import sys
import tempfile
import os
import ast
import re
import platform
import shutil
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

# ─── Optional PIL for image support ────────────────────────────────────────
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─── Constants ──────────────────────────────────────────────────────────────

MIN_W = 40
MIN_H = 20
HANDLE_HALF = 6
GRID_SIZE = 10
CONTAINER_TYPES = {"Frame", "LabelFrame", "PanedWindow", "Notebook"}

# Injected into a generated script's own source (not used by the builder's
# own UI, which has its own separate _show_tooltip/_hide_tooltip) whenever
# any element has a non-empty "tooltip" prop. Previously the generator only
# wrote a "# tooltip: ..." comment into the exported script, which obviously
# never showed anything when the exported app actually ran -- this makes
# tooltips real, functional Toplevel popups in the generated app too.
TOOLTIP_HELPER_CODE = '''class _ToolTip:
    """Small hover tooltip for the generated app (Enter/Leave shows and
    hides a borderless popup near the widget)."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._win = None
        try:
            # A few CTk widgets (e.g. CTkTabview) don't implement bind() at
            # all and raise NotImplementedError -- skip the tooltip for
            # those rather than crashing the whole app on startup.
            widget.bind("<Enter>", self._show, add="+")
            widget.bind("<Leave>", self._hide, add="+")
        except (NotImplementedError, tk.TclError):
            pass

    def _show(self, event=None):
        if self._win is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._win = tk.Toplevel(self.widget)
        self._win.wm_overrideredirect(True)
        self._win.wm_geometry(f"+{x}+{y}")
        tk.Label(self._win, text=self.text, justify="left",
                 background="#FFFFE0", relief="solid", borderwidth=1,
                 font=("Segoe UI", 9)).pack(ipadx=4, ipady=2)

    def _hide(self, event=None):
        if self._win is not None:
            self._win.destroy()
            self._win = None
'''

# ─── Toolbox item colors (CustomTkinter) ────
# The app is forced to light mode only (see set_appearance_mode("light")
# above), so these are single colors rather than CTk's (light, dark) tuple
# form -- there's no dark-mode variant to ever fall back to.
TOOLBOX_NORMAL_COLOR = "#FFFFFF"
TOOLBOX_HOVER_COLOR = "#E3F2FD"
TOOLBOX_ACTIVE_COLOR = "#FF6B35"

# ─── Element Catalogue ──────────────────────────────────────────────────────

ELEMENT_TYPES: Dict[str, Dict[str, Any]] = {
    "Label": {
        "display": "🏷️ Label",
        "widget": "tk.Label",
        "default_size": (120, 30),
        "defaults": {"text": "Label", "font": ("Segoe UI", 9), "fg": "#212121",
                      "bg": "#F5F5F5",
                      "relief": "flat", "justify": "center",
                      "corner_radius": ""},
        "tile_bg": "#E3F2FD", "tile_fg": "#1565C0",
        "category": "Input",
    },
    "Entry": {
        "display": "✍️ Entry",
        "widget": "tk.Entry",
        "default_size": (160, 30),
        "defaults": {"textvariable": "", "show": "", "width": 20,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "white", "relief": "sunken",
                      "justify": "left", "default_value": "",
                      "corner_radius": ""},
        "tile_bg": "#FFFFFF", "tile_fg": "#212121",
        "category": "Input",
    },
    "Button": {
        "display": "🔘 Button",
        "widget": "tk.Button",
        "default_size": (100, 34),
        "defaults": {"text": "Button", "font": ("Segoe UI", 9, "bold"),
                      "fg": "#FFFFFF", "bg": "#1976D2",
                      "relief": "flat", "command": "",
                      "corner_radius": ""},
        "tile_bg": "#1976D2", "tile_fg": "#FFFFFF",
        "category": "Input",
    },
    "Radiobutton": {
        "display": "◉ Radiobutton",
        "widget": "tk.Radiobutton",
        "default_size": (130, 30),
        "defaults": {"text": "Option", "variable": "", "value": 1,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "#F5F5F5", "relief": "flat",
                      "corner_radius": ""},
        "tile_bg": "#F3E5F5", "tile_fg": "#6A1B9A",
        "category": "Input",
    },
    "Checkbutton": {
        "display": "☑ Checkbutton",
        "widget": "tk.Checkbutton",
        "default_size": (130, 30),
        "defaults": {"text": "Checkbox", "variable": "", "onvalue": 1,
                      "offvalue": 0,
                      "font": ("Segoe UI", 9), "fg": "#212121", "bg": "#F5F5F5",
                      "default_value": 0, "corner_radius": ""},
        "tile_bg": "#E8F5E9", "tile_fg": "#2E7D32",
        "category": "Input",
    },
    "Scale": {
        "display": "🎚️ Scale (Slider)",
        "widget": "tk.Scale",
        "default_size": (180, 40),
        "defaults": {"from_": 0, "to": 100, "orient": "horizontal",
                      "length": 150,
                      "tickinterval": 0, "resolution": 1,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "#F5F5F5", "default_value": 0,
                      "corner_radius": ""},
        "tile_bg": "#FCE4EC", "tile_fg": "#AD1457",
        "category": "Input",
    },
    "Combobox": {
        "display": "🔽 Combobox",
        "widget": "ttk.Combobox",
        "default_size": (150, 30),
        "defaults": {"values": ["Option 1", "Option 2", "Option 3"],
                      "state": "readonly",
                      "font": ("Segoe UI", 9), "width": 18,
                      "default_value": "", "corner_radius": ""},
        "tile_bg": "#FFF3E0", "tile_fg": "#E65100",
        "category": "Input",
    },
    "Spinbox": {
        "display": "🔢 Spinbox",
        "widget": "tk.Spinbox",
        "default_size": (80, 30),
        "defaults": {"from_": 0, "to": 100, "width": 5,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "white", "relief": "sunken",
                      "default_value": 0},
        "tile_bg": "#FFF8E1", "tile_fg": "#E65100",
        "category": "Input",
    },
    "Listbox": {
        "display": "📋 Listbox",
        "widget": "tk.Listbox",
        "default_size": (150, 80),
        "defaults": {"listvariable": "", "items": ["Item 1", "Item 2"],
                      "height": 4, "width": 18,
                      "font": ("Segoe UI", 9), "fg": "#212121", "bg": "white",
                      "relief": "sunken", "selectmode": "single"},
        "tile_bg": "#E3F2FD", "tile_fg": "#0D47A1",
        "category": "Input",
    },
    "Text": {
        "display": "📝 Text (Multiline)",
        "widget": "tk.Text",
        "default_size": (200, 90),
        "defaults": {"height": 5, "width": 30, "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "white", "relief": "sunken",
                      "wrap": "word", "corner_radius": ""},
        "tile_bg": "#FFFDE7", "tile_fg": "#F57F17",
        "category": "Input",
    },
    "Canvas": {
        "display": "🎨 Canvas (Drawing)",
        "widget": "tk.Canvas",
        "default_size": (200, 120),
        "defaults": {"width": 200, "height": 120, "bg": "white",
                      "relief": "sunken", "bd": 2},
        "tile_bg": "#FFF8E1", "tile_fg": "#F57F17",
        "category": "Display",
    },
    "Progressbar": {
        "display": "⏳ Progressbar (ttk)",
        "widget": "ttk.Progressbar",
        "default_size": (180, 30),
        "defaults": {"maximum": 100, "value": 40, "orient": "horizontal",
                      "length": 180, "corner_radius": ""},
        "tile_bg": "#E8F5E9", "tile_fg": "#1B5E20",
        "category": "Input",
    },
    "Scrollbar": {
        "display": "↕️ Scrollbar",
        "widget": "tk.Scrollbar",
        "default_size": (20, 120),
        "defaults": {"orient": "vertical", "width": 16, "bg": "#E0E0E0"},
        "tile_bg": "#CFD8DC", "tile_fg": "#37474F",
        "category": "Display",
    },
    "Frame": {
        "display": "🖼️ Frame (Container)",
        "widget": "tk.Frame",
        "default_size": (200, 120),
        "defaults": {"relief": "groove", "bd": 2, "bg": "#F5F5F5",
                      "corner_radius": ""},
        "tile_bg": "#ECEFF1", "tile_fg": "#263238",
        "category": "Containers",
    },
    "LabelFrame": {
        "display": "🗂️ LabelFrame",
        "widget": "tk.LabelFrame",
        "default_size": (200, 120),
        "defaults": {"text": "LabelFrame", "relief": "groove", "bd": 2,
                      "bg": "#F5F5F5", "font": ("Segoe UI", 9),
                      "corner_radius": ""},
        "tile_bg": "#E0F2F1", "tile_fg": "#004D40",
        "category": "Containers",
    },
    "Notebook": {
        "display": "📑 Notebook (Tabs)",
        "widget": "ttk.Notebook",
        "default_size": (260, 160),
        "defaults": {"tabs": ["Tab 1", "Tab 2"], "active_tab": 0,
                      "corner_radius": ""},
        "tile_bg": "#EDE7F6", "tile_fg": "#311B92",
        "category": "Containers",
    },
    "PanedWindow": {
        "display": "🪟 PanedWindow",
        "widget": "tk.PanedWindow",
        "default_size": (200, 120),
        "defaults": {"orient": "horizontal", "bg": "#F5F5F5",
                      "sashrelief": "raised"},
        "tile_bg": "#D7CCC8", "tile_fg": "#4E342E",
        "category": "Containers",
    },
    "Separator": {
        "display": "➖ Separator",
        "widget": "ttk.Separator",
        "default_size": (150, 4),
        "defaults": {"orient": "horizontal"},
        "tile_bg": "#B0BEC5", "tile_fg": "#263238",
        "category": "Display",
    },
    "Table": {
        "display": "📊 Table (Excel/CSV)",
        "widget": "ttk.Treeview",
        "default_size": (320, 200),
        "defaults": {"file": "", "sheet": 0, "columns": "", "height": 8},
        "tile_bg": "#E0F7FA", "tile_fg": "#004D40",
        "category": "Display",
    },
    "Image": {
        "display": "🖼️ Image",
        "widget": "tk.Label",
        "default_size": (140, 100),
        "defaults": {"text": "Image", "tooltip": "", "image_path": "",
                      "corner_radius": ""},
        "tile_bg": "#ECEFF1", "tile_fg": "#455A64",
        "category": "Display",
    },
}

# ─── Property Fields ──────────────────────────────────────────────────────

PROPERTY_FIELDS: Dict[str, List[Tuple]] = {
    "Label": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("justify", "Justify", "combobox", ["left", "center", "right"]),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Entry": [
        ("textvariable", "Variable", "entry"),
        ("show", "Password char", "entry"), ("width", "Width", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("justify", "Justify", "combobox", ["left", "center", "right"]),
        ("default_value", "Default Value", "entry"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Button": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("command", "Command", "text"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Radiobutton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"),
        ("value", "Value", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"), ("relief", "Relief", "combobox",
                                        ["flat", "raised", "sunken", "groove",
                                         "ridge"]),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Checkbutton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"),
        ("onvalue", "On Value", "entry"), ("offvalue", "Off Value", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("default_value", "Default Value", "entry"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Scale": [
        ("from_", "From", "entry"), ("to", "To", "entry"),
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("length", "Length", "entry"),
        ("tickinterval", "Tick interval", "entry"),
        ("resolution", "Resolution", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("default_value", "Default Value", "entry"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Listbox": [
        ("listvariable", "Variable", "entry"),
        ("items", "Items (csv)", "entry"), ("height", "Height (rows)", "entry"),
        ("width", "Width (chars)", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("selectmode", "Select mode", "combobox",
         ["single", "browse", "multiple", "extended"]),
    ],
    "Text": [
        ("height", "Height (rows)", "entry"),
        ("width", "Width (chars)", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("wrap", "Wrap", "combobox", ["none", "char", "word"]),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Frame": [
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("bd", "Border width", "entry"), ("bg", "Background", "color"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "LabelFrame": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("bd", "Border width", "entry"), ("bg", "Background", "color"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Notebook": [
        ("tabs", "Tabs", "entry"),
        ("active_tab", "Active Tab", "combobox", []),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "PanedWindow": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("bg", "Background", "color"), ("sashrelief", "Sash relief", "combobox",
                                        ["flat", "raised", "sunken", "groove",
                                         "ridge"]),
    ],
    "Separator": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("canvas_w", "Width (px)", "entry"),
        ("canvas_h", "Height (px)", "entry")
    ],
    "Canvas": [
        ("width", "Width", "entry"), ("height", "Height", "entry"),
        ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("bd", "Border width", "entry"),
    ],
    "Scrollbar": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("width", "Width", "entry"), ("bg", "Background", "color"),
    ],
    "Combobox": [
        ("values", "Values (csv)", "entry"),
        ("state", "State", "combobox", ["normal", "readonly", "disabled"]),
        ("font", "Font", "font"), ("width", "Width (chars)", "entry"),
        ("default_value", "Default Value", "entry"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Spinbox": [
        ("from_", "From", "entry"), ("to", "To", "entry"),
        ("width", "Width (chars)", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"), ("relief", "Relief", "combobox",
                                        ["flat", "raised", "sunken", "groove",
                                         "ridge"]),
        ("default_value", "Default Value", "entry"),
    ],
    "Progressbar": [
        ("maximum", "Maximum", "entry"), ("value", "Current value", "entry"),
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("length", "Length", "entry"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
    "Table": [
        ("file", "Excel/CSV File", "file"),
        ("sheet", "Sheet Name", "entry"),
        ("columns", "Columns (csv)", "entry"),
        ("height", "Rows visible", "entry"),
    ],
    "Image": [
        ("text", "Caption / Alt", "entry"),
        ("image_path", "Image File", "image_file"),  # custom file picker
        ("tooltip", "Tooltip", "entry"),
        ("corner_radius", "Corner Radius", "entry"),
    ],
}

# ─── Fix 6 & 7: ensure every element type exposes pixel Width/Height and a Tooltip field
for _etype in ELEMENT_TYPES:
    _fields = PROPERTY_FIELDS.setdefault(_etype, [])
    _keys = {f[0] for f in _fields}
    if "canvas_w" not in _keys:
        _fields.append(("canvas_w", "Width (px)", "entry"))
    if "canvas_h" not in _keys:
        _fields.append(("canvas_h", "Height (px)", "entry"))
    if "tooltip" not in _keys:
        _fields.append(("tooltip", "Tooltip", "entry"))

DEFAULT_EVENT_MAP = {
    "Button": "command", "Entry": "<KeyRelease>", "Radiobutton": "command",
    "Checkbutton": "command",
    "Scale": "command", "Listbox": "<<ListboxSelect>>", "Text": "<KeyRelease>",
    "Combobox": "<<ComboboxSelected>>",
    "Spinbox": "<KeyRelease>", "Progressbar": None, "Label": None,
    "Frame": None, "LabelFrame": None,
    "Notebook": None, "PanedWindow": None, "Separator": None,
    "Canvas": None, "Scrollbar": None, "Table": None, "Image": None,
}

# ─── Mapping from element type to CustomTkinter widget class string ────
CTK_WIDGET_MAP = {
    "Label": "ctk.CTkLabel",
    "Entry": "ctk.CTkEntry",
    "Button": "ctk.CTkButton",
    "Radiobutton": "ctk.CTkRadioButton",
    "Checkbutton": "ctk.CTkCheckBox",
    "Scale": "ctk.CTkSlider",
    "Combobox": "ctk.CTkComboBox",
    "Spinbox": "tk.Spinbox",          # no CTk equivalent; keep tk
    "Listbox": "tk.Listbox",          # no CTk equivalent; keep tk
    "Text": "ctk.CTkTextbox",
    "Canvas": "tk.Canvas",            # no CTk equivalent
    "Progressbar": "ctk.CTkProgressBar",
    "Scrollbar": "tk.Scrollbar",      # no CTk equivalent
    "Frame": "ctk.CTkFrame",
    "LabelFrame": "ctk.CTkFrame",     # CTkFrame with border
    "Notebook": "ctk.CTkTabview",
    "PanedWindow": "tk.PanedWindow",  # no CTk equivalent
    "Separator": "ttk.Separator",  # ctk.CTkSeparator isn't present in all
                                    # customtkinter versions; ttk.Separator
                                    # is always available and stable.
    "Table": "ttk.Treeview",          # no CTk equivalent
    "Image": "ctk.CTkLabel",          # with image
}

# CTk property name mapping (tk -> ctk)
CTK_PROP_MAP = {
    "bg": "fg_color",
    "fg": "text_color",
    "relief": None,   # CTk widgets don't use relief; we can drop or use border_width
    "bd": "border_width",
    "width": None,    # we handle separately via canvas_w
    "height": None,   # we handle separately via canvas_h
    "font": "font",
    "text": "text",
    "command": "command",
    "variable": "variable",
    "textvariable": "textvariable",
    "corner_radius": "corner_radius",
    "value": "value",  # for radiobutton
    "onvalue": "onvalue",
    "offvalue": "offvalue",
    "from_": "from_",  # CTkSlider uses from_
    "to": "to",
    "orient": "orientation",  # CTkSlider uses orientation (not orient)
    "length": "length",
    "tickinterval": None,  # not supported
    "resolution": "number_of_steps",  # not exact
    "values": "values",
    "state": "state",
    "listvariable": "listvariable",  # not used
    "items": None,
    "selectmode": None,
    "wrap": "wrap",
    "show": "show",
    "default_value": None,  # handled separately
    "justify": "justify",   # CTkLabel supports justify
    "anchor": "anchor",
    "maximum": "maximum",
    "value": "value",
    "file": None,
    "sheet": None,
    "columns": None,
    "tabs": None,
    "active_tab": None,
    "sashrelief": "sashrelief",
}

# Some legacy tk field keys have no CTk-equivalent kwarg on certain CTk
# widgets, even though CTK_PROP_MAP maps them to *something*. e.g.
# ctk.CTkSlider accepts neither length, font, nor text_color; CTkProgressBar
# accepts neither maximum, value, nor length (progress is set post-init via
# .set()); ctk.CTkFrame (used for LabelFrame) doesn't take text or font.
# These must be dropped before building the constructor call or the
# generated code raises ValueError/TypeError at runtime.
CTK_UNSUPPORTED_PROPS = {
    "Scale": {"length", "font", "fg", "bg", "tickinterval"},
    "Progressbar": {"maximum", "value", "length", "tickinterval"},
    "LabelFrame": {"text", "font"},
}

# For classic (non-CTk) tk widgets, CTK_PROP_MAP's ctk-style renames don't
# apply - e.g. tk.Listbox/tk.Spinbox understand "fg"/"bg", not "text_color"/
# "fg_color"; tk.PanedWindow/tk.Scrollbar understand "orient", not
# "orientation". Keep these original tkinter option names for these widgets.
LEGACY_RAW_PROP_OVERRIDE = {
    "Listbox": {"fg", "bg", "relief"},
    "Spinbox": {"fg", "bg", "relief"},
    "PanedWindow": {"orient", "bg"},
    "Scrollbar": {"orient", "bg"},
    "Separator": {"orient"},
    "Canvas": {"bg", "bd", "relief"},
}

# ─── DesignElement ──────────────────────────────────────────────────────────

@dataclass
class DesignElement:
    elem_type: str
    x: int
    y: int
    props: Dict[str, Any] = field(default_factory=dict)
    elem_id: int = 0
    selected: bool = False
    canvas_w: int = 0
    canvas_h: int = 0
    rect_id: int = 0
    text_id: int = 0
    handle_ids: Dict[str, int] = field(default_factory=dict)
    handler_code: str = ""
    parent_id: Optional[int] = None
    parent_tab: Optional[int] = None
    _image_tk: Any = None

    def __post_init__(self):
        if self.canvas_w == 0:
            self.canvas_w = ELEMENT_TYPES[self.elem_type]["default_size"][0]
        if self.canvas_h == 0:
            self.canvas_h = ELEMENT_TYPES[self.elem_type]["default_size"][1]
        if self.elem_type == "Notebook":
            tabs = self.props.get("tabs")
            if not isinstance(tabs, list) or not tabs:
                self.props["tabs"] = ["Tab 1", "Tab 2"]
            self.props["active_tab"] = max(0, min(
                int(self.props.get("active_tab", 0) or 0),
                len(self.props.get("tabs", ["Tab 1"])) - 1
                )
                                            )

    @property
    def display_label(self) -> str:
        text_val = self.props.get("text")
        if text_val is not None:
            label = str(text_val)
        elif self.props.get("default_text") is not None:
            label = str(self.props["default_text"])
        else:
            label = self.elem_type
        return (label[:15] + "…") if len(label) > 15 else label

    def contains_point(self, px: int, py: int) -> bool:
        top = self.y - 14 if self.elem_type == "LabelFrame" else self.y
        return (
                    self.x <= px <= self.x + self.canvas_w and top <= py <= self.y + self.canvas_h)

    def handle_positions(self) -> Dict[str, Tuple[int, int]]:
        x, y, w, h = self.x, self.y, self.canvas_w, self.canvas_h
        mx, my = x + w // 2, y + h // 2
        return {
            "NW": (x, y), "N": (mx, y), "NE": (x + w, y), "E": (x + w, my),
            "SE": (x + w, y + h), "S": (mx, y + h), "SW": (x, y + h),
            "W": (x, my),
        }

    def hit_handle(self, px: int, py: int) -> Optional[str]:
        x, y, w, h = self.x, self.y, self.canvas_w, self.canvas_h
        del_x, del_y = x + w + 15, y - 15
        if abs(px - del_x) <= 10 and abs(py - del_y) <= 10:
            return "DEL"

        for name, (hx, hy) in self.handle_positions().items():
            if abs(px - hx) <= HANDLE_HALF + 2 and abs(py - hy) <= HANDLE_HALF + 2:
                return name
        return None

    def to_dict(self) -> Dict:
        return {
            "elem_type": self.elem_type,
            "x": self.x,
            "y": self.y,
            "canvas_w": self.canvas_w,
            "canvas_h": self.canvas_h,
            "props": self.props,
            "handler_code": self.handler_code,
            "parent_id": self.parent_id,
            "parent_tab": self.parent_tab,
            "elem_id": self.elem_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DesignElement":
        # JSON has no tuple type, so any prop that started life as a Python
        # tuple (font = (family, size[, weight])) comes back as a list after
        # a save/load or undo/redo round-trip through json.dumps/loads.
        # CustomTkinter's font handling strictly requires a tuple (or a
        # CTkFont instance) and raises if given a list, so normalize it back
        # here -- the one place all such round-trips pass through.
        props = dict(data["props"])
        font_val = props.get("font")
        if isinstance(font_val, list):
            props["font"] = tuple(font_val)
        elem = cls(
            elem_type=data["elem_type"],
            x=data["x"],
            y=data["y"],
            props=props,
            elem_id=data.get("elem_id", 0),
            canvas_w=data["canvas_w"],
            canvas_h=data["canvas_h"],
            handler_code=data.get("handler_code", ""),
            parent_id=data.get("parent_id"),
            parent_tab=data.get("parent_tab"),
        )
        return elem


# ─── CodeGenerator ──────────────────────────────────────────────────────────

class CodeGenerator:
    @staticmethod
    def _container_depth(
            elem: DesignElement, by_id: Dict[int, DesignElement]
            ) -> int:
        depth = 0
        seen = set()
        current = elem
        while current.parent_id is not None and current.parent_id in by_id and current.parent_id not in seen:
            seen.add(current.parent_id)
            current = by_id[current.parent_id]
            depth += 1
        return depth

    @staticmethod
    def _is_ctk_widget(widget_class: str) -> bool:
        return widget_class.startswith("ctk.") or widget_class.startswith("CTk")

    @staticmethod
    def generate(
            elements: List[DesignElement], window_title: str,
            window_size: Tuple[int, int], canvas_bg: str, canvas_imports: str
            ) -> str:
        if not elements:
            return CodeGenerator._empty_template(window_title, window_size,
                                                  canvas_bg, canvas_imports)

        has_table = any(e.elem_type == "Table" for e in elements)
        if has_table and "import pandas as pd" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport pandas as pd"

        has_image_with_path = any(e.elem_type == "Image" and e.props.get("image_path") for e in elements)
        if has_image_with_path:
            if "from PIL import Image" not in canvas_imports:
                canvas_imports = canvas_imports.rstrip() + "\nfrom PIL import Image"

        if "import customtkinter as ctk" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport customtkinter as ctk"

        by_id = {e.elem_id: e for e in elements}
        class_body: List[str] = []
        class_body.append("    def __init__(self, root):")
        class_body.append("        self.root = root")
        class_body.append(f"        root.title({json.dumps(window_title)})")
        class_body.append(
            f"        root.geometry({json.dumps(f'{window_size[0]}x{window_size[1]}')})"
            )
        class_body.append(
            f"        root.configure(bg={json.dumps(canvas_bg)})"
            )
        class_body.append("")

        vars_to_create = {}
        for elem in elements:
            if elem.elem_type in ("Radiobutton", "Checkbutton"):
                var_name = elem.props.get("variable")
                if var_name and var_name not in vars_to_create:
                    var_type = "ctk.IntVar(value=0)" if elem.elem_type == "Checkbutton" else "ctk.StringVar(value='')"
                    vars_to_create[var_name] = var_type
            elif elem.elem_type == "Entry":
                var_name = elem.props.get("textvariable")
                if var_name and var_name not in vars_to_create:
                    vars_to_create[var_name] = "ctk.StringVar(value='')"
        for v_name, v_type in vars_to_create.items():
            class_body.append(f"        self.{v_name} = {v_type}")
        if vars_to_create:
            class_body.append("")

        bindings = []
        for elem in elements:
            if elem.handler_code.strip():
                event = DEFAULT_EVENT_MAP.get(elem.elem_type)
                if event:
                    bindings.append(
                        (elem, event, f"self._elem_{elem.elem_id}")
                        )

        # Order elements: containers first, then by depth, then by id
        depths = {}
        for e in elements:
            depths[e.elem_id] = CodeGenerator._container_depth(e, by_id)
        ordered = sorted(elements, key=lambda e: (
            not (e.elem_type in CONTAINER_TYPES),  # containers first (False < True)
            depths.get(e.elem_id, 0),
            e.elem_id
        ))

        for elem in ordered:
            var_name = f"self._elem_{elem.elem_id}"

            widget_class = CTK_WIDGET_MAP.get(elem.elem_type, ELEMENT_TYPES[elem.elem_type]["widget"])
            props = copy.deepcopy(elem.props)
            listbox_items = props.pop("items", []) if elem.elem_type == "Listbox" else []
            notebook_tabs = props.pop("tabs", ["Tab 1", "Tab 2"]) if elem.elem_type == "Notebook" else []
            if elem.elem_type == "Notebook":
                props.pop("active_tab", None)

            for b_elem, b_event, _ in bindings:
                if b_elem == elem and b_event == "command":
                    props["command"] = f"self._on_{elem.elem_type}_{elem.elem_id}"

            if props.get("textvariable") == "":
                props.pop("textvariable", None)
            def_val = props.pop("default_value", None)
            tooltip_val = props.pop("tooltip", None)

            if elem.elem_type == "Label" and "justify" in props:
                justify = props["justify"]
                anchor_map = {"left": "w", "center": "center", "right": "e"}
                if "anchor" not in props:
                    props["anchor"] = anchor_map.get(justify, "center")

            # Build property string
            prop_strs = []
            unsupported = CTK_UNSUPPORTED_PROPS.get(elem.elem_type, set())
            legacy_raw = LEGACY_RAW_PROP_OVERRIDE.get(elem.elem_type, set())
            for k, v in props.items():
                if k == "font" and isinstance(v, list):
                    # Defense in depth: font must be emitted as a tuple
                    # literal, never a list (CTk widgets raise ValueError
                    # for a list font argument). from_dict() normalizes
                    # this already, but guard here too in case a prop
                    # dict reaches this point some other way.
                    v = tuple(v)
                if k in unsupported:
                    continue
                if k in legacy_raw:
                    target_k = k  # keep original tkinter option name
                else:
                    target_k = CTK_PROP_MAP.get(k)
                    if target_k is None:
                        continue
                if CodeGenerator._is_ctk_widget(widget_class) and k in ("width", "height"):
                    continue
                if k == "variable":
                    if v:
                        prop_strs.append(f"variable=self.{v}")
                    continue
                elif k == "textvariable":
                    if v:
                        prop_strs.append(f"textvariable=self.{v}")
                    continue
                elif k == "corner_radius":
                    if v not in (None, ""):
                        try:
                            prop_strs.append(f"corner_radius={int(v)}")
                        except (TypeError, ValueError):
                            pass
                    continue
                elif k == "command" and isinstance(v, str) and v.startswith("self."):
                    prop_strs.append(f"command={v}")
                elif k == "values" and isinstance(v, list):
                    prop_strs.append(f"values={repr(v)}")
                elif k in ("from_", "to", "onvalue", "offvalue"):
                    prop_strs.append(f"{target_k}={v}")
                elif isinstance(v, str):
                    prop_strs.append(f"{target_k}={json.dumps(v)}")
                elif isinstance(v, (int, float)):
                    prop_strs.append(f"{target_k}={v}")
                else:
                    prop_strs.append(f"{target_k}={repr(v)}")

            # Add orientation defaults for Scale/Progressbar
            if elem.elem_type == "Scale" and "orient" not in props and "orientation" not in [p.split('=')[0] for p in prop_strs]:
                prop_strs.append("orientation='horizontal'")
            if elem.elem_type == "Progressbar" and "orient" not in props and "orientation" not in [p.split('=')[0] for p in prop_strs]:
                prop_strs.append("orientation='horizontal'")

            # For CTk widgets, add width and height from canvas_w/canvas_h
            if CodeGenerator._is_ctk_widget(widget_class):
                prop_strs.append(f"width={elem.canvas_w}")
                prop_strs.append(f"height={elem.canvas_h}")

            prop_str = (", " + ", ".join(prop_strs)) if prop_strs else ""

            parent_name = "root"
            rel_x, rel_y = elem.x, elem.y
            if elem.parent_id is not None and elem.parent_id in by_id:
                parent_elem = by_id[elem.parent_id]
                if parent_elem.elem_type == "Notebook":
                    tab_idx = elem.parent_tab if elem.parent_tab is not None else parent_elem.props.get(
                        "active_tab", 0
                        )
                    tabs_count = len(
                        parent_elem.props.get("tabs", ["Tab 1"])
                        ) or 1
                    tab_idx = max(0,
                                   min(int(tab_idx or 0), tabs_count - 1)
                                   )
                    parent_name = f"self._elem_{parent_elem.elem_id}_tab_{tab_idx}"
                else:
                    parent_name = f"self._elem_{parent_elem.elem_id}"
                rel_x = elem.x - parent_elem.x
                rel_y = elem.y - parent_elem.y

            # --- Generate widget creation line ---
            if elem.elem_type == "Table":
                table_file = elem.props.get("file", "")
                table_sheet = elem.props.get("sheet", 0)
                columns_csv = elem.props.get("columns", "")
                table_height = int(elem.props.get("height", 8) or 8)

                class_body.append(f"        columns = []")
                if columns_csv:
                    cols = [c.strip() for c in columns_csv.split(",") if c.strip()]
                    class_body.append(f"        columns = {repr(cols)}")
                class_body.append(
                    f"        {var_name} = ttk.Treeview({parent_name}, columns=columns, show='headings', height={table_height})"
                    )
                class_body.append(f"        for col in columns:")
                class_body.append(
                    f"            {var_name}.heading(col, text=col)"
                    )
                class_body.append(
                    f"            {var_name}.column(col, width=100, anchor='w')"
                    )
                if table_file:
                    class_body.append(f"        try:")
                    class_body.append(f"            import pandas as pd")
                    if str(table_file).lower().endswith(('.xlsx', '.xls')):
                        class_body.append(
                            f"            df = pd.read_excel({json.dumps(table_file)}, sheet_name={json.dumps(table_sheet) if table_sheet else 0})"
                            )
                    else:
                        class_body.append(
                            f"            df = pd.read_csv({json.dumps(table_file)})"
                            )
                    class_body.append(f"            if not columns:")
                    class_body.append(
                        f"                columns = list(df.columns)"
                        )
                    class_body.append(f"                for col in columns:")
                    class_body.append(
                        f"                    {var_name}.heading(col, text=col)"
                        )
                    class_body.append(
                        f"                    {var_name}.column(col, width=100, anchor='w')"
                        )
                    class_body.append(
                        f"            for _, row in df.head(10).iterrows():"
                        )
                    class_body.append(
                        f"                {var_name}.insert('', 'end', values=list(row))"
                        )
                    class_body.append(f"        except Exception as e:")
                    class_body.append(
                        f"            print('Table load error:', e)"
                        )
            elif elem.elem_type == "Image":
                image_path = elem.props.get("image_path", "")
                if image_path and PIL_AVAILABLE:
                    if "import os" not in canvas_imports:
                        canvas_imports = canvas_imports.rstrip() + "\nimport os"
                    img_rel_path = image_path
                    class_body.append(f"        img_path = {json.dumps(img_rel_path)}")
                    class_body.append(f"        if not os.path.isabs(img_path):")
                    class_body.append(f"            img_path = os.path.join(os.path.dirname(__file__), img_path)")
                    class_body.append(f"        try:")
                    class_body.append(f"            pil_image = Image.open(img_path)")
                    class_body.append(f"            ctk_image = ctk.CTkImage(pil_image, size=({elem.canvas_w}, {elem.canvas_h}))")
                    class_body.append(f"            {var_name} = ctk.CTkLabel({parent_name}, image=ctk_image, text='', width={elem.canvas_w}, height={elem.canvas_h})")
                    class_body.append(f"            {var_name}.image = ctk_image  # keep reference")
                    class_body.append(f"        except Exception as e:")
                    class_body.append(f"            {var_name} = ctk.CTkLabel({parent_name}, text='[Image Error]', fg_color='lightgray', width={elem.canvas_w}, height={elem.canvas_h})")
                else:
                    class_body.append(f'        {var_name} = ctk.CTkLabel({parent_name}, text="[Image]", fg_color="lightgray", width={elem.canvas_w}, height={elem.canvas_h})')
            else:
                class_body.append(f"        {var_name} = {widget_class}({parent_name}{prop_str})")

            # --- Extra lines for specific widgets ---
            if elem.elem_type == "Notebook":
                if not notebook_tabs:
                    notebook_tabs = ["Tab 1"]
                for i, tab_title in enumerate(notebook_tabs):
                    class_body.append(f"        {var_name}_tab_{i} = {var_name}.add({json.dumps(str(tab_title))})")
                    class_body.append(f"        self._elem_{elem.elem_id}_tab_{i} = {var_name}_tab_{i}")
                active_tab = int(elem.props.get("active_tab", 0) or 0)
                active_tab = max(0, min(active_tab, len(notebook_tabs) - 1))
                class_body.append(f"        {var_name}.set({json.dumps(notebook_tabs[active_tab])})")
            elif elem.elem_type == "LabelFrame":
                label_text = elem.props.get("text", "LabelFrame")
                class_body.append(f"        # LabelFrame title")
                class_body.append(f"        {var_name}_label = ctk.CTkLabel({var_name}, text={json.dumps(label_text)})")
                class_body.append(f"        {var_name}_label.place(x=10, y=-10)")
            elif elem.elem_type == "Progressbar":
                try:
                    maximum = float(elem.props.get("maximum", 100) or 100)
                    value = float(elem.props.get("value", 0) or 0)
                    fraction = max(0.0, min(1.0, value / maximum)) if maximum else 0.0
                    class_body.append(f"        {var_name}.set({fraction})")
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

            # --- Default value handling ---
            if def_val is not None and str(def_val).strip() != "":
                if elem.elem_type == "Checkbutton":
                    var_name_chk = copy.deepcopy(elem.props).get("variable")
                    if var_name_chk:
                        class_body.append(
                            f"        self.{var_name_chk}.set({json.dumps(def_val)})"
                            )
                    elif str(def_val).lower() in ("1", "true", "yes"):
                        class_body.append(f"        {var_name}.select()")
                elif elem.elem_type in ("Entry", "Spinbox"):
                    class_body.append(
                        f"        {var_name}.insert(0, {json.dumps(str(def_val))})"
                        )
                elif elem.elem_type == "Combobox":
                    class_body.append(
                        f"        {var_name}.set({json.dumps(str(def_val))})"
                        )
                elif elem.elem_type == "Scale":
                    try:
                        num_val = float(def_val) if "." in str(def_val) else int(def_val)
                        class_body.append(f"        {var_name}.set({num_val})")
                    except (ValueError, TypeError):
                        pass

            # --- Listbox items ---
            if elem.elem_type == "Listbox" and listbox_items:
                for item in listbox_items:
                    class_body.append(
                        f"        {var_name}.insert('end', {json.dumps(item)})"
                        )

            # --- Tooltip ---
            if tooltip_val:
                class_body.append(
                    f"        _ToolTip({var_name}, {json.dumps(str(tooltip_val))})"
                    )

            # --- Place line ---
            if CodeGenerator._is_ctk_widget(widget_class):
                class_body.append(f"        {var_name}.place(x={rel_x}, y={rel_y})")
            else:
                class_body.append(
                    f"        {var_name}.place(x={rel_x}, y={rel_y}, width={elem.canvas_w}, height={elem.canvas_h})"
                    )

        # --- Bindings and handler methods ---
        for elem, event, var_name in bindings:
            if event != "command":
                method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                class_body.append(
                    f"        {var_name}.bind('{event}', self.{method_name})"
                    )

        for elem, event, var_name in bindings:
            method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
            class_body.append("")
            class_body.append(f"    def {method_name}(self, event=None):")
            code_lines = elem.handler_code.strip().splitlines() or ["pass"]
            for cline in code_lines:
                class_body.append(
                    f"        {cline}" if cline.strip() else "        "
                    )

        class_body.append("")
        main_guard = [
            "", "if __name__ == '__main__':", "    root = ctk.CTk()",
            "    app = MainApplication(root)", "    root.mainloop()",
        ]

        has_tooltips = any(e.props.get("tooltip") for e in elements)
        helper_block = [TOOLTIP_HELPER_CODE, ""] if has_tooltips else []

        return "\n".join([
            '"""Generated by Tkinter Visual Designer."""', "",
            canvas_imports, "",
            'ctk.set_appearance_mode("light")  # force light theme regardless of OS setting',
            'ctk.set_default_color_theme("blue")', "",
            *helper_block,
            "class MainApplication:", *class_body, *main_guard,
        ]
        )

    @staticmethod
    def _empty_template(
            window_title: str, window_size: Tuple[int, int], canvas_bg: str,
            canvas_imports: str
            ) -> str:
        if "import customtkinter as ctk" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport customtkinter as ctk"
        return f'''"""Generated by Tkinter Visual Designer."""

{canvas_imports}

ctk.set_appearance_mode("light")  # force light theme regardless of OS setting
ctk.set_default_color_theme("blue")


def main():
    root = ctk.CTk()
    root.title({json.dumps(window_title)})
    root.geometry({json.dumps(f"{window_size[0]}x{window_size[1]}")})
    root.configure(bg={json.dumps(canvas_bg)})
    label = ctk.CTkLabel(root, text="Add elements from the toolbox to begin!", font=("Segoe UI", 10), width=200, height=30)
    label.place(x=10, y=10)
    root.mainloop()

if __name__ == "__main__":
    main()
'''

    # ─── Helper to generate lines for a single element ────────────────────
    @staticmethod
    def generate_element_lines(
            elem: DesignElement, all_elements: List[DesignElement]
            ) -> Tuple[str, str, List[str]]:
        by_id = {e.elem_id: e for e in all_elements}
        widget_line = ""
        place_line = ""
        extra_lines: List[str] = []

        var_name = f"self._elem_{elem.elem_id}"
        widget_class = CTK_WIDGET_MAP.get(elem.elem_type, ELEMENT_TYPES[elem.elem_type]["widget"])
        props = copy.deepcopy(elem.props)

        if elem.elem_type == "Label" and "justify" in props:
            justify = props["justify"]
            anchor_map = {"left": "w", "center": "center", "right": "e"}
            if "anchor" not in props:
                props["anchor"] = anchor_map.get(justify, "center")

        bindings = []
        for e in all_elements:
            if e.handler_code.strip():
                event = DEFAULT_EVENT_MAP.get(e.elem_type)
                if event:
                    bindings.append((e, event, f"self._elem_{e.elem_id}"))

        listbox_items = props.pop("items", []) if elem.elem_type == "Listbox" else []
        notebook_tabs = props.pop("tabs", ["Tab 1", "Tab 2"]) if elem.elem_type == "Notebook" else []
        if elem.elem_type == "Notebook":
            props.pop("active_tab", None)

        for b_elem, b_event, _ in bindings:
            if b_elem == elem and b_event == "command":
                props["command"] = f"self._on_{elem.elem_type}_{elem.elem_id}"

        if props.get("textvariable") == "":
            props.pop("textvariable", None)
        def_val = props.pop("default_value", None)
        tooltip_val = props.pop("tooltip", None)

        # Skip legacy fields unsupported by the target CTk widget, and use
        # raw tkinter option names (not ctk-style renames) for legacy
        # (non-CTk) widgets. See module-level CTK_UNSUPPORTED_PROPS /
        # LEGACY_RAW_PROP_OVERRIDE for details on why this is needed.
        unsupported = CTK_UNSUPPORTED_PROPS.get(elem.elem_type, set())
        legacy_raw = LEGACY_RAW_PROP_OVERRIDE.get(elem.elem_type, set())

        # Build property string
        prop_strs = []
        for k, v in props.items():
            if k == "font" and isinstance(v, list):
                v = tuple(v)  # see comment in CodeGenerator.generate()
            if k in unsupported:
                continue
            if k in legacy_raw:
                ctk_k = k  # keep original tkinter option name
            else:
                ctk_k = CTK_PROP_MAP.get(k)
                if ctk_k is None:
                    continue
            if CodeGenerator._is_ctk_widget(widget_class) and k in ("width", "height"):
                continue
            if k == "variable":
                if v:
                    prop_strs.append(f"variable=self.{v}")
                continue
            elif k == "textvariable":
                if v:
                    prop_strs.append(f"textvariable=self.{v}")
                continue
            elif k == "corner_radius":
                if v not in (None, ""):
                    try:
                        prop_strs.append(f"corner_radius={int(v)}")
                    except (TypeError, ValueError):
                        pass
                continue
            elif k == "command" and isinstance(v, str) and v.startswith("self."):
                prop_strs.append(f"command={v}")
            elif k == "values" and isinstance(v, list):
                prop_strs.append(f"values={repr(v)}")
            elif k in ("from_", "to", "onvalue", "offvalue"):
                prop_strs.append(f"{ctk_k}={v}")
            elif isinstance(v, str):
                prop_strs.append(f"{ctk_k}={json.dumps(v)}")
            elif isinstance(v, (int, float)):
                prop_strs.append(f"{ctk_k}={v}")
            else:
                prop_strs.append(f"{ctk_k}={repr(v)}")

        if elem.elem_type == "Scale" and "orient" not in props and "orientation" not in [p.split('=')[0] for p in prop_strs]:
            prop_strs.append("orientation='horizontal'")
        if elem.elem_type == "Progressbar" and "orient" not in props and "orientation" not in [p.split('=')[0] for p in prop_strs]:
            prop_strs.append("orientation='horizontal'")

        if CodeGenerator._is_ctk_widget(widget_class):
            prop_strs.append(f"width={elem.canvas_w}")
            prop_strs.append(f"height={elem.canvas_h}")

        prop_str = (", " + ", ".join(prop_strs)) if prop_strs else ""

        parent_name = "root"
        rel_x, rel_y = elem.x, elem.y
        if elem.parent_id is not None and elem.parent_id in by_id:
            parent_elem = by_id[elem.parent_id]
            if parent_elem.elem_type == "Notebook":
                tab_idx = elem.parent_tab if elem.parent_tab is not None else parent_elem.props.get(
                    "active_tab", 0
                    )
                tabs_count = len(parent_elem.props.get("tabs", ["Tab 1"])) or 1
                tab_idx = max(0, min(int(tab_idx or 0), tabs_count - 1))
                parent_name = f"self._elem_{parent_elem.elem_id}_tab_{tab_idx}"
            else:
                parent_name = f"self._elem_{parent_elem.elem_id}"
            rel_x = elem.x - parent_elem.x
            rel_y = elem.y - parent_elem.y

        if elem.elem_type == "Table":
            table_file = elem.props.get("file", "")
            table_sheet = elem.props.get("sheet", 0)
            columns_csv = elem.props.get("columns", "")
            table_height = int(elem.props.get("height", 8) or 8)

            lines = []
            lines.append(f"        columns = []")
            if columns_csv:
                cols = [c.strip() for c in columns_csv.split(",") if c.strip()]
                lines.append(f"        columns = {repr(cols)}")
            lines.append(
                f"        {var_name} = ttk.Treeview({parent_name}, columns=columns, show='headings', height={table_height})"
                )
            lines.append(f"        for col in columns:")
            lines.append(f"            {var_name}.heading(col, text=col)")
            lines.append(
                f"            {var_name}.column(col, width=100, anchor='w')"
                )
            if table_file:
                lines.append(f"        try:")
                lines.append(f"            import pandas as pd")
                if str(table_file).lower().endswith(('.xlsx', '.xls')):
                    lines.append(
                        f"            df = pd.read_excel({json.dumps(table_file)}, sheet_name={json.dumps(table_sheet) if table_sheet else 0})"
                        )
                else:
                    lines.append(
                        f"            df = pd.read_csv({json.dumps(table_file)})"
                        )
                lines.append(f"            if not columns:")
                lines.append(f"                columns = list(df.columns)")
                lines.append(f"                for col in columns:")
                lines.append(
                    f"                    {var_name}.heading(col, text=col)"
                    )
                lines.append(
                    f"                    {var_name}.column(col, width=100, anchor='w')"
                    )
                lines.append(
                    f"            for _, row in df.head(10).iterrows():"
                    )
                lines.append(
                    f"                {var_name}.insert('', 'end', values=list(row))"
                    )
                lines.append(f"        except Exception as e:")
                lines.append(f"            print('Table load error:', e)")
            widget_line = "\n".join(lines)
            place_line = f"        {var_name}.place(x={rel_x}, y={rel_y}, width={elem.canvas_w}, height={elem.canvas_h})"
            return widget_line, place_line, []

        if elem.elem_type == "Image":
            image_path = elem.props.get("image_path", "")
            if image_path and PIL_AVAILABLE:
                lines = []
                lines.append(f"        img_path = {json.dumps(image_path)}")
                lines.append(f"        if not os.path.isabs(img_path):")
                lines.append(f"            img_path = os.path.join(os.path.dirname(__file__), img_path)")
                lines.append(f"        try:")
                lines.append(f"            pil_image = Image.open(img_path)")
                lines.append(f"            ctk_image = ctk.CTkImage(pil_image, size=({elem.canvas_w}, {elem.canvas_h}))")
                lines.append(f"            {var_name} = ctk.CTkLabel({parent_name}, image=ctk_image, text='', width={elem.canvas_w}, height={elem.canvas_h})")
                lines.append(f"            {var_name}.image = ctk_image  # keep reference")
                lines.append(f"        except Exception as e:")
                lines.append(f"            {var_name} = ctk.CTkLabel({parent_name}, text='[Image Error]', fg_color='lightgray', width={elem.canvas_w}, height={elem.canvas_h})")
                widget_line = "\n".join(lines)
            else:
                widget_line = f'        {var_name} = ctk.CTkLabel({parent_name}, text="[Image]", fg_color="lightgray", width={elem.canvas_w}, height={elem.canvas_h})'
            place_line = f"        {var_name}.place(x={rel_x}, y={rel_y})"
            return widget_line, place_line, []

        widget_line = f"        {var_name} = {widget_class}({parent_name}{prop_str})"

        if elem.elem_type == "Notebook":
            if not notebook_tabs:
                notebook_tabs = ["Tab 1"]
            for i, tab_title in enumerate(notebook_tabs):
                extra_lines.append(f"        {var_name}_tab_{i} = {var_name}.add({json.dumps(str(tab_title))})")
                extra_lines.append(f"        self._elem_{elem.elem_id}_tab_{i} = {var_name}_tab_{i}")
            active_tab = int(elem.props.get("active_tab", 0) or 0)
            active_tab = max(0, min(active_tab, len(notebook_tabs) - 1))
            extra_lines.append(f"        {var_name}.set({json.dumps(notebook_tabs[active_tab])})")
        elif elem.elem_type == "LabelFrame":
            label_text = elem.props.get("text", "LabelFrame")
            extra_lines.append(f"        # LabelFrame title")
            extra_lines.append(f"        {var_name}_label = ctk.CTkLabel({var_name}, text={json.dumps(label_text)})")
            extra_lines.append(f"        {var_name}_label.place(x=10, y=-10)")
        elif elem.elem_type == "Progressbar":
            try:
                maximum = float(elem.props.get("maximum", 100) or 100)
                value = float(elem.props.get("value", 0) or 0)
                fraction = max(0.0, min(1.0, value / maximum)) if maximum else 0.0
                extra_lines.append(f"        {var_name}.set({fraction})")
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        if def_val is not None and str(def_val).strip() != "":
            if elem.elem_type == "Checkbutton":
                var_name_chk = copy.deepcopy(elem.props).get("variable")
                if var_name_chk:
                    extra_lines.append(
                        f"        self.{var_name_chk}.set({json.dumps(def_val)})"
                        )
                elif str(def_val).lower() in ("1", "true", "yes"):
                    extra_lines.append(f"        {var_name}.select()")
            elif elem.elem_type in ("Entry", "Spinbox"):
                extra_lines.append(
                    f"        {var_name}.insert(0, {json.dumps(str(def_val))})"
                    )
            elif elem.elem_type == "Combobox":
                extra_lines.append(
                    f"        {var_name}.set({json.dumps(str(def_val))})"
                    )
            elif elem.elem_type == "Scale":
                try:
                    num_val = float(def_val) if "." in str(def_val) else int(def_val)
                    extra_lines.append(f"        {var_name}.set({num_val})")
                except (ValueError, TypeError):
                    pass

        if elem.elem_type == "Listbox" and listbox_items:
            for item in listbox_items:
                extra_lines.append(
                    f"        {var_name}.insert('end', {json.dumps(item)})"
                    )

        if tooltip_val:
            extra_lines.append(
                f"        _ToolTip({var_name}, {json.dumps(str(tooltip_val))})"
                )

        if CodeGenerator._is_ctk_widget(widget_class):
            place_line = f"        {var_name}.place(x={rel_x}, y={rel_y})"
        else:
            place_line = f"        {var_name}.place(x={rel_x}, y={rel_y}, width={elem.canvas_w}, height={elem.canvas_h})"

        return widget_line, place_line, extra_lines


# ─── CanvasRenderer ─────────────────────────────────────────────────────────

class CanvasRenderer:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.zoom = 1.0

    def _scaled_font(self, font):
        z = getattr(self, "zoom", 1.0)
        if z == 1.0:
            return font
        if isinstance(font, (tuple, list)) and len(font) >= 2:
            try:
                size = int(round(abs(float(font[1])) * z)) or 1
                return (font[0], size) + tuple(font[2:])
            except (ValueError, TypeError):
                return font
        return font

    def _get_valid_color(self, color_name: str, fallback: str) -> str:
        if not color_name:
            return fallback
        try:
            self.canvas.winfo_rgb(color_name)
            return color_name
        except tk.TclError:
            return fallback

    def draw_grid(self, width: int, height: int) -> None:
        self.canvas.delete("grid")
        z = getattr(self, "zoom", 1.0)
        sw, sh = int(width * z), int(height * z)
        step = max(4, int(round(20 * z)))
        for x in range(0, sw + 1, step):
            self.canvas.create_line(x, 0, x, sh, fill="#E8E8E8",
                                     tags="grid"
                                     )
        for y in range(0, sh + 1, step):
            self.canvas.create_line(0, y, sw, y, fill="#E8E8E8",
                                     tags="grid"
                                     )
        self.canvas.tag_lower("grid")

    def draw_element(self, elem: DesignElement) -> None:
        z = getattr(self, "zoom", 1.0)
        x, y, w, h = int(elem.x * z), int(elem.y * z), int(
            elem.canvas_w * z
            ), int(elem.canvas_h * z)
        bg = self._get_valid_color(elem.props.get("bg"),
                                    ELEMENT_TYPES[elem.elem_type]["tile_bg"]
                                    )
        fg = self._get_valid_color(elem.props.get("fg"),
                                    ELEMENT_TYPES[elem.elem_type]["tile_fg"]
                                    )
        font = self._scaled_font(elem.props.get("font") or ("Segoe UI", 9))
        outline = "#FF6B35" if elem.selected else "#B0BEC5"
        width_outline = 2 if elem.selected else 1

        self.erase_element(elem)

        draw_func = getattr(self, f"_draw_{elem.elem_type.lower()}",
                             self._draw_fallback
                             )
        draw_func(elem, x, y, w, h, bg, fg, font, outline, width_outline)

        elem.handle_ids = {}
        if elem.selected:
            mx, my = x + w // 2, y + h // 2
            handle_pts = {
                "NW": (x, y), "N": (mx, y), "NE": (x + w, y), "E": (x + w, my),
                "SE": (x + w, y + h), "S": (mx, y + h), "SW": (x, y + h),
                "W": (x, my),
            }
            for name, (hx, hy) in handle_pts.items():
                hid = self.canvas.create_rectangle(
                    hx - HANDLE_HALF, hy - HANDLE_HALF, hx + HANDLE_HALF,
                    hy + HANDLE_HALF,
                    fill="#FF6B35", outline="#FFFFFF", width=2,
                    tags=("handle", f"handle_{elem.elem_id}_{name}")
                )
                elem.handle_ids[name] = hid

            del_x, del_y = x + w + 15, y - 15
            hid_bg = self.canvas.create_rectangle(del_x - 9, del_y - 9,
                                                   del_x + 9, del_y + 9,
                                                   fill="#E53935",
                                                   outline="#FFFFFF",
                                                   width=2, tags=("handle",
                                                                  f"del_{elem.elem_id}")
                                                   )
            hid_l1 = self.canvas.create_line(del_x - 4, del_y - 4, del_x + 4,
                                              del_y + 4, fill="white",
                                              width=2, tags=("handle",
                                                             f"del_{elem.elem_id}")
                                             )
            hid_l2 = self.canvas.create_line(del_x - 4, del_y + 4, del_x + 4,
                                              del_y - 4, fill="white",
                                              width=2, tags=("handle",
                                                             f"del_{elem.elem_id}")
                                             )
            elem.handle_ids["DEL"] = hid_bg
            elem.handle_ids["DEL_L1"] = hid_l1
            elem.handle_ids["DEL_L2"] = hid_l2

            id_lbl_bg = self.canvas.create_rectangle(x + w // 2 - 20, y - 20,
                                                      x + w // 2 + 20, y - 6,
                                                      fill="#1976D2",
                                                      outline="#FFFFFF",
                                                      width=2,
                                                      tags=("handle",
                                                            f"id_{elem.elem_id}")
                                                     )
            id_lbl = self.canvas.create_text(x + w // 2, y - 15,
                                              text=f"ID:{elem.elem_id}",
                                              fill="white",
                                              font=("Segoe UI", 8, "bold"),
                                              tags=("handle",
                                                    f"id_{elem.elem_id}")
                                             )
            elem.handle_ids["ID_BG"] = id_lbl_bg
            elem.handle_ids["ID"] = id_lbl

    def _draw_label(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        justify = elem.props.get("justify", "center")
        anchor_map = {"left": "w", "center": "center", "right": "e"}
        anchor = anchor_map.get(justify, "center")
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font, anchor=anchor
                                     )

    def _draw_entry(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        text = elem.props.get("textvariable") or elem.display_label
        self._render_text_on_canvas(elem, x + 4, y, w - 8, h, text, fg, font,
                                     anchor="w"
                                     )

    def _draw_button(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font
                                     )

    def _draw_radiobutton(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx = x + 20
        cy = y + h // 2
        r = 6
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 outline="#757575", fill=bg,
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        if elem.props.get("value") == 1:
            self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3,
                                     fill="#1976D2",
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        self._render_text_on_canvas(elem, x + 25, y, w - 25, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_checkbutton(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx = x + 16
        cy = y + h // 2
        size = 10
        self.canvas.create_rectangle(cx - size // 2, cy - size // 2,
                                      cx + size // 2, cy + size // 2,
                                      outline="#757575", fill=bg,
                                      tags=("element", f"elem_{elem.elem_id}")
                                     )
        if elem.props.get("onvalue") == 1:
            self.canvas.create_line(cx - 3, cy, cx, cy + 3, cx + 5, cy - 4,
                                     fill="#1976D2", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        self._render_text_on_canvas(elem, x + 25, y, w - 25, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_scale(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        track_y = y + h // 2
        track_len = w - 20
        self.canvas.create_line(x + 10, track_y, x + 10 + track_len, track_y,
                                 fill="#B0BEC5", width=4,
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        thumb_x = x + 10 + int(track_len * 0.3)
        self.canvas.create_oval(thumb_x - 6, track_y - 6, thumb_x + 6,
                                 track_y + 6, fill="#1976D2",
                                 outline="#1976D2",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        val = elem.props.get("to", 100) * 0.3
        self.canvas.create_text(x + w - 5, track_y - 10,
                                 text=str(int(val)), anchor="e",
                                 fill="#212121",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_combobox(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        arrow_x = x + w - 18
        arrow_y = y + h // 2
        self.canvas.create_polygon(arrow_x - 5, arrow_y - 4, arrow_x + 5,
                                    arrow_y - 4, arrow_x, arrow_y + 4,
                                    fill="#757575",
                                    tags=("element", f"elem_{elem.elem_id}")
                                    )
        self._render_text_on_canvas(elem, x + 4, y, w - 22, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_spinbox(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        arrow_x = x + w - 16
        arrow_y = y + h // 2
        self.canvas.create_polygon(arrow_x - 6, arrow_y - 2, arrow_x + 6,
                                    arrow_y - 2, arrow_x, arrow_y - 8,
                                    fill="#757575",
                                    tags=("element", f"elem_{elem.elem_id}")
                                    )
        self.canvas.create_polygon(arrow_x - 6, arrow_y + 2, arrow_x + 6,
                                    arrow_y + 2, arrow_x, arrow_y + 8,
                                    fill="#757575",
                                    tags=("element", f"elem_{elem.elem_id}")
                                    )
        self._render_text_on_canvas(elem, x + 4, y, w - 20, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_listbox(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        for i in range(3):
            line_y = y + 12 + i * 20
            if line_y < y + h - 5:
                self.canvas.create_line(x + 5, line_y, x + w - 5, line_y,
                                         fill="#E0E0E0", tags=("element",
                                                               f"elem_{elem.elem_id}")
                                         )

    def _draw_text(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        for i in range(min(max(1, h // 22), 8)):
            line_y = y + 15 + i * 22
            if line_y < y + h - 5:
                self.canvas.create_line(x + 5, line_y, x + w - 5, line_y,
                                         fill="#E0E0E0", tags=("element",
                                                               f"elem_{elem.elem_id}")
                                         )

    def _draw_image(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        image_path = elem.props.get("image_path", "")
        if image_path and PIL_AVAILABLE:
            try:
                img = Image.open(image_path)
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                elem._image_tk = tk_img
                self.canvas.create_image(x + w//2, y + h//2, image=tk_img,
                                         tags=("element", f"elem_{elem.elem_id}"))
                self.canvas.create_rectangle(x, y, x + w, y + h,
                                             outline=outline, width=outline_w,
                                             tags=("element", f"elem_{elem.elem_id}"))
                return
            except Exception:
                pass
        self.canvas.create_rectangle(
            x, y, x + w, y + h, fill="#ECEFF1", outline=outline,
            width=outline_w,
            dash=(4, 3), tags=("element", f"elem_{elem.elem_id}")
        )
        emoji_size = max(12, min(w, h) // 3)
        self.canvas.create_text(
            x + w // 2, y + h // 2 - 6, text="🖼️",
            font=("Segoe UI Emoji", emoji_size),
            tags=("element", f"elem_{elem.elem_id}")
        )
        caption = elem.props.get("text", "") or ""
        if caption:
            self.canvas.create_text(
                x + w // 2, y + h - 12, text=str(caption), fill=fg,
                font=font,
                tags=("element", f"elem_{elem.elem_id}")
            )

    def _draw_canvas(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        self.canvas.create_rectangle(x + 10, y + 10, x + w - 10, y + h - 10,
                                      outline="#B0BEC5",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_line(x + 15, y + 15, x + w - 15, y + h - 15,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_progressbar(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        value = elem.props.get("value", 40)
        max_val = elem.props.get("maximum", 100)
        orient = elem.props.get("orient", "horizontal")
        frac = min(1.0, max(0, value / max_val))
        if orient == "vertical":
            bar_h = int((h - 4) * frac)
            self.canvas.create_rectangle(x + 2, y + h - 2 - bar_h, x + w - 2,
                                          y + h - 2, fill="#1976D2",
                                          outline="", tags=("element",
                                                            f"elem_{elem.elem_id}")
                                          )
        else:
            bar_w = int((w - 4) * frac)
            self.canvas.create_rectangle(x + 2, y + 2, x + 2 + bar_w,
                                          y + h - 2, fill="#1976D2",
                                          outline="", tags=("element",
                                                            f"elem_{elem.elem_id}")
                                          )

    def _draw_scrollbar(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        slider_h = h // 3
        slider_y = y + (h - slider_h) // 2
        self.canvas.create_rectangle(x + 2, slider_y, x + w - 2,
                                      slider_y + slider_h, fill="#B0BEC5",
                                      outline="#78909C",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )

    def _draw_frame(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        relief = elem.props.get("relief", "groove")
        if relief == "groove":
            self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        elif relief == "raised":
            self._draw_raised_rect(elem, x, y, w, h, bg, outline, outline_w)
        elif relief == "sunken":
            self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        else:
            self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)

    def _draw_labelframe(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        text = elem.props.get("text", "LabelFrame")
        self.canvas.create_rectangle(x + 10, y - 6,
                                      x + min(w - 10, 10 + len(text) * 8),
                                      y + 6, fill=bg, outline="",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_text(x + 14, y, text=text, fill=fg, font=font,
                                 anchor="w",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_notebook(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self.canvas.create_rectangle(x, y + 26, x + w, y + h, fill=bg,
                                      outline="#B0BEC5",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        tabs = elem.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
        active = int(elem.props.get("active_tab", 0) or 0)
        active = max(0, min(active, len(tabs) - 1))
        tab_width = max(58, min(120, int(
            (w - 10) / max(1, min(len(tabs), 4))
            )
                                  )
                         )
        tab_x = x + 5
        for i, title in enumerate(tabs):
            if tab_x >= x + w - 4:
                break
            tw = min(tab_width, x + w - 4 - tab_x)
            fill = "#FFFFFF" if i == active else "#F5F5F5"
            text_fill = "#1976D2" if i == active else "#757575"
            self.canvas.create_rectangle(tab_x, y + 4, tab_x + tw, y + 26,
                                          fill=fill, outline="#B0BEC5",
                                          tags=("element",
                                                f"elem_{elem.elem_id}")
                                          )
            self.canvas.create_text(tab_x + tw / 2, y + 15,
                                     text=str(title), fill=text_fill,
                                     font=font,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
            tab_x += tw + 3

    def _draw_panedwindow(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        orient = elem.props.get("orient", "horizontal")
        if orient == "vertical":
            sash_y = y + h // 2
            self.canvas.create_line(x + 10, sash_y, x + w - 10, sash_y,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        else:
            sash_x = x + w // 2
            self.canvas.create_line(sash_x, y + 10, sash_x, y + h - 10,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )

    def _draw_separator(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        orient = elem.props.get("orient", "horizontal")
        if orient == "vertical":
            self.canvas.create_line(x + w // 2, y, x + w // 2, y + h,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        else:
            self.canvas.create_line(x, y + h // 2, x + w, y + h // 2,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )

    def _draw_table(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        cols = elem.props.get("columns", "")
        if cols:
            columns = [c.strip() for c in cols.split(",") if c.strip()]
        else:
            columns = ["A", "B", "C"]
        n_cols = max(1, len(columns))
        col_w = w / n_cols
        row_h = 24
        self.canvas.create_rectangle(x, y, x + w, y + row_h, fill="#E3F2FD",
                                      outline="#B0BEC5",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        for i, col in enumerate(columns):
            self.canvas.create_line(x + (i + 1) * col_w, y,
                                     x + (i + 1) * col_w, y + row_h,
                                     fill="#B0BEC5",
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
            self.canvas.create_text(x + i * col_w + col_w / 2, y + row_h / 2,
                                     text=col, fill="#1976D2", font=font,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        rows = min(5, max(0, int(h - row_h) // 20))
        for r in range(rows):
            ry = y + row_h + r * 20
            self.canvas.create_rectangle(x, ry, x + w, ry + 20,
                                          outline="#E0E0E0",
                                          tags=("element",
                                                f"elem_{elem.elem_id}")
                                          )

    def _draw_fallback(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font
                                     )

    def _draw_flat_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        elem.rect_id = self.canvas.create_rectangle(
            x, y, x + w, y + h, fill=fill, outline=outline,
            width=outline_w,
            tags=("element", f"elem_{elem.elem_id}")
        )

    def _draw_sunken_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill,
                                      outline=outline, width=outline_w,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_line(x + 1, y + 1, x + w - 2, y + 1,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 1, y + 1, x + 1, y + h - 2,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + w - 2, y + 2, x + w - 2, y + h - 2,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 2, y + h - 2, x + w - 2, y + h - 2,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_raised_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill,
                                      outline=outline, width=outline_w,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_line(x + 1, y + 1, x + w - 2, y + 1,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 1, y + 1, x + 1, y + h - 2,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + w - 2, y + 2, x + w - 2, y + h - 2,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 2, y + h - 2, x + w - 2, y + h - 2,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_groove_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill,
                                      outline=outline, width=outline_w,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_rectangle(x + 2, y + 2, x + w - 2, y + h - 2,
                                      outline="#B0BEC5", width=1,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )

    def _render_text_on_canvas(
            self, elem, x, y, w, h, text, color, font, anchor="center"
            ):
        if anchor == "center":
            elem.text_id = self.canvas.create_text(
                x + w // 2, y + h // 2, text=text, fill=color, font=font,
                tags=("element", f"elem_{elem.elem_id}")
            )
        elif anchor == "w":
            elem.text_id = self.canvas.create_text(
                x + 2, y + h // 2, text=text, fill=color, font=font,
                anchor="w",
                tags=("element", f"elem_{elem.elem_id}")
            )
        elif anchor == "e":
            elem.text_id = self.canvas.create_text(
                x + w - 2, y + h // 2, text=text, fill=color, font=font,
                anchor="e",
                tags=("element", f"elem_{elem.elem_id}")
            )

    def erase_element(self, elem: DesignElement) -> None:
        self.canvas.delete(f"elem_{elem.elem_id}")
        for hid in elem.handle_ids.values():
            self.canvas.delete(hid)
        elem.rect_id = 0
        elem.text_id = 0
        elem.handle_ids = {}
        elem._image_tk = None

    def redraw_element(self, elem: DesignElement) -> None:
        self.erase_element(elem)
        self.draw_element(elem)

    def move_element(self, elem: DesignElement, dx: int, dy: int) -> None:
        """Translate an already-drawn element's existing canvas items in
        place, instead of erasing and recreating them. Used during
        interactive dragging so a mouse-move doesn't pay the cost of
        color/font revalidation and widget-specific shape reconstruction
        on every event. Safe because a pure move never changes size, text,
        or color — only position — so the existing items remain correct,
        just shifted. dx/dy are in logical (unzoomed) canvas units.
        """
        if dx == 0 and dy == 0:
            return
        z = getattr(self, "zoom", 1.0)
        sdx, sdy = dx * z, dy * z
        self.canvas.move(f"elem_{elem.elem_id}", sdx, sdy)
        for hid in elem.handle_ids.values():
            self.canvas.move(hid, sdx, sdy)

    def snap_to_grid(self, x: int, y: int) -> Tuple[int, int]:
        return int(round(x / GRID_SIZE) * GRID_SIZE), int(
            round(y / GRID_SIZE) * GRID_SIZE
            )


# ─── GUIBuilderApp ──────────────────────────────────────────────────────────

class GUIBuilderApp:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self._setup_styles()
        self.window_title = "My Application"
        self.current_file_path: Optional[str] = None
        self._is_modified = False
        self.full_code: Optional[str] = None
        self._current_code: str = ""

        self._update_window_title_display()
        self.root.geometry("1400x800")
        self.root.minsize(1000, 600)

        self._zoom = 1.0

        self.root.update()
        try:
            if platform.system() in ("Windows", "Darwin"):
                self.root.state('zoomed')
            else:
                self.root.attributes('-zoomed', True)
        except tk.TclError:
            try:
                self.root.state('zoomed')
            except tk.TclError:
                pass

        self.CANVAS_W = 800
        self.CANVAS_H = 600
        self.CANVAS_BG = "#FFFFFF"

        self.canvas_imports = "import tkinter as tk\nfrom tkinter import ttk"

        self.elements: List[DesignElement] = []
        self.selected_elems: List[DesignElement] = []
        self.clipboard: List[DesignElement] = []
        # id -> element and parent_id -> [children] indexes, kept in sync by
        # _rebuild_index() (called after any add/remove/clear of self.elements).
        # These replace O(n) linear scans of self.elements that previously
        # happened inside per-element loops (O(n^2) on redraw/reorder/etc).
        self._by_id: Dict[int, DesignElement] = {}
        self._children_by_parent: Dict[int, List[DesignElement]] = {}

        self.next_id = 1
        self.reusable_ids = set()

        self.undo_stack = []
        self.redo_stack = []

        self.pending_type: Optional[str] = None
        self.code_visible = False
        self._code_display_timer = None
        self.prop_context_var = tk.StringVar(value="Container: None")
        self._tooltip_win = None
        self._toolbox_compact = False

        self.drag_mode = "none"
        self.drag_elem = None
        self.mouse_down_pos = None
        self.elem_origs = {}
        self.active_handle = None
        self.selection_box_id = None
        self._last_move_delta = (0, 0)

        self._build_ui()
        self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)

        self.root.bind("<Control-c>", self._copy_elements)
        self.root.bind("<Control-v>", self._paste_elements)
        self.root.bind("<Delete>", self._delete_selected)
        self.root.bind("<Control-z>", self._undo)
        self.root.bind("<Control-y>", self._redo)
        self.root.bind("<Control-Z>", self._redo)

        self.root.bind("<Control-s>", lambda e: self._save_design())
        self.root.bind("<Control-o>", lambda e: self._load_design())
        self.root.bind("<Control-n>", lambda e: self._new_design())

        self.root.bind("<Up>", self._move_with_keys)
        self.root.bind("<Down>", self._move_with_keys)
        self.root.bind("<Left>", self._move_with_keys)
        self.root.bind("<Right>", self._move_with_keys)

        self.canvas.bind("<Control-a>", self._select_all)

        # Tooltip on canvas hover
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Leave>", self._on_canvas_leave)

        self._update_code()
        self._update_element_count()
        self._update_status(
            "Ready — pick a tool and click canvas, or double-click elements to edit code."
            )
        self._show_properties(None)

        self._save_state()

    def _rebuild_index(self):
        """Rebuild the id->element and parent_id->children lookup tables.
        Call this once after any code that adds/removes/replaces entries in
        self.elements. It's O(n), which is far cheaper than the O(n) linear
        scans it replaces when those scans happen inside a per-element loop.
        """
        self._by_id = {e.elem_id: e for e in self.elements}
        children: Dict[int, List[DesignElement]] = {}
        for e in self.elements:
            if e.parent_id is not None:
                children.setdefault(e.parent_id, []).append(e)
        self._children_by_parent = children

    def _setup_styles(self):
        style = ttk.Style()
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=9)
        self.root.option_add("*Font", default_font)

        bg = "#F5F5F5"
        fg = "#212121"
        select_bg = "#1976D2"

        # The native ttk themes ("vista"/"xpnative" on Windows, "aqua" on
        # macOS) ignore most style.configure() calls for widgets like
        # Scrollbar and PanedWindow, which is why those widgets used to look
        # visually disconnected from CustomTkinter's flat design elsewhere in
        # the app (native 3D sash/scrollbar chrome next to flat CTk buttons).
        # "clam" is a theme-able ttk theme that actually honors the color/
        # relief overrides below, so switch to it before configuring styles.
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass  # fall back to whatever default theme is available

        style.configure("Treeview", background="white", foreground=fg,
                         fieldbackground="white", rowheight=24
                         )
        style.map("Treeview", background=[('selected', select_bg)])
        style.configure("Treeview.Heading", background=bg, foreground=fg,
                         relief="flat", borderwidth=0
                         )

        # Match the flat CTk look for the ttk widgets that have no CTk
        # equivalent and are used in the builder's own chrome (main pane
        # splitters and canvas/code-editor scrollbars).
        style.configure("TPanedWindow", background=bg)
        style.configure("Sash", sashthickness=6, gripcount=0,
                         background=bg, lightcolor=bg, darkcolor="#D0D0D0"
                         )
        for orient in ("Vertical", "Horizontal"):
            name = f"{orient}.TScrollbar"
            style.configure(name, background=bg, troughcolor="#EDEDED",
                             bordercolor=bg, arrowcolor=fg,
                             relief="flat", borderwidth=0
                             )
            style.map(name,
                      background=[("active", "#D5D5D5"), ("pressed", "#C0C0C0")]
                      )

    def _update_window_title_display(self):
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled.tvd"
        dirty_marker = "*" if self._is_modified else ""
        self.root.title(
            f"Tkinter Visual Designer - [{filename}{dirty_marker}]"
            )

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_toolbar()

        self.v_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.v_paned.grid(row=1, column=0, sticky="nsew")

        self.main_paned = ttk.PanedWindow(self.v_paned,
                                           orient=tk.HORIZONTAL
                                           )
        self.v_paned.add(self.main_paned, weight=3)

        self.toolbox_frame = ctk.CTkFrame(self.main_paned, width=220,
                                           corner_radius=0
                                           )
        self.toolbox_frame.pack_propagate(False)
        self.main_paned.add(self.toolbox_frame, weight=0)
        self._build_toolbox()

        center_frame = ctk.CTkFrame(self.main_paned, corner_radius=0)
        self.main_paned.add(center_frame, weight=1)

        self.canvas_scroll_y = ttk.Scrollbar(center_frame,
                                              orient=tk.VERTICAL
                                              )
        self.canvas_scroll_x = ttk.Scrollbar(center_frame,
                                              orient=tk.HORIZONTAL
                                              )
        self.canvas = tk.Canvas(
            center_frame, bg=self.CANVAS_BG, width=self.CANVAS_W,
            height=self.CANVAS_H,
            yscrollcommand=self.canvas_scroll_y.set,
            xscrollcommand=self.canvas_scroll_x.set,
            takefocus=1, highlightthickness=0, relief="flat"
        )
        self.canvas_scroll_y.config(command=self.canvas.yview)
        self.canvas_scroll_x.config(command=self.canvas.xview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas_scroll_y.grid(row=0, column=1, sticky="ns")
        self.canvas_scroll_x.grid(row=1, column=0, sticky="ew")
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        self.canvas.config(
            scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H)
            )
        self.renderer = CanvasRenderer(self.canvas)
        self.renderer.zoom = self._zoom

        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_zoom)
        self.canvas.bind("<Control-Button-4>", self._on_ctrl_zoom)
        self.canvas.bind("<Control-Button-5>", self._on_ctrl_zoom)

        self.prop_frame = ctk.CTkFrame(self.main_paned, width=400,
                                        corner_radius=0
                                        )
        self.prop_frame.pack_propagate(False)
        self.main_paned.add(self.prop_frame, weight=0)
        self._build_property_inspector()

        self.code_frame = ctk.CTkFrame(self.v_paned, corner_radius=0)
        self.code_frame.grid_rowconfigure(0, weight=0)
        self.code_frame.grid_rowconfigure(1, weight=1)
        self.code_frame.grid_columnconfigure(0, weight=1)

        code_header = ctk.CTkFrame(self.code_frame, corner_radius=0)
        code_header.grid(row=0, column=0, sticky="ew", padx=2,
                          pady=2
                          )
        ctk.CTkLabel(code_header, text="LIVE CODE",
                      font=ctk.CTkFont(size=10, weight="bold")
                      ).pack(side=tk.LEFT, padx=5)

        self.code_text = ctk.CTkTextbox(
            self.code_frame, font=("Consolas", 13), wrap="none",
            text_color="#1E1E1E", fg_color="#FAFAFA",
            activate_scrollbars=True
        )
        self.code_text.grid(row=1, column=0, sticky="nsew", padx=2,
                             pady=2
                             )
        self.code_text.configure(state="disabled")

        self.status_var = tk.StringVar()
        self.count_var = tk.StringVar()
        self.zoom_var = tk.StringVar(value="Zoom: 100%")
        status_bar = ctk.CTkFrame(self.root, corner_radius=0)
        status_bar.grid(row=2, column=0, sticky="ew")
        ctk.CTkLabel(status_bar, textvariable=self.status_var, anchor="w"
                      ).pack(side=tk.LEFT, fill=tk.X, expand=True,
                              padx=4, pady=2
                              )
        ctk.CTkLabel(status_bar, textvariable=self.count_var, anchor="e"
                      ).pack(side=tk.RIGHT, padx=4, pady=2)
        ctk.CTkLabel(status_bar, textvariable=self.zoom_var, anchor="e"
                      ).pack(side=tk.RIGHT, padx=10, pady=2)

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self.root, corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=4)
        toolbar.columnconfigure(0, weight=1)

        def _sep():
            ctk.CTkFrame(toolbar, width=2, height=28).pack(
                side=tk.LEFT, fill=tk.Y, padx=5, pady=2
                )

        ctk.CTkButton(toolbar, text="📄 New Design",
                       command=self._new_design, width=126, height=28
                       ).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(toolbar, text="📂 Load Design",
                       command=self._load_design, width=134, height=28
                       ).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(toolbar, text="💾 Save Design",
                       command=self._save_design, width=134, height=28
                       ).pack(side=tk.LEFT, padx=2)
        _sep()
        undo_btn = ctk.CTkButton(toolbar, text=" ↶ ", command=self._undo,
                                  width=35, height=28,
                                  font=("Helv", 18, "bold")
                                  )
        undo_btn.pack(side=tk.LEFT, padx=2)
        undo_btn.bind("<Enter>", lambda e, b=undo_btn: self._show_tooltip(b,
                                                                          "Undo (Ctrl+Z)"
                                                                          )
                       )
        undo_btn.bind("<Leave>", self._hide_tooltip)
        redo_btn = ctk.CTkButton(toolbar, text=" ↷ ", command=self._redo,
                                  width=35, height=28,
                                  font=("Helv", 18, "bold")
                                  )
        redo_btn.pack(side=tk.LEFT, padx=2)
        redo_btn.bind("<Enter>", lambda e, b=redo_btn: self._show_tooltip(b,
                                                                          "Redo (Ctrl+Y)"
                                                                          )
                       )
        redo_btn.bind("<Leave>", self._hide_tooltip)
        _sep()
        ctk.CTkButton(toolbar, text="🗑️ Delete",
                       command=self._delete_selected, width=100, height=28
                       ).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(toolbar, text="🧹 Clear Canvas",
                       command=self._clear_all, width=143, height=28
                       ).pack(side=tk.LEFT, padx=2)
        _sep()

        ctk.CTkButton(toolbar, text="📋 Copy Code", command=self._copy_code,
                       width=117, height=28
                       ).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(toolbar, text="▶ Run Preview",
                       command=self._run_preview, width=134, height=28
                       ).pack(side=tk.LEFT, padx=2)
        _sep()
        ctk.CTkButton(toolbar, text="👁️ Toggle Code",
                       command=self._toggle_code_view, width=143,
                       height=28
                       ).pack(side=tk.LEFT, padx=2)

    def _toggle_code_view(self):
        if self.code_visible:
            self.v_paned.forget(self.code_frame)
            self.code_visible = False
            self._update_status("Live code section hidden.")
        else:
            self.v_paned.add(self.code_frame, weight=1)
            self.code_visible = True
            self._update_status("Live code section visible.")

    def _build_toolbox(self):
        header = ctk.CTkFrame(self.toolbox_frame, fg_color="transparent")
        header.pack(fill=tk.X, pady=(5, 4))
        ctk.CTkLabel(header, text="TOOLBOX",
                      font=ctk.CTkFont(size=10, weight="bold")
                      ).pack(side=tk.LEFT, padx=6)
        self._toolbox_toggle_btn = ctk.CTkButton(
            header, text="⊞ Icons", width=70, height=22,
            font=ctk.CTkFont(size=10), command=self._toggle_toolbox_mode
        )
        self._toolbox_toggle_btn.pack(side=tk.RIGHT, padx=6)

        self.toolbox_items_container = ctk.CTkScrollableFrame(self.toolbox_frame,
                                                               fg_color="transparent"
                                                               )
        self.toolbox_items_container.pack(fill=tk.BOTH, expand=True, padx=2,
                                          pady=2)

        self._toolbox_items = {}  # name -> (frame, icon_lbl, name_lbl)
        self._toolbox_buttons = {}  # name -> frame
        self._toolbox_category_frames = {}  # cat -> (header_lbl, items_frame)

        categories = {}
        for name, spec in ELEMENT_TYPES.items():
            cat = spec.get("category", "Other")
            categories.setdefault(cat, []).append((name, spec))

        for cat in sorted(categories.keys()):
            # Each category gets its own always-packed wrapper. The header
            # label lives directly in this wrapper (always packed). The
            # items live in a dedicated sub-frame that we can freely switch
            # between pack (list mode) and grid (compact mode) without ever
            # mixing geometry managers with sibling widgets.
            cat_wrapper = ctk.CTkFrame(self.toolbox_items_container,
                                        fg_color="transparent")
            cat_wrapper.pack(fill=tk.X, padx=0, pady=0)

            header_lbl = ctk.CTkLabel(cat_wrapper, text=cat,
                          font=ctk.CTkFont(size=9, weight="bold"),
                          anchor="w"
                          )
            header_lbl.pack(anchor=tk.W, padx=5, pady=(8, 1))

            items_frame = ctk.CTkFrame(cat_wrapper, fg_color="transparent")
            items_frame.pack(fill=tk.X, padx=0, pady=0)

            self._toolbox_category_frames[cat] = (header_lbl, items_frame)

            for name, spec in sorted(categories[cat], key=lambda x: x[0]):
                display_str = spec["display"]
                parts = display_str.split(" ", 1)
                icon = parts[0] if len(parts) > 1 else ""
                elem_name = parts[1] if len(parts) > 1 else display_str

                item_frame = ctk.CTkFrame(items_frame, cursor="hand2",
                                           corner_radius=6,
                                           fg_color=TOOLBOX_NORMAL_COLOR
                                           )
                item_frame.pack(fill=tk.X, padx=5, pady=1)

                lbl_icon = ctk.CTkLabel(item_frame, text=icon, anchor="w",
                                        font=ctk.CTkFont(size=12))
                lbl_icon.pack(side=tk.LEFT, padx=6, pady=4)

                lbl_name = ctk.CTkLabel(item_frame, text=elem_name,
                                         anchor="e")
                lbl_name.pack(side=tk.RIGHT, padx=6, pady=4)

                def on_click(e, t=name):
                    self._tool_selected(t)

                def on_enter(e, f=item_frame, tip=elem_name):
                    f.configure(fg_color=TOOLBOX_HOVER_COLOR)
                    if self._toolbox_compact:
                        self._show_tooltip(f, tip)

                def on_leave(e, f=item_frame):
                    f.configure(fg_color=TOOLBOX_NORMAL_COLOR)
                    self._hide_tooltip()

                for widget in (item_frame, lbl_icon, lbl_name):
                    widget.bind("<Button-1>", on_click)
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)

                self._toolbox_items[name] = (item_frame, lbl_icon, lbl_name, cat)
                self._toolbox_buttons[name] = item_frame

        self._toolbox_compact = False

    def _toggle_toolbox_mode( self ):
        self._toolbox_compact = not self._toolbox_compact

        # Group items by category so each category's own items_frame is
        # gridded/packed independently. Each items_frame is a distinct
        # parent, so this never mixes geometry managers within one parent.
        items_by_cat = {}
        for name, (frame, icon_lbl, name_lbl, cat) in self._toolbox_items.items():
            items_by_cat.setdefault(cat, []).append((frame, icon_lbl, name_lbl))

        if self._toolbox_compact:
            # Compact mode: grid with 3 columns per category, larger icons
            for frame, icon_lbl, name_lbl, _cat in self._toolbox_items.values():
                frame.pack_forget()
                name_lbl.pack_forget()
                icon_lbl.pack_forget()
                icon_lbl.configure(
                    font = ctk.CTkFont( family = "Segoe UI Emoji", size = 18 )
                    )
                icon_lbl.pack( expand = True, fill = tk.BOTH, padx = 4,
                               pady = 4
                               )

            for cat, (header_lbl, items_frame) in self._toolbox_category_frames.items():
                row = col = 0
                for frame, icon_lbl, name_lbl in items_by_cat.get(cat, []):
                    # grid these into items_frame, which never has pack siblings
                    frame.grid( row = row, column = col, padx = 2, pady = 2,
                                sticky = "nsew"
                                )
                    col += 1
                    if col >= 3:
                        col = 0
                        row += 1
                for c in range( 3 ):
                    items_frame.grid_columnconfigure( c, weight = 1 )
            self._toolbox_toggle_btn.configure( text = "☰ Labels" )
        else:
            # Two-phase transition, mirroring the compact-mode branch:
            # forget ALL grid placements first, THEN pack everything back.
            # Packing a frame immediately after forgetting only itself
            # (while siblings in the same items_frame are still under grid)
            # mixes geometry managers within one parent and raises TclError.
            for frame, icon_lbl, name_lbl, _cat in self._toolbox_items.values():
                frame.grid_forget()

            for frame, icon_lbl, name_lbl, _cat in self._toolbox_items.values():
                icon_lbl.pack_forget()
                name_lbl.pack_forget()
                icon_lbl.configure(
                    font = ctk.CTkFont( family = "Segoe UI Emoji", size = 12 )
                    )
                frame.pack( fill = tk.X, padx = 5, pady = 1 )
                icon_lbl.pack( side = tk.LEFT, padx = 6, pady = 4 )
                name_lbl.pack( side = tk.RIGHT, padx = 6, pady = 4 )
            self._toolbox_toggle_btn.configure( text = "⊞ Icons" )



    # ---- Tooltip helpers ----
    def _show_tooltip(self, widget, text):
        self._hide_tooltip()
        try:
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height() + 4
        except Exception:
            return
        self._tooltip_win = tk.Toplevel(self.root)
        self._tooltip_win.wm_overrideredirect(True)
        self._tooltip_win.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._tooltip_win, text=text, justify=tk.LEFT,
            background="#2b2b2b", foreground="#ffffff",
            relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 9),
            padx=6, pady=3
        ).pack()

    def _hide_tooltip(self, event=None):
        if getattr(self, "_tooltip_win", None) is not None:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None

    # ---- Canvas hover tooltip ----
    def _on_canvas_motion(self, event):
        x, y = self._logical_xy(event)
        elem = self._find_element_at(x, y)
        if elem:
            tooltip_text = f"{elem.elem_type} (ID: {elem.elem_id})"
            self._show_tooltip(self.canvas, tooltip_text)
        else:
            self._hide_tooltip()

    def _on_canvas_leave(self, event):
        self._hide_tooltip()

    # ---- Zoom ----
    def _on_ctrl_zoom(self, event):
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self._zoom = min(3.0, self._zoom * 1.1)
        elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
            self._zoom = max(0.3, self._zoom / 1.1)
        else:
            return "break"
        self.renderer.zoom = self._zoom
        self.canvas.config(
            scrollregion=(0, 0, int(self.CANVAS_W * self._zoom),
                            int(self.CANVAS_H * self._zoom))
            )
        self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
        self._redraw_all_elements()
        self._update_zoom_label()
        return "break"

    def _update_zoom_label(self):
        if hasattr(self, "zoom_var"):
            self.zoom_var.set(f"Zoom: {int(round(self._zoom * 100))}%")

    def _highlight_active_tool(self, active_name: str):
        for name in ELEMENT_TYPES:
            frame = self._toolbox_buttons.get(name)
            if frame:
                color = TOOLBOX_ACTIVE_COLOR if name == active_name else TOOLBOX_NORMAL_COLOR
                frame.configure(fg_color=color)

    def _reset_tool_colors(self):
        for name in ELEMENT_TYPES:
            frame = self._toolbox_buttons.get(name)
            if frame:
                frame.configure(fg_color=TOOLBOX_NORMAL_COLOR)

    def _build_property_inspector(self):
        ctk.CTkLabel(self.prop_frame, text="PROPERTIES",
                      font=ctk.CTkFont(size=10, weight="bold")
                      ).pack(pady=(5, 6))
        self.prop_title_label = ctk.CTkLabel(self.prop_frame,
                                              text="No element selected.",
                                              anchor="w"
                                              )
        self.prop_title_label.pack(anchor=tk.W, padx=6, pady=(0, 2),
                                    fill=tk.X
                                    )
        self.prop_context_var = tk.StringVar(value="Container: None")
        ctk.CTkLabel(self.prop_frame, textvariable=self.prop_context_var,
                      text_color="#757575", anchor="w"
                      ).pack(anchor=tk.W, padx=6, pady=(0, 5),
                              fill=tk.X
                              )

        self.prop_scrollable = ctk.CTkScrollableFrame(self.prop_frame,
                                                       width=370,
                                                       fg_color="transparent"
                                                       )
        self.prop_scrollable.pack(fill=tk.BOTH, expand=True)

        self.prop_rows = []
        for i in range(20):
            frame = ctk.CTkFrame(self.prop_scrollable, corner_radius=0,
                                  fg_color="transparent"
                                  )
            lbl = ctk.CTkLabel(frame, text="", width=90, anchor="w")
            lbl.pack(side=tk.LEFT, padx=(2, 4))
            control_frame = ctk.CTkFrame(frame, fg_color="transparent",
                                          corner_radius=0
                                          )
            control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.prop_rows.append({
                "frame": frame, "label": lbl, "control_frame": control_frame,
                "widget": None, "visible": False,
                "_shape": None, "_trace_id": None, "_combo_widget": None,
            }
            )

    # ─── Incremental code insertion for new elements ──────────────────────
    def _insert_code_for_new_elements(
            self, new_elems: List[DesignElement]
            ) -> bool:
        if not self.full_code:
            return False

        # If any of the new elements need a tooltip and the reusable
        # _ToolTip helper class isn't in the script yet, bail out to the
        # full regenerate path (CodeGenerator.generate()) instead of
        # trying to splice the class definition in here -- that keeps the
        # helper-injection logic in exactly one place.
        if any(e.props.get("tooltip") for e in new_elems) and "_ToolTip" not in self.full_code:
            return False

        lines = self.full_code.splitlines(True)

        class_start = None
        for i, line in enumerate(lines):
            if line.startswith("class MainApplication:"):
                class_start = i
                break
        if class_start is None:
            return False

        init_start = None
        for i in range(class_start, len(lines)):
            if lines[i].startswith("    def __init__(self, root):"):
                init_start = i
                break
        if init_start is None:
            return False

        main_guard_idx = None
        for i, line in enumerate(lines):
            if line.startswith("if __name__ == '__main__':"):
                main_guard_idx = i
                break
        if main_guard_idx is None:
            main_guard_idx = len(lines)

        init_end = None
        for i in range(init_start + 1, min(len(lines), main_guard_idx)):
            line = lines[i]
            if line.strip() and line.startswith(" " * 4) and not line.startswith(" " * 8):
                init_end = i
                break
        if init_end is None:
            init_end = main_guard_idx

        existing_vars = set()
        for line in lines[init_start:init_end]:
            match = re.match(r'        self\.(\w+) = (?:tk\.(?:IntVar|StringVar|DoubleVar|BooleanVar)|ctk\.(?:IntVar|StringVar|DoubleVar|BooleanVar)|ttk\.\w+Var)\(', line)
            if match:
                existing_vars.add(match.group(1))

        new_vars = {}
        for elem in new_elems:
            if elem.elem_type in ("Radiobutton", "Checkbutton"):
                var_name = elem.props.get("variable")
                if var_name:
                    if elem.elem_type == "Checkbutton":
                        new_vars[var_name] = "ctk.IntVar(value=0)"
                    else:
                        new_vars.setdefault(var_name, "ctk.StringVar(value='')")
            elif elem.elem_type == "Entry":
                var_name = elem.props.get("textvariable")
                if var_name:
                    new_vars.setdefault(var_name, "ctk.StringVar(value='')")
        new_vars = {v: t for v, t in new_vars.items() if v not in existing_vars}

        init_lines = []
        for var, typ in new_vars.items():
            init_lines.append(f"        self.{var} = {typ}\n")

        for elem in new_elems:
            widget_line, place_line, extra_lines = CodeGenerator.generate_element_lines(
                elem, self.elements
                )
            init_lines.append(widget_line + "\n")
            for extra in extra_lines:
                init_lines.append(extra + "\n")
            init_lines.append(place_line + "\n")

            event = DEFAULT_EVENT_MAP.get(elem.elem_type)
            if event and event != "command" and elem.handler_code.strip():
                var_name = f"self._elem_{elem.elem_id}"
                method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                init_lines.append(
                    f"        {var_name}.bind('{event}', self.{method_name})\n"
                    )

        method_lines = []
        for elem in new_elems:
            if elem.handler_code.strip():
                method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                method_lines.append(f"    def {method_name}(self, event=None):\n")
                code_lines = elem.handler_code.strip().splitlines() or ["pass"]
                for cline in code_lines:
                    method_lines.append(f"        {cline}\n" if cline.strip() else "        \n")
                method_lines.append("\n")

        required_imports = []
        if any(e.elem_type == "Table" for e in new_elems):
            required_imports.append("import pandas as pd")
        if any(e.elem_type == "Image" and e.props.get("image_path") for e in new_elems):
            required_imports.append("from PIL import Image")
            required_imports.append("import os")
        required_imports.append("import customtkinter as ctk")
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_idx = i
        if last_import_idx != -1:
            existing_imports = [line.strip() for line in lines if line.startswith("import ") or line.startswith("from ")]
            for imp in required_imports:
                if imp not in existing_imports:
                    lines.insert(last_import_idx + 1, imp + "\n")
                    last_import_idx += 1

        if init_lines:
            lines[init_end:init_end] = init_lines
            if main_guard_idx >= init_end:
                main_guard_idx += len(init_lines)

        if method_lines:
            lines[main_guard_idx:main_guard_idx] = method_lines

        new_code = ''.join(lines)
        for elem in new_elems:
            if f"self._elem_{elem.elem_id} =" not in new_code:
                return False

        self.full_code = new_code
        self._current_code = self.full_code
        self._update_code_display()
        return True

    # ─── Incremental code removal for deleted elements ────────────────────
    def _remove_code_for_elements(self, elems: List[DesignElement]) -> bool:
        if not self.full_code or not elems:
            return False

        ids_to_remove = {e.elem_id for e in elems}
        lines = self.full_code.splitlines(True)
        indices_to_remove = set()

        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r'    def _on_(\w+)_(\d+)\(self, event=None\):', line)
            if match:
                elem_id = int(match.group(2))
                if elem_id in ids_to_remove:
                    start = i
                    i += 1
                    while i < len(lines) and (lines[i].startswith(" " * 8) or lines[i].strip() == ""):
                        i += 1
                    for j in range(start, i):
                        indices_to_remove.add(j)
                    continue
            i += 1

        for elem in elems:
            widget_pattern = rf'self\._elem_{elem.elem_id}\s*=\s*'
            widget_idx = None
            for i, line in enumerate(lines):
                if re.search(widget_pattern, line):
                    widget_idx = i
                    break
            if widget_idx is None:
                return False
            place_pattern = rf'self\._elem_{elem.elem_id}\s*\.place\s*\('
            place_idx = None
            for i in range(widget_idx + 1, len(lines)):
                if re.search(place_pattern, lines[i]):
                    place_idx = i
                    break
            if place_idx is None:
                return False
            for j in range(widget_idx, place_idx + 1):
                indices_to_remove.add(j)
            bind_pattern = rf'self\._elem_{elem.elem_id}\s*\.bind\s*\('
            for i, line in enumerate(lines):
                if re.search(bind_pattern, line):
                    indices_to_remove.add(i)

        if indices_to_remove:
            for idx in sorted(indices_to_remove, reverse=True):
                del lines[idx]

        self.full_code = ''.join(lines)
        self._current_code = self.full_code
        self._update_code_display()
        return True

    def _update_code_display(self):
        """Refresh the read-only generated-code preview panel.

        This is called from many places (every keystroke while editing a
        property, every arrow-key nudge, every drag release, etc.), but the
        actual refresh is a full delete()+insert() of the whole generated
        script into a Tk Text widget, which triggers a full re-layout and
        gets slow once the script is a few hundred lines. self.full_code and
        self._current_code (the actual source of truth -- nothing reads the
        Text widget's content back out) are always updated synchronously by
        the caller before this runs, so debouncing the on-screen refresh
        never risks anyone seeing stale generated code -- it only delays how
        soon the *preview panel* catches up, by well under the time it takes
        to notice.
        """
        if getattr(self, "_code_display_timer", None):
            self.root.after_cancel(self._code_display_timer)
        self._code_display_timer = self.root.after(120,
                                                      self._apply_code_display
                                                      )

    def _apply_code_display(self):
        self._code_display_timer = None
        if self.full_code is None:
            return
        self.code_text.configure(state="normal")
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, self.full_code)
        self.code_text.configure(state="disabled")

    def _regenerate_full_code(self):
        self.full_code = CodeGenerator.generate(
            self.elements, self.window_title, (self.CANVAS_W, self.CANVAS_H),
            self.CANVAS_BG, self.canvas_imports
        )
        self._current_code = self.full_code
        self._update_code_display()

    def _move_with_keys(self, event):
        if not self.selected_elems:
            return
        if event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
            return

        dx, dy = 0, 0
        if event.keysym == "Up":
            dy = -1
        elif event.keysym == "Down":
            dy = 1
        elif event.keysym == "Left":
            dx = -1
        elif event.keysym == "Right":
            dx = 1

        step = GRID_SIZE if (event.state & 0x0001) else 1
        dx *= step
        dy *= step

        for elem in self.selected_elems:
            elem.x = max(0, min(elem.x + dx, self.CANVAS_W - elem.canvas_w))
            elem.y = max(0, min(elem.y + dy, self.CANVAS_H - elem.canvas_h))
            self.renderer.redraw_element(elem)

        self._update_code_for_moved_elements()
        self._update_code()

        if hasattr(self, "_prop_save_timer"):
            self.root.after_cancel(self._prop_save_timer)
        self._prop_save_timer = self.root.after(500, self._save_state)

    def _update_code_for_moved_elements(self):
        for elem in self.selected_elems:
            self._update_code_for_element(elem)

    def _invalidate_full_code(self):
        self.full_code = None

    def _save_state(self, clear_redo=True):
        state = {
            "elements": [e.to_dict() for e in self.elements],
            "next_id": self.next_id,
            "reusable_ids": list(self.reusable_ids),
            "window_title": self.window_title,
            "canvas_w": self.CANVAS_W,
            "canvas_h": self.CANVAS_H,
            "canvas_bg": self.CANVAS_BG,
            "canvas_imports": self.canvas_imports,
            "full_code": self.full_code
        }
        state_str = json.dumps(state)
        if not self.undo_stack or self.undo_stack[-1] != state_str:
            self.undo_stack.append(state_str)
            if clear_redo:
                self.redo_stack.clear()
        self._is_modified = True
        self._update_window_title_display()

    def _load_state(self, state_str: str):
        data = json.loads(state_str)

        self.canvas.delete("all")
        self.elements.clear()
        self.selected_elems.clear()

        self.next_id = data.get("next_id", 1)
        self.reusable_ids = set(data.get("reusable_ids", []))
        self.window_title = data.get("window_title", "My Application")
        if hasattr(self, "title_var"):
            self.title_var.set(self.window_title)

        self.CANVAS_W = data.get("canvas_w", 800)
        self.CANVAS_H = data.get("canvas_h", 600)
        self.CANVAS_BG = data.get("canvas_bg", "#FAFAFA")
        self.canvas_imports = data.get("canvas_imports",
                                        "import tkinter as tk\nfrom tkinter import ttk")
        self.full_code = data.get("full_code")

        self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H,
                            bg=self.CANVAS_BG,
                            scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H)
                            )

        for elem_data in data.get("elements", []):
            elem = DesignElement.from_dict(elem_data)
            self.elements.append(elem)
        self._rebuild_index()

        self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
        self._redraw_all_elements()
        self._reorder_elements()
        self._show_properties(None)
        self._update_code()
        self._update_element_count()

    def _undo(self, event=None):
        if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry",
                                                                                 "TEntry",
                                                                                 "Text"):
            return

        if len(self.undo_stack) > 1:
            curr = self.undo_stack.pop()
            self.redo_stack.append(curr)
            prev = self.undo_stack[-1]
            self._load_state(prev)
            self._update_status("Undo successful.")

    def _redo(self, event=None):
        if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry",
                                                                                 "TEntry",
                                                                                 "Text"):
            return

        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.undo_stack.append(next_state)
            self._load_state(next_state)
            self._update_status("Redo successful.")

    def _is_element_visible(self, elem: DesignElement) -> bool:
        current = elem
        seen = set()
        while current.parent_id is not None:
            parent = self._by_id.get(current.parent_id)
            if parent is None:
                break
            if parent.elem_type == "Notebook":
                child = current
                tab = child.parent_tab
                if tab is None:
                    tab = 0
                active = int(parent.props.get("active_tab", 0) or 0)
                if tab != active:
                    return False
            current = parent
            if current.elem_id in seen:
                break
            seen.add(current.elem_id)
        return True

    def _visible_elements(self) -> List[DesignElement]:
        return [e for e in self.elements if self._is_element_visible(e)]

    def _redraw_all_elements(self):
        for e in self.elements:
            self.renderer.erase_element(e)
        for e in self._visible_elements():
            self.renderer.draw_element(e)
        self._reorder_elements()

    def _reorder_elements(self):
        self.canvas.tag_lower("grid")
        visible = self._visible_elements()

        # Memoized depth-of-nesting lookup (was an O(n^2) fixed-point loop
        # over the full element list; now O(n) using the parent index).
        depths: Dict[int, int] = {}

        def depth_of(e: DesignElement, visiting: set) -> int:
            if e.elem_id in depths:
                return depths[e.elem_id]
            if e.parent_id is None or e.elem_id in visiting:
                depths[e.elem_id] = 0
                return 0
            parent = self._by_id.get(e.parent_id)
            if parent is None:
                depths[e.elem_id] = 0
                return 0
            visiting.add(e.elem_id)
            d = depth_of(parent, visiting) + 1
            visiting.discard(e.elem_id)
            depths[e.elem_id] = d
            return d

        for e in self.elements:
            depth_of(e, set())

        sorted_elems = sorted(visible,
                               key=lambda e: depths.get(e.elem_id, 0)
                               )
        for e in sorted_elems:
            self.canvas.tag_raise(f"elem_{e.elem_id}")
        self.canvas.tag_raise("handle")

    def _tool_selected(self, tool_name: str):
        self.pending_type = tool_name
        self._highlight_active_tool(tool_name)
        self._update_status(
            f"{ELEMENT_TYPES[tool_name]['display']} selected — click canvas to place it."
            )

    def _notebook_tab_at(self, elem: DesignElement, x: float, y: float) -> Optional[int]:
        if elem.elem_type != "Notebook":
            return None
        if not (elem.x <= x <= elem.x + elem.canvas_w and elem.y <= y <= elem.y + 26):
            return None
        tabs = elem.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
        tab_width = max(58, min(120, int(
            (elem.canvas_w - 10) / max(1, min(len(tabs), 4))
            )
                                  )
                         )
        tab_x = elem.x + 5
        for i, _ in enumerate(tabs):
            tw = min(tab_width, elem.x + elem.canvas_w - 4 - tab_x)
            if tab_x <= x <= tab_x + tw:
                return i
            tab_x += tw + 3
            if tab_x >= elem.x + elem.canvas_w:
                break
        return None

    def _container_at(self, x: float, y: float) -> Optional[DesignElement]:
        containers = []
        for elem in self._visible_elements():
            if elem.elem_type not in CONTAINER_TYPES:
                continue
            if elem.elem_type == "Notebook":
                if not (elem.x <= x <= elem.x + elem.canvas_w and elem.y + 26 <= y <= elem.y + elem.canvas_h):
                    continue
            elif not elem.contains_point(x, y):
                continue
            area = max(1, elem.canvas_w * elem.canvas_h)
            depth = 0
            cur = elem
            seen = set()
            while cur.parent_id is not None and cur.parent_id not in seen:
                seen.add(cur.parent_id)
                p = self._by_id.get(cur.parent_id)
                if not p:
                    break
                depth += 1
                cur = p
            containers.append((depth, -area, elem))
        if not containers:
            return None
        containers.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return containers[0][2]

    def _set_notebook_active_tab(
            self, notebook: DesignElement, tab_index: int
            ):
        tabs = notebook.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
        if 0 <= tab_index < len(tabs):
            notebook.props["active_tab"] = tab_index
            for e in self.elements:
                e.selected = False
            self.selected_elems.clear()
            notebook.selected = True
            self.selected_elems.append(notebook)
            self._redraw_all_elements()
            self._show_properties(notebook)
            self._update_code()
            self._save_state()
            self._update_status(
                f"Notebook ID {notebook.elem_id}: {tabs[tab_index]} selected."
                )

    def _logical_xy(self, event):
        z = self._zoom or 1.0
        return self.canvas.canvasx(event.x) / z, self.canvas.canvasy(event.y) / z

    def _tag_drag_group(self):
        """Tag every canvas item belonging to the currently selected
        elements (plus any children cascaded along with a container) with
        a shared "dragging" tag, so _on_canvas_drag can move the whole
        group with a single canvas.move() call per mouse-move event
        instead of one call per element. Rebuilt fresh at the start of
        every move-drag.
        """
        self.canvas.dtag("dragging", "dragging")
        group_ids: set = set()

        def collect(e: DesignElement):
            if e.elem_id in group_ids:
                return
            group_ids.add(e.elem_id)
            if e.elem_type in CONTAINER_TYPES:
                for child in self._children_by_parent.get(e.elem_id, []):
                    collect(child)

        for e in self.selected_elems:
            collect(e)

        for eid in group_ids:
            self.canvas.addtag_withtag("dragging", f"elem_{eid}")
            el = self._by_id.get(eid)
            if el:
                for hid in el.handle_ids.values():
                    self.canvas.addtag_withtag("dragging", hid)

    def _on_canvas_click(self, event):
        x, y = self._logical_xy(event)
        z = self._zoom or 1.0
        ctrl_held = (event.state & 0x0004) != 0 or (event.state & 0x0001) != 0

        if self.pending_type:
            tool = self.pending_type
            self.pending_type = None
            self._reset_tool_colors()
            self._add_element(tool, x, y)
            return

        self.elem_origs = {e.elem_id: (e.x, e.y, e.canvas_w, e.canvas_h) for e in self.elements}

        for candidate in reversed(self._visible_elements()):
            tab_index = self._notebook_tab_at(candidate, x, y)
            if tab_index is not None:
                self._set_notebook_active_tab(candidate, tab_index)
                self._reset_drag_state()
                return

        handle_hit = None
        for elem in self.selected_elems:
            hit = elem.hit_handle(x, y)
            if hit:
                handle_hit = hit
                self.drag_mode = "resize"
                self.drag_elem = elem
                self.mouse_down_pos = (x, y)
                self.active_handle = hit
                self.pending_type = None
                self._reset_tool_colors()
                break

        if handle_hit:
            if handle_hit == "DEL":
                self._delete_selected()
                return
            return

        clicked = self._find_element_at(x, y)
        if clicked:
            self._select_element(clicked, clear=not ctrl_held)
            self.drag_mode = "move"
            self.drag_elem = clicked
            self.mouse_down_pos = (x, y)
            self.active_handle = None
            self._last_move_delta = (0, 0)
            self._tag_drag_group()
        else:
            self._select_element(None, clear=not ctrl_held)
            self._reset_drag_state()
            self.drag_mode = "select_box"
            self.mouse_down_pos = (x, y)
            self.selection_box_id = self.canvas.create_rectangle(x * z, y * z,
                                                                  x * z, y * z,
                                                                  dash=(4, 4),
                                                                  outline="#1976D2"
                                                                  )

        self.canvas.focus_set()

    def _find_element_at(self, x: int, y: int) -> Optional[DesignElement]:
        for elem in reversed(self._visible_elements()):
            if elem.contains_point(x, y):
                return elem
        return None

    def _on_canvas_drag(self, event):
        if not self.mouse_down_pos:
            return
        z = self._zoom or 1.0
        mx, my = self._logical_xy(event)
        cum_dx, cum_dy = mx - self.mouse_down_pos[0], my - self.mouse_down_pos[1]

        if self.drag_mode == "move":
            # Snap once, using the element the user actually grabbed as the
            # anchor, then apply that exact same delta to every selected
            # element (and cascaded container children). Snapping each
            # element to the grid independently -- the old behavior --
            # could round each one onto a different grid line and change
            # the gaps between them during a multi-select drag; a single
            # shared delta keeps relative spacing exact.
            anchor = (self.drag_elem
                      if self.drag_elem and self.drag_elem.elem_id in self.elem_origs
                      else next((e for e in self.selected_elems
                                 if e.elem_id in self.elem_origs), None)
                      )
            if anchor is None:
                return
            aox, aoy, _, _ = self.elem_origs[anchor.elem_id]
            snapped_x, snapped_y = self.renderer.snap_to_grid(aox + cum_dx,
                                                               aoy + cum_dy
                                                               )
            dx, dy = snapped_x - aox, snapped_y - aoy

            # Incremental delta since the previous drag frame. Canvas items
            # are translated by this amount, not by the full cumulative
            # delta, since they're already sitting at last frame's position.
            prev_dx, prev_dy = self._last_move_delta
            inc_dx, inc_dy = dx - prev_dx, dy - prev_dy
            self._last_move_delta = (dx, dy)

            moved_ids = set()
            # Elements whose canvas-edge clamp made their actual movement
            # this frame differ from the rest of the group (only possible
            # right at the edge of the canvas) -- corrected individually
            # after the single batched move below.
            clamped: List[Tuple[DesignElement, int, int]] = []

            def apply_delta(elem: DesignElement, base_x: int, base_y: int):
                prev_x, prev_y = elem.x, elem.y
                new_x = max(0, min(base_x + dx, self.CANVAS_W - elem.canvas_w))
                new_y = max(0, min(base_y + dy, self.CANVAS_H - elem.canvas_h))
                if (new_x - prev_x, new_y - prev_y) != (inc_dx, inc_dy):
                    clamped.append((elem, prev_x, prev_y))
                elem.x, elem.y = new_x, new_y
                moved_ids.add(elem.elem_id)

            for elem in self.selected_elems:
                if elem.elem_id in moved_ids or elem.elem_id not in self.elem_origs:
                    continue
                ox, oy, _, _ = self.elem_origs[elem.elem_id]
                apply_delta(elem, ox, oy)

                if elem.elem_type in CONTAINER_TYPES:
                    for child in self._children_by_parent.get(elem.elem_id, []):
                        if child.elem_id in moved_ids:
                            continue
                        cox, coy, _, _ = self.elem_origs.get(child.elem_id,
                                                              (child.x,
                                                               child.y,
                                                               child.canvas_w,
                                                               child.canvas_h)
                                                              )
                        apply_delta(child, cox, coy)

            # One canvas call moves everything tagged "dragging" this
            # session (set up in _tag_drag_group), instead of a separate
            # canvas.move() per element -- this is what keeps a large
            # multi-selection from feeling laggy while dragging.
            z = getattr(self.renderer, "zoom", 1.0)
            if inc_dx or inc_dy:
                self.canvas.move("dragging", inc_dx * z, inc_dy * z)
            for elem, prev_x, prev_y in clamped:
                self.renderer.move_element(elem, elem.x - prev_x - inc_dx,
                                            elem.y - prev_y - inc_dy)

        elif self.drag_mode == "resize":
            for elem in self.selected_elems:
                if elem.elem_id in self.elem_origs:
                    ox, oy, ow, oh = self.elem_origs[elem.elem_id]
                    nx, ny, nw, nh = self._compute_resize(self.active_handle,
                                                           ox, oy, ow, oh,
                                                           cum_dx, cum_dy
                                                           )
                    elem.x, elem.y, elem.canvas_w, elem.canvas_h = nx, ny, nw, nh
                    self.renderer.redraw_element(elem)

        elif self.drag_mode == "select_box" and self.selection_box_id:
            self.canvas.coords(
                self.selection_box_id,
                self.mouse_down_pos[0] * z, self.mouse_down_pos[1] * z, mx * z,
                my * z
            )

    def _on_canvas_release(self, event):
        parent_changed = False
        if self.drag_mode == "select_box":
            mx, my = self._logical_xy(event)
            x1, y1 = min(self.mouse_down_pos[0], mx), min(
                self.mouse_down_pos[1], my
                )
            x2, y2 = max(self.mouse_down_pos[0], mx), max(
                self.mouse_down_pos[1], my
                )
            for elem in self._visible_elements():
                cx, cy = elem.x + elem.canvas_w // 2, elem.y + elem.canvas_h // 2
                if x1 <= cx <= x2 and y1 <= cy <= y2 and elem not in self.selected_elems:
                    self._select_element(elem, clear=False)
            if self.selection_box_id:
                self.canvas.delete(self.selection_box_id)
                self.selection_box_id = None

        elif self.drag_mode in ("move", "resize"):
            if self.drag_mode == "move":
                for elem in self.selected_elems:
                    if elem.elem_type in CONTAINER_TYPES:
                        continue
                    cx = elem.x + elem.canvas_w / 2
                    cy = elem.y + elem.canvas_h / 2
                    parent = self._container_at(cx, cy)
                    old_parent = elem.parent_id
                    elem.parent_id = parent.elem_id if parent else None
                    if parent and parent.elem_type == "Notebook":
                        elem.parent_tab = int(
                            parent.props.get("active_tab", 0) or 0
                            )
                    elif old_parent != elem.parent_id:
                        elem.parent_tab = None
                    # Track if parent changed
                    if old_parent != elem.parent_id:
                        parent_changed = True

            self._update_code_for_moved_elements()
            self._update_code()
            self._reorder_elements()
            self._save_state()

        self._reset_drag_state()

        # If any parent changed, regenerate full code to fix ordering
        if parent_changed:
            self._invalidate_full_code()
            self._update_code()

    def _on_canvas_double_click(self, event):
        x, y = self._logical_xy(event)
        elem = self._find_element_at(x, y)
        if elem:
            self._open_code_editor(elem)

    def _compute_resize(self, handle, ox, oy, ow, oh, cum_dx, cum_dy):
        nx, ny, nw, nh = ox, oy, ow, oh
        if "W" in handle:
            nw = max(MIN_W, ow - cum_dx)
            nx = ox + ow - nw
        if "E" in handle:
            nw = max(MIN_W, ow + cum_dx)
        if "N" in handle:
            nh = max(MIN_H, oh - cum_dy)
            ny = oy + oh - nh
        if "S" in handle:
            nh = max(MIN_H, oh + cum_dy)
        nx = max(0, min(nx, self.CANVAS_W - nw))
        ny = max(0, min(ny, self.CANVAS_H - nh))
        nw = min(nw, self.CANVAS_W - nx)
        nh = min(nh, self.CANVAS_H - ny)
        return nx, ny, nw, nh

    def _reset_drag_state(self):
        self.drag_mode, self.drag_elem, self.mouse_down_pos, self.elem_origs, self.active_handle = "none", None, None, {}, None
        self._last_move_delta = (0, 0)
        self.canvas.dtag("dragging", "dragging")

    def _add_element(self, elem_type: str, x: int, y: int):
        sx, sy = self.renderer.snap_to_grid(int(x), int(y))
        w, h = ELEMENT_TYPES[elem_type]["default_size"]
        sx = max(0, min(sx, self.CANVAS_W - w))
        sy = max(0, min(sy, self.CANVAS_H - h))

        if self.reusable_ids:
            new_id = min(self.reusable_ids)
            self.reusable_ids.remove(new_id)
        else:
            new_id = self.next_id
            self.next_id += 1

        props = copy.deepcopy(ELEMENT_TYPES[elem_type]["defaults"])
        elem = DesignElement(elem_type=elem_type, x=sx, y=sy,
                              props=props, elem_id=new_id, canvas_w=w,
                              canvas_h=h
                              )
        parent = self._container_at(sx + w / 2, sy + h / 2)
        if parent is not None:
            elem.parent_id = parent.elem_id
            if parent.elem_type == "Notebook":
                elem.parent_tab = int(
                    parent.props.get("active_tab", 0) or 0
                    )

        event_name = DEFAULT_EVENT_MAP.get(elem_type)
        if event_name:
            code = f'"""\nEvent handler for {elem_type} (ID: {elem.elem_id}).\nTriggered by: {event_name}\nAccess widget instance via: self._elem_{elem.elem_id}\n"""\npass'
            elem.handler_code = code

        self.elements.append(elem)
        self._rebuild_index()

        if self.full_code is None:
            self._regenerate_full_code()
        else:
            if not self._insert_code_for_new_elements([elem]):
                self._regenerate_full_code()

        if self._is_element_visible(elem):
            self.renderer.draw_element(elem)
            self._select_element(elem, clear=True)
        else:
            self._select_element(None, clear=True)

        self._update_code()
        self._update_element_count()
        self._update_status(f"Added {ELEMENT_TYPES[elem_type]['display']}.")
        self._save_state()

    def _select_element(
            self, elem: Optional[DesignElement], clear: bool = True
            ):
        if clear:
            for e in self.selected_elems:
                e.selected = False
                self.renderer.redraw_element(e)
            self.selected_elems.clear()

        if elem and elem not in self.selected_elems:
            self.selected_elems.append(elem)
            elem.selected = True
            self.renderer.redraw_element(elem)

        self._reorder_elements()

        if len(self.selected_elems) == 1:
            self._show_properties(self.selected_elems[0])
        elif len(self.selected_elems) > 1:
            self._show_properties_multi()
        else:
            self._show_properties(None)

    def _show_properties_multi(self):
        for row in self.prop_rows:
            row["frame"].pack_forget()
            row["visible"] = False
        self.prop_title_label.configure(
            text=f"[{len(self.selected_elems)} elements selected - Common Properties]"
            )

        common_fields = [
            ("font", "Font", "font"),
            ("fg", "Foreground", "color"),
            ("bg", "Background", "color"),
            ("width", "Width", "entry"),
            ("height", "Height", "entry"),
        ]

        row_index = 0
        for field_key, label, widget_type in common_fields:
            if row_index >= len(self.prop_rows):
                break
            row = self.prop_rows[row_index]
            row["label"].configure(text=label + " (All):")
            row["field_key"] = field_key

            self._clear_prop_row(row)

            var = tk.StringVar(value="")

            if widget_type in ("entry", "color"):
                var.trace_add("write", lambda *args,
                                               r=row: self._on_live_multi_prop_change(
                    r
                    )
                               )
                row["var"] = var

                if widget_type == "entry":
                    ctk.CTkEntry(row["control_frame"], textvariable=var,
                                  width=200
                                  ).pack(fill=tk.X)
                elif widget_type == "color":
                    frame = ctk.CTkFrame(row["control_frame"],
                                          fg_color="transparent",
                                          corner_radius=0
                                          )
                    frame.pack(fill=tk.X)
                    ctk.CTkEntry(frame, textvariable=var, width=200).pack(
                        side=tk.LEFT, fill=tk.X, expand=True
                        )
                    ctk.CTkButton(frame, text="Pick",
                                   command=lambda v=var: self._pick_color(
                                       v
                                       ), width=60, height=28
                                   ).pack(side=tk.RIGHT)
                    rgb_lbl = ctk.CTkLabel(
                        row["control_frame"],
                        text=self._rgb_label_text(var.get()),
                        font=("Segoe UI", 10), text_color="#757575",
                        anchor="w"
                        )
                    rgb_lbl.pack(fill=tk.X, pady=(1, 0))
                    var.trace_add(
                        "write",
                        lambda *a, v=var, lbl=rgb_lbl: lbl.configure(
                            text=self._rgb_label_text(v.get())
                            )
                        )

            elif widget_type == "font":
                frame = ctk.CTkFrame(row["control_frame"],
                                      fg_color="transparent",
                                      corner_radius=0
                                      )
                frame.pack(fill=tk.X)
                family_var = tk.StringVar(value="Segoe UI")
                size_var = tk.StringVar(value="9")

                def update_font(
                        *args, target_var=var, f_var=family_var,
                        s_var=size_var
                        ):
                    target_var.set(f"('{f_var.get()}', {s_var.get()})")

                family_var.trace_add("write", update_font)
                size_var.trace_add("write", update_font)

                try:
                    families = sorted(list(tkfont.families()))
                except:
                    families = ["Arial", "Segoe UI"]

                # See the single-select font branch for why this is
                # ttk.Combobox rather than CTkComboBox: CTk's dropdown has
                # no scrollbar at all, which is unusable for a 100+ item
                # font list.
                ttk.Combobox(frame, textvariable=family_var,
                             values=families, width=26
                             ).pack(side=tk.LEFT, padx=(0, 2))
                ctk.CTkComboBox(frame, variable=size_var,
                                 values=[str(s) for s in
                                           [8, 9, 10, 11, 12, 14, 16, 18, 20,
                                            24]], width=200
                                 ).pack(side=tk.LEFT)

                var.trace_add("write", lambda *args,
                                               r=row: self._on_live_multi_prop_change(
                    r
                    )
                               )
                row["var"] = var

            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            row_index += 1

    def _on_live_multi_prop_change(self, row):
        if len(self.selected_elems) <= 1 or not row.get("visible"):
            return
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None:
            return
        value = var.get()
        if not value:
            return

        for elem in self.selected_elems:
            if field_key in elem.props or field_key in ("width", "height"):
                if field_key == "width":
                    try:
                        elem.canvas_w = int(value)
                    except:
                        pass
                elif field_key == "height":
                    try:
                        elem.canvas_h = int(value)
                    except:
                        pass
                elif field_key == "font":
                    try:
                        parsed = ast.literal_eval(value)
                        if isinstance(parsed, list):
                            parsed = tuple(parsed)
                        elem.props["font"] = parsed if isinstance(parsed, tuple) else value
                    except:
                        elem.props["font"] = value
                else:
                    elem.props[field_key] = value
                self.renderer.redraw_element(elem)

        self._update_code_for_moved_elements()
        self._update_code()
        if hasattr(self, "_prop_save_timer"):
            self.root.after_cancel(self._prop_save_timer)
        self._prop_save_timer = self.root.after(500, self._save_state)

    def _copy_elements(self, event=None):
        if not self.selected_elems:
            return
        self.clipboard = [copy.deepcopy(e) for e in self.selected_elems]
        self._update_status(
            f"Copied {len(self.clipboard)} element(s) to clipboard."
            )

    def _paste_elements(self, event=None):
        if not self.clipboard:
            return
        self._select_element(None, clear=True)

        pasted = []
        for data in self.clipboard:
            new_elem = copy.deepcopy(data)
            if self.reusable_ids:
                new_elem.elem_id = min(self.reusable_ids)
                self.reusable_ids.remove(new_elem.elem_id)
            else:
                new_elem.elem_id = self.next_id
                self.next_id += 1
            new_elem.x += 20
            new_elem.y += 20
            new_elem.rect_id = 0
            new_elem.text_id = 0
            new_elem.handle_ids = {}
            new_elem.selected = False
            new_elem.parent_id = None
            self.elements.append(new_elem)
            pasted.append(new_elem)

        self._rebuild_index()
        for new_elem in pasted:
            if self._is_element_visible(new_elem):
                self.renderer.draw_element(new_elem)

        if self.full_code is None:
            self._regenerate_full_code()
        else:
            if not self._insert_code_for_new_elements(pasted):
                self._regenerate_full_code()

        for e in pasted:
            if self._is_element_visible(e):
                self._select_element(e, clear=False)

        self._update_code()
        self._update_element_count()
        self._update_status(f"Pasted {len(pasted)} element(s).")
        self._save_state()

    def _delete_selected(self, event=None):
        if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry",
                                                                                 "TEntry",
                                                                                 "Text"):
            return

        if not self.selected_elems:
            return

        if not messagebox.askyesno("Confirm Deletion",
                                    "Are you sure you want to delete the selected element(s)?\nNote: Deleting a Container deletes all enclosed children elements."
                                    ):
            return

        to_delete = list(self.selected_elems)

        for elem in self.selected_elems:
            if elem.elem_type in CONTAINER_TYPES:
                for child in self._children_by_parent.get(elem.elem_id, []):
                    if child not in to_delete:
                        to_delete.append(child)

        if self.full_code is not None:
            if not self._remove_code_for_elements(to_delete):
                self._regenerate_full_code()
        else:
            self._regenerate_full_code()

        for elem in to_delete:
            self.renderer.erase_element(elem)
            if elem in self.elements:
                self.elements.remove(elem)
                self.reusable_ids.add(elem.elem_id)
        self._rebuild_index()

        self.selected_elems.clear()
        self._reset_drag_state()
        self._show_properties(None)
        self._update_code()
        self._update_element_count()
        self._update_status("Element(s) deleted.")
        self._save_state()

    def _clear_all(self):
        if not self.elements:
            return
        if not messagebox.askyesno("Confirm Clear",
                                    "Are you sure you want to clear the entire canvas? All unsaved progress will be lost."
                                    ):
            return

        self._invalidate_full_code()
        for elem in self.elements:
            self.renderer.erase_element(elem)
        self.elements.clear()
        self._rebuild_index()
        self.selected_elems.clear()
        self.reusable_ids.clear()
        self.next_id = 1

        self._reset_drag_state()
        self.canvas.delete("all")
        self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
        self._show_properties(None)
        self._update_code()
        self._update_element_count()
        self._save_state()

    def _clear_prop_row(self, row):
        """Destroy a property row's control widgets and reset its pooling
        state. Centralizes what used to be a repeated
        `for child in ...: child.destroy()` at every call site, and makes
        sure the fast-reuse path in _show_properties never mistakes a row
        that another function (multi-select / canvas properties) just
        rebuilt for one it can still safely pool.
        """
        for child in row["control_frame"].winfo_children():
            child.destroy()
        row["_shape"] = None
        row["_trace_id"] = None
        row["_combo_widget"] = None

    def _set_var_quiet(self, var: tk.StringVar, value: str, row: dict,
                        callback) -> None:
        """Update a StringVar's value without firing its live-edit trace.
        Used when reusing an existing property-field widget across a
        selection change: merely viewing a different element's properties
        should never mark the document modified or touch the generated
        code the way actually editing a field does, so the trace is
        detached for the programmatic set and reattached right after.
        """
        trace_id = row.get("_trace_id")
        if trace_id is not None:
            try:
                var.trace_remove("write", trace_id)
            except tk.TclError:
                pass
        var.set(value)
        row["_trace_id"] = var.trace_add("write", callback)

    def _show_properties(self, elem: Optional[DesignElement]):
        for row in self.prop_rows:
            row["frame"].pack_forget()
            row["visible"] = False

        if elem is None:
            self.prop_title_label.configure(text="Canvas Settings")
            self.prop_context_var.set("Container: None")
            self._show_canvas_properties()
            return

        spec = ELEMENT_TYPES[elem.elem_type]
        self.prop_title_label.configure(
            text=f"{spec['display']} [id={elem.elem_id}]"
            )
        self.prop_context_var.set(self._parent_description(elem))
        fields = PROPERTY_FIELDS.get(elem.elem_type, [])
        row_index = 0

        for fielddef in fields:
            if row_index >= len(self.prop_rows):
                break
            field_key, label, widget_type = fielddef[0], fielddef[1], fielddef[2]
            options = fielddef[3] if len(fielddef) > 3 else None
            row = self.prop_rows[row_index]
            row["label"].configure(text=label + ":")
            row["field_key"] = field_key

            if field_key == "canvas_w":
                value = elem.canvas_w
            elif field_key == "canvas_h":
                value = elem.canvas_h
            elif field_key == "active_tab" and elem.elem_type == "Notebook":
                value = int(elem.props.get("active_tab", 0) or 0) + 1
                options = [str(i + 1) for i in range(
                    max(1, len(elem.props.get("tabs", [])))
                    )]
            else:
                value = elem.props.get(field_key, "")

            if field_key == "tabs" and elem.elem_type == "Notebook":
                value = ", ".join(
                    str(v) for v in (elem.props.get("tabs") or ["Tab 1"])
                    )

            display_val = "" if value is None else str(value)

            # Fields handled by dedicated composite widgets below (file
            # pickers, the notebook tab editor) are never pooled -- only
            # plain single-widget "entry"/"combobox" fields are, since
            # those are simple enough to reuse safely (see _set_var_quiet)
            # and make up the large majority of property fields overall.
            is_special = (
                (elem.elem_type == "Image" and field_key == "image_path") or
                (elem.elem_type == "Table" and field_key == "file") or
                (field_key == "tabs" and elem.elem_type == "Notebook")
                )
            poolable = (not is_special) and widget_type in ("entry", "combobox")
            shape = (field_key, widget_type) if poolable else None

            if poolable and row.get("_shape") == shape and row.get("var") is not None:
                # Fast path: this row already holds a live CTkEntry/
                # CTkComboBox for this exact field+widget shape (e.g. the
                # previous selection was another element of the same
                # type). Reuse it in place instead of destroying and
                # rebuilding -- CTk widget construction is comparatively
                # expensive, and clicking between same-type elements is a
                # very common flow.
                var = row["var"]
                self._set_var_quiet(
                    var, display_val, row,
                    lambda *args, r=row: self._on_live_prop_change(r)
                    )
                if widget_type == "combobox" and row.get("_combo_widget") is not None:
                    row["_combo_widget"].configure(
                        values=[str(o) for o in (options or [])]
                        )
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                row_index += 1
                continue

            self._clear_prop_row(row)
            var = tk.StringVar(value=display_val)

            # Special handling for image file picker
            if elem.elem_type == "Image" and field_key == "image_path":
                var.trace_add("write",
                               lambda *args, r=row: self._on_live_prop_change(
                                   r
                                   )
                               )
                row["var"] = var
                file_frame = ctk.CTkFrame(row["control_frame"],
                                           fg_color="transparent",
                                           corner_radius=0
                                           )
                file_frame.pack(fill=tk.X)
                ctk.CTkEntry(file_frame, textvariable=var, width=200
                              ).pack(side=tk.LEFT, fill=tk.X,
                                      expand=True
                                      )
                ctk.CTkButton(file_frame, text="Browse", width=80, height=28,
                               command=lambda v=var, e=elem: self._browse_image_file(v, e)
                               ).pack(side=tk.LEFT, padx=(3, 0))
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                row_index += 1
                continue

            if elem.elem_type == "Table" and field_key == "file":
                var.trace_add("write",
                               lambda *args, r=row: self._on_live_prop_change(
                                   r
                                   )
                               )
                row["var"] = var
                file_frame = ctk.CTkFrame(row["control_frame"],
                                           fg_color="transparent",
                                           corner_radius=0
                                           )
                file_frame.pack(fill=tk.X)
                ctk.CTkEntry(file_frame, textvariable=var, width=200
                              ).pack(side=tk.LEFT, fill=tk.X,
                                      expand=True
                                      )
                ctk.CTkButton(file_frame, text="…", width=60, height=28,
                               command=lambda v=var: self._browse_table_file(v)
                               ).pack(side=tk.LEFT, padx=(3, 0))
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                row_index += 1
                continue

            if field_key == "tabs" and elem.elem_type == "Notebook":
                var.trace_add("write",
                               lambda *args, r=row: self._on_live_prop_change(
                                   r
                                   )
                               )
                row["var"] = var
                tabs_frame = ctk.CTkFrame(row["control_frame"],
                                           fg_color="transparent",
                                           corner_radius=0
                                           )
                tabs_frame.pack(fill=tk.X)
                ctk.CTkEntry(tabs_frame, textvariable=var, width=200
                              ).pack(side=tk.LEFT, fill=tk.X,
                                      expand=True
                                      )
                ctk.CTkButton(tabs_frame, text="+", width=60, height=28,
                               command=lambda e=elem: self._add_notebook_tab(e)
                               ).pack(side=tk.LEFT, padx=(3, 0))
                ctk.CTkButton(tabs_frame, text="−", width=60, height=28,
                               command=lambda e=elem: self._remove_notebook_tab(e)
                               ).pack(side=tk.LEFT, padx=(2, 0))
            elif widget_type in ("entry", "combobox", "color"):
                trace_id = var.trace_add(
                    "write",
                    lambda *args, r=row: self._on_live_prop_change(r)
                    )
                row["var"] = var
                if widget_type == "entry":
                    ctk.CTkEntry(row["control_frame"], textvariable=var,
                                  width=200
                                  ).pack(fill=tk.X)
                    row["_shape"] = (field_key, "entry")
                    row["_trace_id"] = trace_id
                elif widget_type == "combobox":
                    combo = ctk.CTkComboBox(row["control_frame"], variable=var,
                                             values=[str(o) for o in
                                                       (options or [])], width=200
                                             )
                    combo.pack(fill=tk.X)
                    row["_shape"] = (field_key, "combobox")
                    row["_trace_id"] = trace_id
                    row["_combo_widget"] = combo
                else:
                    cf = ctk.CTkFrame(row["control_frame"],
                                       fg_color="transparent",
                                       corner_radius=0
                                       )
                    cf.pack(fill=tk.X)
                    ctk.CTkEntry(cf, textvariable=var, width=200).pack(
                        side=tk.LEFT, fill=tk.X, expand=True
                        )
                    ctk.CTkButton(cf, text="Pick", width=60, height=28,
                                   command=lambda v=var: self._pick_color(
                                       v
                                       )
                                   ).pack(side=tk.RIGHT, padx=(3, 0))
                    rgb_lbl = ctk.CTkLabel(
                        row["control_frame"],
                        text=self._rgb_label_text(var.get()),
                        font=("Segoe UI", 10), text_color="#757575",
                        anchor="w"
                        )
                    rgb_lbl.pack(fill=tk.X, pady=(1, 0))
                    var.trace_add(
                        "write",
                        lambda *a, v=var, lbl=rgb_lbl: lbl.configure(
                            text=self._rgb_label_text(v.get())
                            )
                        )
                    # "color" fields aren't pooled (row["_shape"] stays
                    # None from _clear_prop_row), so this always rebuilds.
            elif widget_type == "text":
                text_w = tk.Text(row["control_frame"], height=4, width=22,
                                  font=("Segoe UI", 9), wrap=tk.WORD
                                  )
                text_w.pack(fill=tk.X)
                text_w.insert("1.0", display_val)
                text_w.bind("<KeyRelease>", lambda event, target_var=var,
                                                    tw=text_w: target_var.set(
                    tw.get("1.0", "end-1c")
                    )
                             )
                var.trace_add("write",
                               lambda *args, r=row: self._on_live_prop_change(
                                   r
                                   )
                               )
                row["var"] = var
            elif widget_type == "font":
                frame = ctk.CTkFrame(row["control_frame"],
                                      fg_color="transparent",
                                      corner_radius=0
                                      )
                frame.pack(fill=tk.X)
                family_var = tk.StringVar()
                size_var = tk.StringVar()
                if isinstance(value, (tuple, list)):
                    f_family = str(value[0]) if value else "Segoe UI"
                    f_size = str(value[1]) if len(value) > 1 else "9"
                else:
                    try:
                        parsed = ast.literal_eval(str(value))
                        if isinstance(parsed, list):
                            parsed = tuple(parsed)
                        f_family = str(parsed[0]) if isinstance(parsed, (tuple, list)) and parsed else "Segoe UI"
                        f_size = str(parsed[1]) if isinstance(parsed, (tuple, list)) and len(parsed) > 1 else "9"
                    except Exception:
                        f_family, f_size = "Segoe UI", "9"
                family_var.set(f_family)
                size_var.set(f_size)

                def update_font(
                        *args, target_var=var, f_var=family_var,
                        s_var=size_var
                        ):
                    target_var.set(f"('{f_var.get()}', {s_var.get()})")

                family_var.trace_add("write", update_font)
                size_var.trace_add("write", update_font)
                try:
                    families = sorted(list(tkfont.families()))
                except Exception:
                    families = ["Arial", "Segoe UI"]
                # ttk.Combobox (not CTkComboBox) specifically for the font
                # family list: CTkComboBox's dropdown is a bare native OS
                # Menu with no scrollbar at all, which is unusable for the
                # 100+ fonts most systems have installed. ttk's popdown is
                # a real Listbox+Scrollbar, so it stays scrollable/typeable
                # for a long list. Still driven by the same family_var, so
                # update_font's trace above works unchanged.
                ttk.Combobox(frame, textvariable=family_var,
                             values=families, width=17, state="readonly"
                             ).pack(side=tk.LEFT, padx=(0, 2))
                ctk.CTkComboBox(frame, variable=size_var,
                                 values=[str(s) for s in
                                           [8, 9, 10, 11, 12, 14, 16, 18, 20,
                                            24, 28, 36, 48]], width=70
                                 ).pack(side=tk.LEFT)
                var.trace_add("write",
                               lambda *args, r=row: self._on_live_prop_change(
                                   r
                                   )
                               )
                row["var"] = var
            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            row_index += 1

    def _browse_image_file(self, var: tk.StringVar, elem: DesignElement):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico"),
                       ("All Files", "*.*")]
        )
        if not path:
            return
        resources_dir = "resources"
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
        ext = os.path.splitext(path)[1]
        dest_filename = f"img_{elem.elem_id}{ext}"
        dest_path = os.path.join(resources_dir, dest_filename)
        shutil.copy2(path, dest_path)
        rel_path = os.path.join(resources_dir, dest_filename)
        var.set(rel_path)
        elem.props["image_path"] = rel_path
        self.renderer.redraw_element(elem)
        self._update_code_for_element(elem)
        self._update_code()
        self._save_state()
        self._update_status(f"Image added: {rel_path}")

    def _browse_table_file(self, var: tk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv"),
                       ("All Files", "*.*")]
        )
        if path:
            var.set(path)

    def _parent_description(self, elem: DesignElement) -> str:
        if elem.parent_id is None:
            return "Container: None (root)"
        parent = self._by_id.get(elem.parent_id)
        if parent is None:
            return f"Container: ID {elem.parent_id} (missing)"
        description = f"Container: {parent.elem_type} [id={parent.elem_id}]"
        if parent.elem_type == "Notebook":
            tabs = parent.props.get("tabs") or ["Tab 1"]
            idx = elem.parent_tab if elem.parent_tab is not None else 0
            idx = max(0, min(idx, len(tabs) - 1))
            description += f" — Tab {idx + 1}: {tabs[idx]}"
        return description

    def _add_notebook_tab(self, elem: DesignElement):
        tabs = list(elem.props.get("tabs") or ["Tab 1"])
        tabs.append(f"Tab {len(tabs) + 1}")
        elem.props["tabs"] = tabs
        self._invalidate_full_code()
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._update_code()
        self._save_state()

    def _remove_notebook_tab(self, elem: DesignElement):
        tabs = list(elem.props.get("tabs") or ["Tab 1"])
        if len(tabs) <= 1:
            self._update_status("A Notebook must have at least one tab.")
            return
        tabs.pop()
        elem.props["tabs"] = tabs
        for child in self._children_by_parent.get(elem.elem_id, []):
            if child.parent_tab is not None and child.parent_tab >= len(tabs):
                child.parent_tab = len(tabs) - 1
        elem.props["active_tab"] = min(
            int(elem.props.get("active_tab", 0) or 0), len(tabs) - 1
            )
        self._invalidate_full_code()
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._update_code()
        self._save_state()

    def _show_canvas_properties(self):
        row_index = 0

        row = self.prop_rows[row_index]
        row["label"].configure(text="Window Title:")
        self._clear_prop_row(row)
        self.title_var = tk.StringVar(value=self.window_title)
        title_entry = ctk.CTkEntry(row["control_frame"],
                                    textvariable=self.title_var
                                    )
        title_entry.pack(fill=tk.X)
        title_entry.bind("<KeyRelease>",
                          lambda e: self._window_title_changed()
                          )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Canvas Width:")
        self._clear_prop_row(row)
        var_w = tk.StringVar(value=str(self.CANVAS_W))
        ctk.CTkEntry(row["control_frame"], textvariable=var_w).pack(
            fill=tk.X
            )
        var_w.trace_add("write",
                         lambda *a: self._apply_canvas_size_from_props(var_w,
                                                                        None,
                                                                        None
                                                                        )
                         )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Canvas Height:")
        self._clear_prop_row(row)
        var_h = tk.StringVar(value=str(self.CANVAS_H))
        ctk.CTkEntry(row["control_frame"], textvariable=var_h).pack(
            fill=tk.X
            )
        var_h.trace_add("write",
                         lambda *a: self._apply_canvas_size_from_props(None,
                                                                        var_h,
                                                                        None
                                                                        )
                         )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Background:")
        self._clear_prop_row(row)
        var_bg = tk.StringVar(value=self.CANVAS_BG)
        frame_bg = ctk.CTkFrame(row["control_frame"],
                                 fg_color="transparent"
                                 )
        frame_bg.pack(fill=tk.X)
        ctk.CTkEntry(frame_bg, textvariable=var_bg, width=100).pack(
            side=tk.LEFT, fill=tk.X, expand=True
            )
        ctk.CTkButton(frame_bg, text="Pick", width=60, height=28,
                       command=lambda v=var_bg: self._pick_color(v)
                       ).pack(side=tk.RIGHT, padx=(4, 0))
        rgb_lbl_bg = ctk.CTkLabel(
            row["control_frame"], text=self._rgb_label_text(var_bg.get()),
            font=("Segoe UI", 10), text_color="#757575", anchor="w"
            )
        rgb_lbl_bg.pack(fill=tk.X, pady=(1, 0))
        var_bg.trace_add(
            "write",
            lambda *a, v=var_bg, lbl=rgb_lbl_bg: lbl.configure(
                text=self._rgb_label_text(v.get())
                )
            )
        var_bg.trace_add("write",
                          lambda *a: self._apply_canvas_size_from_props(None,
                                                                         None,
                                                                         var_bg
                                                                         )
                          )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

    def _apply_canvas_size_from_props(self, var_w, var_h, var_bg):
        try:
            if var_w:
                self.CANVAS_W = int(var_w.get())
            if var_h:
                self.CANVAS_H = int(var_h.get())
            if var_bg:
                self.CANVAS_BG = var_bg.get()
            self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H,
                                bg=self.CANVAS_BG,
                                scrollregion=(0, 0, self.CANVAS_W,
                                                self.CANVAS_H)
                                )
            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
            self._update_code_for_canvas_change()
            self._update_code()
            if hasattr(self, "_prop_save_timer"):
                self.root.after_cancel(self._prop_save_timer)
            self._prop_save_timer = self.root.after(500, self._save_state)
        except ValueError:
            pass

    def _update_code_for_canvas_change(self):
        if self.full_code:
            self.full_code = re.sub(
                r'root\.geometry\([^\)]+\)',
                f'root.geometry("{self.CANVAS_W}x{self.CANVAS_H}")',
                self.full_code
            )
            self.full_code = re.sub(
                r'root\.configure\(bg=[^\)]+\)',
                f'root.configure(bg="{self.CANVAS_BG}")',
                self.full_code
            )
        else:
            self._invalidate_full_code()
            self._update_code()

    def _on_live_prop_change(self, row):
        if not self.selected_elems or len(self.selected_elems
                                           ) > 1 or not row.get("visible"):
            return
        elem = self.selected_elems[0]
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None:
            return

        value = var.get()

        if field_key == "orient" and elem.elem_type in ("Scale", "Separator",
                                                        "Progressbar",
                                                        "Scrollbar"):
            if value == "vertical" and elem.canvas_w > elem.canvas_h:
                elem.canvas_w, elem.canvas_h = elem.canvas_h, elem.canvas_w
            elif value == "horizontal" and elem.canvas_h > elem.canvas_w:
                elem.canvas_w, elem.canvas_h = elem.canvas_h, elem.canvas_w

        if field_key == "canvas_w":
            try:
                elem.canvas_w = int(value)
            except ValueError:
                pass
        elif field_key == "canvas_h":
            try:
                elem.canvas_h = int(value)
            except ValueError:
                pass
        elif field_key == "font":
            try:
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list):
                    parsed = tuple(parsed)
                elem.props["font"] = parsed if isinstance(parsed, tuple) else value
            except:
                elem.props["font"] = value
        elif field_key in ("values", "items"):
            elem.props[field_key] = [v.strip() for v in value.split(",") if
                                     v.strip()]
        elif elem.elem_type == "Notebook" and field_key == "tabs":
            tabs = [v.strip() for v in value.split(",") if v.strip()] or [
                "Tab 1"]
            elem.props["tabs"] = tabs
            elem.props["active_tab"] = min(
                int(elem.props.get("active_tab", 0) or 0), len(tabs) - 1
                )
            for child in self._children_by_parent.get(elem.elem_id, []):
                if child.parent_tab is not None and child.parent_tab >= len(tabs):
                    child.parent_tab = len(tabs) - 1
            self._show_properties(elem)
        elif elem.elem_type == "Notebook" and field_key == "active_tab":
            try:
                idx = max(0, int(value) - 1)
            except ValueError:
                idx = 0
            tabs = elem.props.get("tabs") or ["Tab 1"]
            elem.props["active_tab"] = min(idx, len(tabs) - 1)
            self._show_properties(elem)
        else:
            try:
                elem.props[field_key] = int(value)
            except ValueError:
                try:
                    elem.props[field_key] = float(value)
                except ValueError:
                    elem.props[field_key] = value

        self.renderer.redraw_element(elem)
        self._update_code_for_element(elem)
        self._update_code()

        if hasattr(self, "_prop_save_timer"):
            self.root.after_cancel(self._prop_save_timer)
        self._prop_save_timer = self.root.after(500, self._save_state)

    def _update_code_for_element(self, elem: DesignElement):
        if not self.full_code:
            self._invalidate_full_code()
            self._update_code()
            return

        widget_line, place_line, extra_lines = CodeGenerator.generate_element_lines(
            elem, self.elements
            )
        widget_pattern = rf'        self\._elem_{elem.elem_id} = .+'
        place_pattern = rf'        self\._elem_{elem.elem_id}\.place\(.+'

        lines = self.full_code.splitlines(keepends=True)
        new_lines = []
        widget_found = False
        place_found = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if not widget_found and re.match(widget_pattern, line):
                widget_found = True
                block_lines = []
                block_start = i
                while i < len(lines):
                    current = lines[i]
                    if re.match(place_pattern, current):
                        block_lines.append(current)
                        i += 1
                        place_found = True
                        break
                    if re.match(r'        self\._elem_\d+ = ', current
                                 ) and current != lines[block_start]:
                        break
                    block_lines.append(current)
                    i += 1
                new_block = [widget_line]
                if extra_lines:
                    new_block.extend(extra_lines)
                new_block.append(place_line)
                new_lines.extend([l + '\n' for l in new_block])
                continue
            else:
                new_lines.append(line)
                i += 1

        if not widget_found or not place_found:
            self._invalidate_full_code()
            self._update_code()
        else:
            self.full_code = ''.join(new_lines)
            self._current_code = self.full_code

    def _pick_color(self, var: tk.StringVar):
        color = colorchooser.askcolor(initialcolor=var.get() or "#ffffff",
                                       title="Select Color"
                                       )
        if color[1]:
            var.set(color[1])

    def _rgb_label_text(self, hex_color: str) -> str:
        """RGB text for a "#RRGGBB" color, for the small label shown next
        to each color field's hex entry. The color picker dialog itself
        shows RGB sliders (a native OS control we can't restyle), but the
        field stores/generates hex (the only format CTk widgets accept) --
        showing both side by side means neither value looks unexplained.
        """
        hc = (hex_color or "").strip()
        if len(hc) == 7 and hc.startswith("#"):
            try:
                r, g, b = int(hc[1:3], 16), int(hc[3:5], 16), int(hc[5:7], 16)
                return f"RGB {r}, {g}, {b}"
            except ValueError:
                pass
        return ""

    def _update_code(self):
        if self.full_code is not None:
            code = self.full_code
        else:
            code = CodeGenerator.generate(
                self.elements, self.window_title,
                (self.CANVAS_W, self.CANVAS_H),
                self.CANVAS_BG, self.canvas_imports
            )
            self.full_code = code
        self._current_code = code
        self._update_code_display()

    def _window_title_changed(self):
        if hasattr(self, "title_var"):
            self.window_title = self.title_var.get()
            if self.full_code:
                self.full_code = re.sub(
                    r'root\.title\([^\)]+\)',
                    f'root.title({json.dumps(self.window_title)})',
                    self.full_code
                )
                self._current_code = self.full_code
                self._update_code_display()
            if hasattr(self, "_title_save_timer"):
                self.root.after_cancel(self._title_save_timer)
            self._title_save_timer = self.root.after(500, self._save_state)

    def _update_element_count(self):
        self.count_var.set(f"Elements: {len(self.elements)}")

    def _update_status(self, msg: str):
        self.status_var.set(msg)

    def _save_to_path(self, path: str):
        try:
            self._save_state()
            state_str = self.undo_stack[-1] if self.undo_stack else "{}"
            with open(path, "w", encoding="utf-8") as f:
                f.write(state_str)
            self.current_file_path = path
            self._is_modified = False
            self._update_window_title_display()
            self._update_status(f"Saved design to {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _save_design(self):
        if self.current_file_path:
            self._save_to_path(self.current_file_path)
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".tvd",
                filetypes=[("Tkinter Visual Design", "*.tvd"),
                           ("All Files", "*.*")]
            )
            if path:
                self._save_to_path(path)

    def _load_design(self):
        path = filedialog.askopenfilename(
            filetypes=[("Tkinter Visual Design", "*.tvd"),
                       ("All Files", "*.*")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state_str = f.read()
                self.undo_stack.clear()
                self.redo_stack.clear()
                self.undo_stack.append(state_str)
                self._load_state(state_str)
                self.current_file_path = path
                self._is_modified = False
                self._update_window_title_display()
                self._update_status(
                    f"Loaded design from {os.path.basename(path)}"
                    )
            except Exception as e:
                messagebox.showerror("Load Error", str(e))

    def _new_design(self):
        if self._is_modified:
            if not messagebox.askyesno("Confirm New",
                                        "You have unsaved changes. Create new design anyway?"
                                        ):
                return
        self.current_file_path = None
        self._is_modified = False
        self.elements.clear()
        self._rebuild_index()
        self.selected_elems.clear()
        self.reusable_ids.clear()
        self.next_id = 1
        self.window_title = "My Application"
        self.CANVAS_W = 800
        self.CANVAS_H = 600
        self.CANVAS_BG = "#FAFAFA"
        self.canvas_imports = "import tkinter as tk\nfrom tkinter import ttk"
        self.full_code = None
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.canvas.delete("all")
        self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
        self._show_properties(None)
        self._update_code()
        self._update_element_count()
        self._save_state()
        self._update_window_title_display()
        self._update_status("Created new design.")

    def _copy_code(self):
        code = self._current_code
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self._update_status("Code copied to clipboard.")

    def _run_preview(self):
        try:
            # Regenerate fresh from the current canvas state rather than
            # trusting a possibly-stale self._current_code cache.
            code = CodeGenerator.generate(
                self.elements, self.window_title,
                (self.CANVAS_W, self.CANVAS_H),
                self.CANVAS_BG, self.canvas_imports
            )
        except Exception as e:
            messagebox.showerror("Run Preview Error",
                                  f"Failed to generate code:\n{e}")
            return

        if not code or not code.strip():
            messagebox.showerror("Run Preview Error",
                                  "Generated code is empty - nothing to run.")
            return

        try:
            fd, temp_path = tempfile.mkstemp(suffix=".py")
            os.close(fd)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            messagebox.showerror("Run Preview Error",
                                  f"Failed to write preview file:\n{e}")
            return

        try:
            proc = subprocess.Popen(
                [sys.executable, temp_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            self._update_status("Running Code Preview...")
        except Exception as e:
            messagebox.showerror("Run Preview Error", str(e))
            return

        # If the preview script crashes immediately (e.g. a bug in the
        # generated code), Popen itself won't raise - the process just
        # exits on its own. Poll shortly after launch so that failure is
        # actually surfaced instead of silently doing nothing.
        def _check_preview_alive():
            ret = proc.poll()
            if ret is not None and ret != 0:
                try:
                    _, stderr_out = proc.communicate(timeout=1)
                except Exception:
                    stderr_out = ""
                messagebox.showerror(
                    "Run Preview Error",
                    f"Preview exited immediately (code {ret}).\n\n{stderr_out or 'No error output captured.'}"
                )

        self.root.after(800, _check_preview_alive)

    def _open_code_editor(self, elem: DesignElement):
        top = ctk.CTkToplevel(self.root)
        top.title(f"Code Editor - {elem.elem_type} (ID: {elem.elem_id})")
        top.geometry("900x680")
        top.minsize(650, 450)

        editor_frame = ctk.CTkFrame(top, corner_radius=0)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        text_widget = tk.Text(editor_frame, font=("Consolas", 10),
                               bg="white", fg="black", wrap=tk.NONE,
                               undo=True, padx=8, pady=6
                               )
        y_scroll = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL,
                                  command=text_widget.yview
                                  )
        x_scroll = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL,
                                  command=text_widget.xview
                                  )
        text_widget.configure(yscrollcommand=y_scroll.set,
                               xscrollcommand=x_scroll.set
                               )
        text_widget.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        text_widget.tag_config("syntax_error", background="#FF4444",
                                foreground="white"
                                )

        full_code = self._current_code
        text_widget.insert("1.0", full_code)

        method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
        target = text_widget.search(f"def {method_name}", "1.0", tk.END
                                     ) or text_widget.search(
            f"self._elem_{elem.elem_id}", "1.0", tk.END
            )
        if target:
            target = text_widget.index(f"{target} linestart")
            text_widget.mark_set("insert", target)
            text_widget.see(target)
            text_widget.xview_moveto(0.0)
            text_widget.tag_add("highlight", target, f"{target} lineend")
            text_widget.tag_config("highlight", background="#FFF2CC",
                                    foreground="black"
                                    )

        syntax_bar = ctk.CTkFrame(top, height=28, corner_radius=0)
        syntax_bar.pack(fill=tk.X, padx=5, pady=(0, 2))
        syntax_bar.pack_propagate(False)
        syntax_status_var = tk.StringVar(value="Ready")
        line_col_var = tk.StringVar(value="Ln 1, Col 1")
        syntax_status_label = ctk.CTkLabel(syntax_bar,
                                            textvariable=syntax_status_var,
                                            anchor="w"
                                            )
        syntax_status_label.pack(side=tk.LEFT, padx=8)
        line_col_label = ctk.CTkLabel(syntax_bar, textvariable=line_col_var,
                                       anchor="e"
                                       )
        line_col_label.pack(side=tk.RIGHT, padx=8)

        _syntax_timer_id = [None]

        def _check_syntax():
            text_widget.tag_remove("syntax_error", "1.0", tk.END)
            code = text_widget.get("1.0", "end-1c")
            try:
                ast.parse(code)
                syntax_status_var.set("✓ No syntax errors")
                syntax_status_label.configure(
                    text_color=("#1B7F3B", "#4ADE80")
                    )
                return True
            except SyntaxError as e:
                lineno = e.lineno or 1
                msg = e.msg or "invalid syntax"
                syntax_status_var.set(
                    f"✗ Syntax error (line {lineno}): {msg}"
                    )
                syntax_status_label.configure(
                    text_color=("#C62828", "#FF6B6B")
                    )
                try:
                    text_widget.tag_add("syntax_error", f"{lineno}.0",
                                         f"{lineno}.end"
                                         )
                except Exception:
                    pass
                return False

        def _schedule_check(event=None):
            if _syntax_timer_id[0] is not None:
                try:
                    top.after_cancel(_syntax_timer_id[0])
                except Exception:
                    pass
            _syntax_timer_id[0] = top.after(400, _check_syntax)

        def _update_line_col(event=None):
            try:
                idx = text_widget.index("insert")
                line, col = idx.split(".")
                line_col_var.set(f"Ln {line}, Col {int(col) + 1}")
            except Exception:
                pass

        btn_frame = ctk.CTkFrame(top, corner_radius=0)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        def save_code():
            if not _check_syntax():
                proceed = messagebox.askyesno(
                    "Syntax Error",
                    "The code contains a syntax error. Save anyway?",
                    parent=top,
                )
                if not proceed:
                    self._update_status("Save cancelled due to syntax error.")
                    return
            edited_code = text_widget.get("1.0", "end-1c")
            self.full_code = edited_code
            try:
                lines = edited_code.splitlines()
                def_index = next(i for i, line in enumerate(lines) if
                                  line.startswith(f"    def {method_name}(")
                                  )
                end_index = len(lines)
                for i in range(def_index + 1, len(lines)):
                    if lines[i].startswith("    def ") or lines[i].startswith(
                            "if __name__ =="
                            ):
                        end_index = i
                        break
                body_lines = lines[def_index + 1:end_index]
                cleaned = []
                for line in body_lines:
                    cleaned.append(
                        line[8:] if line.startswith("        ") else (
                            "" if not line.strip() else line.strip())
                        )
                elem.handler_code = "\n".join(cleaned).strip() or "pass"
            except (StopIteration, ValueError):
                pass
            self._update_code()
            self._save_state()
            self._update_status(
                f"Saved full code and handler for {elem.elem_type} ID {elem.elem_id}."
                )
            refreshed = self._current_code
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", refreshed)
            pos = text_widget.search(f"def {method_name}", "1.0", tk.END)
            if pos:
                pos = text_widget.index(f"{pos} linestart")
                text_widget.mark_set("insert", pos)
                text_widget.see(pos)
                text_widget.xview_moveto(0.0)

        def open_in_vscode():
            edited_code = text_widget.get("1.0", tk.END)
            fd, temp_path = tempfile.mkstemp(suffix=".py")
            os.close(fd)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(edited_code)
            try:
                subprocess.Popen(["code", temp_path], shell=True)
                self._update_status(
                    "Opened temporary generated code in VS Code."
                    )
            except Exception as e:
                messagebox.showerror("Execution Error",
                                      f"Could not launch VS Code. Ensure 'code' is in PATH.\n\n{e}",
                                      parent=top
                                      )

        ctk.CTkButton(btn_frame, text="💾 Save", command=save_code,
                       width=100, height=28
                       ).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(btn_frame, text="💻 Open in VS Code",
                       command=open_in_vscode, width=150, height=28
                       ).pack(side=tk.LEFT, padx=2)
        ctk.CTkButton(btn_frame, text="Close", command=top.destroy,
                       width=80, height=28
                       ).pack(side=tk.RIGHT, padx=2)
        text_widget.bind("<KeyRelease>",
                          lambda event: (_schedule_check(), _update_line_col()),
                          add="+"
                          )
        text_widget.bind("<ButtonRelease-1>", _update_line_col, add="+")
        text_widget.bind("<Control-s>",
                          lambda event: (save_code(), "break")[1]
                          )
        text_widget.focus_set()
        top.after(100, _check_syntax)

    def _select_all(self, event=None):
        all_visible = self._visible_elements()
        if not all_visible:
            return
        self._select_element(None, clear=True)
        for elem in all_visible:
            self._select_element(elem, clear=False)
        self._update_status(f"Selected {len(all_visible)} elements.")


if __name__ == "__main__":
    root = ctk.CTk()
    app = GUIBuilderApp(root)
    root.mainloop()