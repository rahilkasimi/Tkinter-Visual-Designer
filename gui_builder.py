#!/usr/bin/env python3
"""
Tkinter Visual GUI Designer
----------------------------
A drag‑and‑drop GUI builder for Tkinter.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, scrolledtext, filedialog, messagebox
import tkinter.font as tkfont
import json
import copy
import subprocess
import sys
import tempfile
import os
import ast
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

# ─── Constants ──────────────────────────────────────────────────────────────

MIN_W = 40
MIN_H = 20
HANDLE_HALF = 6
GRID_SIZE = 10

# ─── Element Catalogue ──────────────────────────────────────────────────────

ELEMENT_TYPES: Dict[str, Dict[str, Any]] = {
    "Label": {
        "display": "🏷️ Label",
        "widget": "tk.Label",
        "default_size": (120, 30),
        "defaults": {"text": "Label", "font": ("TkDefaultFont",), "fg": "black", "bg": "SystemButtonFace",
                     "relief": "flat", "justify": "center"},
        "tile_bg": "#E8F0FE", "tile_fg": "#1A237E",
        "category": "Input",
    },
    "Entry": {
        "display": "✍️ Entry",
        "widget": "tk.Entry",
        "default_size": (160, 30),
        "defaults": {"textvariable": "", "show": "", "width": 20, "font": ("TkDefaultFont",),
                     "fg": "black", "bg": "white", "relief": "sunken", "justify": "left", "default_value": ""},
        "tile_bg": "#FFFFFF", "tile_fg": "#212121",
        "category": "Input",
    },
    "Button": {
        "display": "🔘 Button",
        "widget": "tk.Button",
        "default_size": (100, 34),
        "defaults": {"text": "Button", "font": ("TkDefaultFont",), "fg": "black", "bg": "SystemButtonFace",
                     "relief": "raised", "command": ""},
        "tile_bg": "#3F51B5", "tile_fg": "#FFFFFF",
        "category": "Input",
    },
    "Radiobutton": {
        "display": "◉ Radiobutton",
        "widget": "tk.Radiobutton",
        "default_size": (130, 30),
        "defaults": {"text": "Option", "variable": "", "value": 1, "font": ("TkDefaultFont",),
                     "fg": "black", "bg": "SystemButtonFace", "relief": "flat"},
        "tile_bg": "#F3E5F5", "tile_fg": "#4A148C",
        "category": "Input",
    },
    "Checkbutton": {
        "display": "☑ Checkbutton",
        "widget": "tk.Checkbutton",
        "default_size": (130, 30),
        "defaults": {"text": "Checkbox", "variable": "", "onvalue": 1, "offvalue": 0,
                     "font": ("TkDefaultFont",), "fg": "black", "bg": "SystemButtonFace", "default_value": 0},
        "tile_bg": "#F1F8E9", "tile_fg": "#1B5E20",
        "category": "Input",
    },
    "Scale": {
        "display": "🎚️ Scale (Slider)",
        "widget": "tk.Scale",
        "default_size": (180, 40),
        "defaults": {"from_": 0, "to": 100, "orient": "horizontal", "length": 150,
                     "tickinterval": 0, "resolution": 1, "font": ("TkDefaultFont",),
                     "fg": "black", "bg": "SystemButtonFace", "default_value": 0},
        "tile_bg": "#FCE4EC", "tile_fg": "#880E4F",
        "category": "Input",
    },
    "Combobox": {
        "display": "🔽 Combobox",
        "widget": "ttk.Combobox",
        "default_size": (150, 30),
        "defaults": {"values": ["Option 1", "Option 2", "Option 3"], "state": "readonly",
                     "font": ("TkDefaultFont",), "width": 18, "default_value": ""},
        "tile_bg": "#FFF3E0", "tile_fg": "#E65100",
        "category": "Input",
    },
    "Spinbox": {
        "display": "🔢 Spinbox",
        "widget": "tk.Spinbox",
        "default_size": (80, 30),
        "defaults": {"from_": 0, "to": 100, "width": 5, "font": ("TkDefaultFont",),
                     "fg": "black", "bg": "white", "relief": "sunken", "default_value": 0},
        "tile_bg": "#FFF8E1", "tile_fg": "#FF6F00",
        "category": "Input",
    },
    "Listbox": {
        "display": "📋 Listbox",
        "widget": "tk.Listbox",
        "default_size": (150, 80),
        "defaults": {"listvariable": "", "items": ["Item 1", "Item 2"], "height": 4, "width": 18,
                     "font": ("TkDefaultFont",), "fg": "black", "bg": "white",
                     "relief": "sunken", "selectmode": "single"},
        "tile_bg": "#E3F2FD", "tile_fg": "#0D47A1",
        "category": "Display",
    },
    "Text": {
        "display": "📝 Text (Multiline)",
        "widget": "tk.Text",
        "default_size": (200, 90),
        "defaults": {"height": 5, "width": 30, "font": ("TkDefaultFont",),
                     "fg": "black", "bg": "white", "relief": "sunken", "wrap": "word"},
        "tile_bg": "#FFFDE7", "tile_fg": "#F57F17",
        "category": "Display",
    },
    "Canvas": {
        "display": "🎨 Canvas (Drawing)",
        "widget": "tk.Canvas",
        "default_size": (200, 120),
        "defaults": {"width": 200, "height": 120, "bg": "white", "relief": "sunken", "bd": 2},
        "tile_bg": "#FFF8E1", "tile_fg": "#FF6F00",
        "category": "Display",
    },
    "Progressbar": {
        "display": "⏳ Progressbar (ttk)",
        "widget": "ttk.Progressbar",
        "default_size": (180, 30),
        "defaults": {"maximum": 100, "value": 40, "orient": "horizontal", "length": 180},
        "tile_bg": "#E8F5E9", "tile_fg": "#1B5E20",
        "category": "Display",
    },
    "Scrollbar": {
        "display": "↕️ Scrollbar",
        "widget": "tk.Scrollbar",
        "default_size": (20, 120),
        "defaults": {"orient": "vertical", "width": 16, "bg": "SystemButtonFace"},
        "tile_bg": "#CFD8DC", "tile_fg": "#37474F",
        "category": "Display",
    },
    "Frame": {
        "display": "🖼️ Frame (Container)",
        "widget": "tk.Frame",
        "default_size": (200, 120),
        "defaults": {"relief": "groove", "bd": 2, "bg": "SystemButtonFace"},
        "tile_bg": "#ECEFF1", "tile_fg": "#263238",
        "category": "Containers",
    },
    "LabelFrame": {
        "display": "🗂️ LabelFrame",
        "widget": "tk.LabelFrame",
        "default_size": (200, 120),
        "defaults": {"text": "LabelFrame", "relief": "groove", "bd": 2, "bg": "SystemButtonFace", "font": ("TkDefaultFont",)},
        "tile_bg": "#E0F2F1", "tile_fg": "#004D40",
        "category": "Containers",
    },
    "Notebook": {
        "display": "📑 Notebook (Tabs)",
        "widget": "ttk.Notebook",
        "default_size": (260, 160),
        "defaults": {"tabs": ["Tab 1", "Tab 2"], "active_tab": 0},
        "tile_bg": "#EDE7F6", "tile_fg": "#311B92",
        "category": "Containers",
    },
    "PanedWindow": {
        "display": "🪟 PanedWindow",
        "widget": "tk.PanedWindow",
        "default_size": (200, 120),
        "defaults": {"orient": "horizontal", "bg": "SystemButtonFace", "sashrelief": "raised"},
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
}

# ─── Property Fields ──────────────────────────────────────────────────────

PROPERTY_FIELDS: Dict[str, List[Tuple]] = {
    "Label": [
        ("text", "Text", "entry"), ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("justify", "Justify", "combobox", ["left", "center", "right"]),
    ],
    "Entry": [
        ("textvariable", "Variable", "entry"), ("show", "Password char", "entry"), ("width", "Width", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("justify", "Justify", "combobox", ["left", "center", "right"]),
        ("default_value", "Default Value", "entry"),
    ],
    "Button": [
        ("text", "Text", "entry"), ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("command", "Command", "text"),
    ],
    "Radiobutton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"), ("value", "Value", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"), ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]),
    ],
    "Checkbutton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"), ("onvalue", "On Value", "entry"), ("offvalue", "Off Value", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("default_value", "Default Value", "entry"),
    ],
    "Scale": [
        ("from_", "From", "entry"), ("to", "To", "entry"), ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("length", "Length", "entry"), ("tickinterval", "Tick interval", "entry"), ("resolution", "Resolution", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("default_value", "Default Value", "entry"),
    ],
    "Listbox": [
        ("listvariable", "Variable", "entry"), ("items", "Items (csv)", "entry"), ("height", "Height (rows)", "entry"), ("width", "Width (chars)", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("selectmode", "Select mode", "combobox", ["single", "browse", "multiple", "extended"]),
    ],
    "Text": [
        ("height", "Height (rows)", "entry"), ("width", "Width (chars)", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"), ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]),
        ("wrap", "Wrap", "combobox", ["none", "char", "word"]),
    ],
    "Frame": [
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("bd", "Border width", "entry"), ("bg", "Background", "color"),
    ],
    "LabelFrame": [
        ("text", "Text", "entry"), ("font", "Font", "font"), ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("bd", "Border width", "entry"), ("bg", "Background", "color"),
    ],
    "Notebook": [
        ("tabs", "Tabs", "entry"),
        ("active_tab", "Active Tab", "combobox", []),
    ],
    "PanedWindow": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]), ("bg", "Background", "color"), ("sashrelief", "Sash relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]),
    ],
    "Separator": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("canvas_w", "Width (px)", "entry"),
        ("canvas_h", "Height (px)", "entry")
    ],
    "Canvas": [
        ("width", "Width", "entry"), ("height", "Height", "entry"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]), ("bd", "Border width", "entry"),
    ],
    "Scrollbar": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]), ("width", "Width", "entry"), ("bg", "Background", "color"),
    ],
    "Combobox": [
        ("values", "Values (csv)", "entry"), ("state", "State", "combobox", ["normal", "readonly", "disabled"]),
        ("font", "Font", "font"), ("width", "Width (chars)", "entry"),
        ("default_value", "Default Value", "entry"),
    ],
    "Spinbox": [
        ("from_", "From", "entry"), ("to", "To", "entry"), ("width", "Width (chars)", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"), ("bg", "Background", "color"), ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge"]),
        ("default_value", "Default Value", "entry"),
    ],
    "Progressbar": [
        ("maximum", "Maximum", "entry"), ("value", "Current value", "entry"), ("orient", "Orientation", "combobox", ["horizontal", "vertical"]), ("length", "Length", "entry"),
    ],
    "Table": [
        ("file", "Excel/CSV File", "file"),
        ("sheet", "Sheet Name", "entry"),
        ("columns", "Columns (csv)", "entry"),
        ("height", "Rows visible", "entry"),
    ],
}

DEFAULT_EVENT_MAP = {
    "Button": "command", "Entry": "<KeyRelease>", "Radiobutton": "command", "Checkbutton": "command",
    "Scale": "command", "Listbox": "<<ListboxSelect>>", "Text": "<KeyRelease>", "Combobox": "<<ComboboxSelected>>",
    "Spinbox": "<KeyRelease>", "Progressbar": None, "Label": None, "Frame": None, "LabelFrame": None,
    "Notebook": None, "PanedWindow": None, "Separator": None,
    "Canvas": None, "Scrollbar": None, "Table": None,
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

    def __post_init__(self):
        if self.canvas_w == 0:
            self.canvas_w = ELEMENT_TYPES[self.elem_type]["default_size"][0]
        if self.canvas_h == 0:
            self.canvas_h = ELEMENT_TYPES[self.elem_type]["default_size"][1]
        if self.elem_type == "Notebook":
            tabs = self.props.get("tabs")
            if not isinstance(tabs, list) or not tabs:
                self.props["tabs"] = ["Tab 1", "Tab 2"]
            self.props["active_tab"] = max(0, min(int(self.props.get("active_tab", 0) or 0), len(self.props.get("tabs", ["Tab 1"])) - 1))

    @property
    def display_label(self) -> str:
        # Fix: treat text=0 as a valid value, not as falsy
        text_val = self.props.get("text")
        if text_val is not None:
            label = str(text_val)
        elif self.props.get("default_text") is not None:
            label = str(self.props["default_text"])
        else:
            label = self.elem_type
        return (label[:15] + "…") if len(label) > 15 else label

    def contains_point(self, px: int, py: int) -> bool:
        return (self.x <= px <= self.x + self.canvas_w and self.y <= py <= self.y + self.canvas_h)

    def handle_positions(self) -> Dict[str, Tuple[int, int]]:
        x, y, w, h = self.x, self.y, self.canvas_w, self.canvas_h
        mx, my = x + w // 2, y + h // 2
        return {
            "NW": (x, y), "N": (mx, y), "NE": (x + w, y), "E": (x + w, my),
            "SE": (x + w, y + h), "S": (mx, y + h), "SW": (x, y + h), "W": (x, my),
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
        elem = cls(
            elem_type=data["elem_type"],
            x=data["x"],
            y=data["y"],
            props=data["props"],
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
    def _container_depth(elem: DesignElement, by_id: Dict[int, DesignElement]) -> int:
        depth = 0
        seen = set()
        current = elem
        while current.parent_id is not None and current.parent_id in by_id and current.parent_id not in seen:
            seen.add(current.parent_id)
            current = by_id[current.parent_id]
            depth += 1
        return depth

    @staticmethod
    def generate(elements: List[DesignElement], window_title: str, window_size: Tuple[int, int], canvas_bg: str, canvas_imports: str) -> str:
        if not elements:
            return CodeGenerator._empty_template(window_title, window_size, canvas_bg, canvas_imports)

        has_table = any(e.elem_type == "Table" for e in elements)
        if has_table and "import pandas as pd" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport pandas as pd"

        by_id = {e.elem_id: e for e in elements}
        class_body: List[str] = []
        class_body.append("    def __init__(self, root):")
        class_body.append("        self.root = root")
        class_body.append(f"        root.title({json.dumps(window_title)})")
        class_body.append(f"        root.geometry({json.dumps(f'{window_size[0]}x{window_size[1]}')})")
        class_body.append(f"        root.configure(bg={json.dumps(canvas_bg)})")
        class_body.append("")

        vars_to_create = {}
        for elem in elements:
            if elem.elem_type in ("Radiobutton", "Checkbutton"):
                var_name = elem.props.get("variable")
                if var_name and var_name not in vars_to_create:
                    var_type = "tk.IntVar(value=0)" if elem.elem_type == "Checkbutton" else "tk.StringVar(value='')"
                    vars_to_create[var_name] = var_type
        for v_name, v_type in vars_to_create.items():
            class_body.append(f"        self.{v_name} = {v_type}")
        if vars_to_create:
            class_body.append("")

        bindings = []
        for elem in elements:
            if elem.handler_code.strip():
                event = DEFAULT_EVENT_MAP.get(elem.elem_type)
                if event:
                    bindings.append((elem, event, f"self._elem_{elem.elem_id}"))

        ordered = sorted(elements, key=lambda e: (CodeGenerator._container_depth(e, by_id), e.elem_id))

        for elem in ordered:
            var_name = f"self._elem_{elem.elem_id}"
            widget_class = ELEMENT_TYPES[elem.elem_type]["widget"]
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

            prop_strs = []
            for k, v in props.items():
                if k == "variable" and v:
                    prop_strs.append(f"variable=self.{v}")
                elif k == "command" and isinstance(v, str) and v.startswith("self."):
                    prop_strs.append(f"{k}={v}")
                elif k == "values" and isinstance(v, list):
                    prop_strs.append(f"{k}={repr(v)}")
                elif k in ("from_", "to", "onvalue", "offvalue"):
                    prop_strs.append(f"{k}={v}")
                elif isinstance(v, str):
                    prop_strs.append(f"{k}={json.dumps(v)}")
                elif isinstance(v, (int, float)):
                    prop_strs.append(f"{k}={v}")
                else:
                    prop_strs.append(f"{k}={repr(v)}")
            prop_str = (", " + ", ".join(prop_strs)) if prop_strs else ""

            parent_name = "root"
            rel_x, rel_y = elem.x, elem.y
            if elem.parent_id is not None and elem.parent_id in by_id:
                parent_elem = by_id[elem.parent_id]
                if parent_elem.elem_type == "Notebook":
                    tab_idx = elem.parent_tab if elem.parent_tab is not None else parent_elem.props.get("active_tab", 0)
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

                class_body.append(f"        columns = []")
                if columns_csv:
                    cols = [c.strip() for c in columns_csv.split(",") if c.strip()]
                    class_body.append(f"        columns = {repr(cols)}")
                class_body.append(f"        {var_name} = ttk.Treeview({parent_name}, columns=columns, show='headings', height={table_height})")
                class_body.append(f"        for col in columns:")
                class_body.append(f"            {var_name}.heading(col, text=col)")
                class_body.append(f"            {var_name}.column(col, width=100, anchor='w')")
                if table_file:
                    class_body.append(f"        try:")
                    class_body.append(f"            import pandas as pd")
                    if str(table_file).lower().endswith(('.xlsx', '.xls')):
                        class_body.append(f"            df = pd.read_excel({json.dumps(table_file)}, sheet_name={json.dumps(table_sheet) if table_sheet else 0})")
                    else:
                        class_body.append(f"            df = pd.read_csv({json.dumps(table_file)})")
                    class_body.append(f"            if not columns:")
                    class_body.append(f"                columns = list(df.columns)")
                    class_body.append(f"                for col in columns:")
                    class_body.append(f"                    {var_name}.heading(col, text=col)")
                    class_body.append(f"                    {var_name}.column(col, width=100, anchor='w')")
                    class_body.append(f"            for _, row in df.head(10).iterrows():")
                    class_body.append(f"                {var_name}.insert('', 'end', values=list(row))")
                    class_body.append(f"        except Exception as e:")
                    class_body.append(f"            print('Table load error:', e)")
            else:
                class_body.append(f"        {var_name} = {widget_class}({parent_name}{prop_str})")

            if elem.elem_type == "Notebook":
                if not notebook_tabs:
                    notebook_tabs = ["Tab 1"]
                for i, tab_title in enumerate(notebook_tabs):
                    class_body.append(f"        {var_name}_tab_{i} = ttk.Frame({var_name})")
                    class_body.append(f"        {var_name}.add({var_name}_tab_{i}, text={json.dumps(str(tab_title))})")
                    class_body.append(f"        self._elem_{elem.elem_id}_tab_{i} = {var_name}_tab_{i}")
                active_tab = int(elem.props.get("active_tab", 0) or 0)
                active_tab = max(0, min(active_tab, len(notebook_tabs) - 1))
                class_body.append(f"        {var_name}.select({active_tab})")

            if def_val is not None and str(def_val).strip() != "":
                if elem.elem_type == "Checkbutton":
                    var_name_chk = copy.deepcopy(elem.props).get("variable")
                    if var_name_chk:
                        class_body.append(f"        self.{var_name_chk}.set({json.dumps(def_val)})")
                    elif str(def_val).lower() in ("1", "true", "yes"):
                        class_body.append(f"        {var_name}.select()")
                elif elem.elem_type in ("Entry", "Spinbox"):
                    class_body.append(f"        {var_name}.insert(0, {json.dumps(str(def_val))})")
                elif elem.elem_type == "Combobox":
                    class_body.append(f"        {var_name}.set({json.dumps(str(def_val))})")
                elif elem.elem_type == "Scale":
                    try:
                        num_val = float(def_val) if "." in str(def_val) else int(def_val)
                        class_body.append(f"        {var_name}.set({num_val})")
                    except (ValueError, TypeError):
                        pass

            if elem.elem_type == "Listbox" and listbox_items:
                for item in listbox_items:
                    class_body.append(f"        {var_name}.insert('end', {json.dumps(item)})")

            class_body.append(f"        {var_name}.place(x={rel_x}, y={rel_y}, width={elem.canvas_w}, height={elem.canvas_h})")

        for elem, event, var_name in bindings:
            if event != "command":
                method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                class_body.append(f"        {var_name}.bind('{event}', self.{method_name})")

        for elem, event, var_name in bindings:
            method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
            class_body.append("")
            class_body.append(f"    def {method_name}(self, event=None):")
            code_lines = elem.handler_code.strip().splitlines() or ["pass"]
            for cline in code_lines:
                class_body.append(f"        {cline}" if cline.strip() else "        ")

        class_body.append("")
        main_guard = [
            "", "if __name__ == '__main__':", "    root = tk.Tk()",
            "    app = MainApplication(root)", "    root.mainloop()",
        ]

        return "\n".join([
            '"""Generated by Tkinter Visual Designer."""', "",
            canvas_imports, "", "",
            "class MainApplication:", *class_body, *main_guard,
        ])

    @staticmethod
    def _empty_template(window_title: str, window_size: Tuple[int, int], canvas_bg: str, canvas_imports: str) -> str:
        return f'''"""Generated by Tkinter Visual Designer."""

{canvas_imports}


def main():
    root = tk.Tk()
    root.title({json.dumps(window_title)})
    root.geometry({json.dumps(f"{window_size[0]}x{window_size[1]}")})
    root.configure(bg={json.dumps(canvas_bg)})
    label = tk.Label(root, text="Add elements from the toolbox to begin!")
    label.place(x=10, y=10)
    root.mainloop()

if __name__ == "__main__":
    main()
'''

    # ─── Helper to generate lines for a single element ────────────────────
    @staticmethod
    def generate_element_lines(elem: DesignElement, all_elements: List[DesignElement]) -> Tuple[str, str, List[str]]:
        """
        Returns (widget_creation_line, place_line, extra_lines)
        where extra_lines contain any additional lines related to this element
        (e.g., Notebook tab frames, Listbox insertions, etc.).
        """
        by_id = {e.elem_id: e for e in all_elements}
        widget_line = ""
        place_line = ""
        extra_lines: List[str] = []

        var_name = f"self._elem_{elem.elem_id}"
        widget_class = ELEMENT_TYPES[elem.elem_type]["widget"]
        props = copy.deepcopy(elem.props)

        # Determine if this element has a command binding
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

        prop_strs = []
        for k, v in props.items():
            if k == "variable" and v:
                prop_strs.append(f"variable=self.{v}")
            elif k == "command" and isinstance(v, str) and v.startswith("self."):
                prop_strs.append(f"{k}={v}")
            elif k == "values" and isinstance(v, list):
                prop_strs.append(f"{k}={repr(v)}")
            elif k in ("from_", "to", "onvalue", "offvalue"):
                prop_strs.append(f"{k}={v}")
            elif isinstance(v, str):
                prop_strs.append(f"{k}={json.dumps(v)}")
            elif isinstance(v, (int, float)):
                prop_strs.append(f"{k}={v}")
            else:
                prop_strs.append(f"{k}={repr(v)}")
        prop_str = (", " + ", ".join(prop_strs)) if prop_strs else ""

        parent_name = "root"
        rel_x, rel_y = elem.x, elem.y
        if elem.parent_id is not None and elem.parent_id in by_id:
            parent_elem = by_id[elem.parent_id]
            if parent_elem.elem_type == "Notebook":
                tab_idx = elem.parent_tab if elem.parent_tab is not None else parent_elem.props.get("active_tab", 0)
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
            lines.append(f"        {var_name} = ttk.Treeview({parent_name}, columns=columns, show='headings', height={table_height})")
            lines.append(f"        for col in columns:")
            lines.append(f"            {var_name}.heading(col, text=col)")
            lines.append(f"            {var_name}.column(col, width=100, anchor='w')")
            if table_file:
                lines.append(f"        try:")
                lines.append(f"            import pandas as pd")
                if str(table_file).lower().endswith(('.xlsx', '.xls')):
                    lines.append(f"            df = pd.read_excel({json.dumps(table_file)}, sheet_name={json.dumps(table_sheet) if table_sheet else 0})")
                else:
                    lines.append(f"            df = pd.read_csv({json.dumps(table_file)})")
                lines.append(f"            if not columns:")
                lines.append(f"                columns = list(df.columns)")
                lines.append(f"                for col in columns:")
                lines.append(f"                    {var_name}.heading(col, text=col)")
                lines.append(f"                    {var_name}.column(col, width=100, anchor='w')")
                lines.append(f"            for _, row in df.head(10).iterrows():")
                lines.append(f"                {var_name}.insert('', 'end', values=list(row))")
                lines.append(f"        except Exception as e:")
                lines.append(f"            print('Table load error:', e)")
            widget_line = "\n".join(lines)
            place_line = f"        {var_name}.place(x={rel_x}, y={rel_y}, width={elem.canvas_w}, height={elem.canvas_h})"
            return widget_line, place_line, []

        # Normal widget creation
        widget_line = f"        {var_name} = {widget_class}({parent_name}{prop_str})"

        # Handle Notebook special lines
        if elem.elem_type == "Notebook":
            if not notebook_tabs:
                notebook_tabs = ["Tab 1"]
            for i, tab_title in enumerate(notebook_tabs):
                extra_lines.append(f"        {var_name}_tab_{i} = ttk.Frame({var_name})")
                extra_lines.append(f"        {var_name}.add({var_name}_tab_{i}, text={json.dumps(str(tab_title))})")
                extra_lines.append(f"        self._elem_{elem.elem_id}_tab_{i} = {var_name}_tab_{i}")
            active_tab = int(elem.props.get("active_tab", 0) or 0)
            active_tab = max(0, min(active_tab, len(notebook_tabs) - 1))
            extra_lines.append(f"        {var_name}.select({active_tab})")

        # Handle default value
        if def_val is not None and str(def_val).strip() != "":
            if elem.elem_type == "Checkbutton":
                var_name_chk = copy.deepcopy(elem.props).get("variable")
                if var_name_chk:
                    extra_lines.append(f"        self.{var_name_chk}.set({json.dumps(def_val)})")
                elif str(def_val).lower() in ("1", "true", "yes"):
                    extra_lines.append(f"        {var_name}.select()")
            elif elem.elem_type in ("Entry", "Spinbox"):
                extra_lines.append(f"        {var_name}.insert(0, {json.dumps(str(def_val))})")
            elif elem.elem_type == "Combobox":
                extra_lines.append(f"        {var_name}.set({json.dumps(str(def_val))})")
            elif elem.elem_type == "Scale":
                try:
                    num_val = float(def_val) if "." in str(def_val) else int(def_val)
                    extra_lines.append(f"        {var_name}.set({num_val})")
                except (ValueError, TypeError):
                    pass

        # Listbox items
        if elem.elem_type == "Listbox" and listbox_items:
            for item in listbox_items:
                extra_lines.append(f"        {var_name}.insert('end', {json.dumps(item)})")

        # Place line
        place_line = f"        {var_name}.place(x={rel_x}, y={rel_y}, width={elem.canvas_w}, height={elem.canvas_h})"

        return widget_line, place_line, extra_lines

# ─── CanvasRenderer ─────────────────────────────────────────────────────────

class CanvasRenderer:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas

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
        for x in range(0, width + 1, 20):
            self.canvas.create_line(x, 0, x, height, fill="#e0e0e0", tags="grid")
        for y in range(0, height + 1, 20):
            self.canvas.create_line(0, y, width, y, fill="#e0e0e0", tags="grid")
        self.canvas.tag_lower("grid")

    def draw_element(self, elem: DesignElement) -> None:
        x, y, w, h = elem.x, elem.y, elem.canvas_w, elem.canvas_h
        bg = self._get_valid_color(elem.props.get("bg"), ELEMENT_TYPES[elem.elem_type]["tile_bg"])
        fg = self._get_valid_color(elem.props.get("fg"), ELEMENT_TYPES[elem.elem_type]["tile_fg"])
        font = elem.props.get("font") or ("Segoe UI", 9)
        outline = "#FF6B35" if elem.selected else "#AAAAAA"
        width_outline = 2 if elem.selected else 1

        self.erase_element(elem)

        draw_func = getattr(self, f"_draw_{elem.elem_type.lower()}", self._draw_fallback)
        draw_func(elem, x, y, w, h, bg, fg, font, outline, width_outline)

        elem.handle_ids = {}
        if elem.selected:
            for name, (hx, hy) in elem.handle_positions().items():
                hid = self.canvas.create_rectangle(
                    hx - HANDLE_HALF, hy - HANDLE_HALF, hx + HANDLE_HALF, hy + HANDLE_HALF,
                    fill="#FF6B35", outline="white", width=1,
                    tags=("handle", f"handle_{elem.elem_id}_{name}")
                )
                elem.handle_ids[name] = hid
                
            del_x, del_y = x + w + 15, y - 15
            hid_bg = self.canvas.create_rectangle(del_x-8, del_y-8, del_x+8, del_y+8, fill="#E53935", outline="white", tags=("handle", f"del_{elem.elem_id}"))
            hid_l1 = self.canvas.create_line(del_x-4, del_y-4, del_x+4, del_y+4, fill="white", width=2, tags=("handle", f"del_{elem.elem_id}"))
            hid_l2 = self.canvas.create_line(del_x-4, del_y+4, del_x+4, del_y-4, fill="white", width=2, tags=("handle", f"del_{elem.elem_id}"))
            elem.handle_ids["DEL"] = hid_bg
            elem.handle_ids["DEL_L1"] = hid_l1
            elem.handle_ids["DEL_L2"] = hid_l2

        
        id_lbl_bg = self.canvas.create_rectangle(x + w//2 - 15, y - 17, x + w//2 + 15, y - 3, fill="#FF6B35", outline="white", tags=("handle", f"id_{elem.elem_id}"))
        id_lbl = self.canvas.create_text(x + w//2, y - 12, text=f"ID:{elem.elem_id}", fill="white", font=("Segoe UI", 8, "bold"), tags=("handle", f"id_{elem.elem_id}"))
        elem.handle_ids["ID_BG"] = id_lbl_bg
        elem.handle_ids["ID"] = id_lbl

    def _draw_label(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg, font)

    def _draw_entry(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        text = elem.props.get("textvariable") or elem.display_label
        self._render_text_on_canvas(elem, x+4, y, w-8, h, text, fg, font, anchor="w")

    def _draw_button(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_raised_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg, font)

    def _draw_radiobutton(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx = x + 20
        cy = y + h//2
        r = 6
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="black", fill=bg, tags=("element", f"elem_{elem.elem_id}"))
        if elem.props.get("value") == 1:
            self.canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="black", tags=("element", f"elem_{elem.elem_id}"))
        self._render_text_on_canvas(elem, x+25, y, w-25, h, elem.display_label, fg, font, anchor="w")

    def _draw_checkbutton(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx = x + 16
        cy = y + h//2
        size = 10
        self.canvas.create_rectangle(cx-size//2, cy-size//2, cx+size//2, cy+size//2, outline="black", fill=bg, tags=("element", f"elem_{elem.elem_id}"))
        if elem.props.get("onvalue") == 1:
            self.canvas.create_line(cx-3, cy, cx, cy+3, cx+5, cy-4, fill="black", width=2, tags=("element", f"elem_{elem.elem_id}"))
        self._render_text_on_canvas(elem, x+25, y, w-25, h, elem.display_label, fg, font, anchor="w")

    def _draw_scale(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        track_y = y + h//2
        track_len = w - 20
        self.canvas.create_line(x+10, track_y, x+10+track_len, track_y, fill="gray", width=4, tags=("element", f"elem_{elem.elem_id}"))
        thumb_x = x + 10 + int(track_len * 0.3)
        self.canvas.create_oval(thumb_x-6, track_y-6, thumb_x+6, track_y+6, fill="black", tags=("element", f"elem_{elem.elem_id}"))
        val = elem.props.get("to", 100) * 0.3
        self.canvas.create_text(x+w-5, track_y-10, text=str(int(val)), anchor="e", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_combobox(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        arrow_x = x + w - 18
        arrow_y = y + h//2
        self.canvas.create_polygon(arrow_x-5, arrow_y-4, arrow_x+5, arrow_y-4, arrow_x, arrow_y+4, fill="black", tags=("element", f"elem_{elem.elem_id}"))
        self._render_text_on_canvas(elem, x+4, y, w-22, h, elem.display_label, fg, font, anchor="w")

    def _draw_spinbox(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        arrow_x = x + w - 16
        arrow_y = y + h//2
        self.canvas.create_polygon(arrow_x-6, arrow_y-2, arrow_x+6, arrow_y-2, arrow_x, arrow_y-8, fill="black", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_polygon(arrow_x-6, arrow_y+2, arrow_x+6, arrow_y+2, arrow_x, arrow_y+8, fill="black", tags=("element", f"elem_{elem.elem_id}"))
        self._render_text_on_canvas(elem, x+4, y, w-20, h, elem.display_label, fg, font, anchor="w")

    def _draw_listbox(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        for i in range(3):
            line_y = y + 12 + i*20
            if line_y < y + h - 5:
                self.canvas.create_line(x+5, line_y, x+w-5, line_y, fill="gray", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_text(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        for i in range(max(1, h//22)):
            line_y = y + 15 + i*22
            if line_y < y + h - 5:
                self.canvas.create_line(x+5, line_y, x+w-5, line_y, fill="gray", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_canvas(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        self.canvas.create_rectangle(x+10, y+10, x+w-10, y+h-10, outline="gray", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+15, y+15, x+w-15, y+h-15, fill="gray", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_progressbar(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        value = elem.props.get("value", 40)
        max_val = elem.props.get("maximum", 100)
        orient = elem.props.get("orient", "horizontal")
        frac = min(1.0, max(0, value/max_val))
        if orient == "vertical":
            bar_h = int((h-4) * frac)
            self.canvas.create_rectangle(x+2, y+h-2-bar_h, x+w-2, y+h-2, fill="blue", outline="", tags=("element", f"elem_{elem.elem_id}"))
        else:
            bar_w = int((w-4) * frac)
            self.canvas.create_rectangle(x+2, y+2, x+2+bar_w, y+h-2, fill="blue", outline="", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_scrollbar(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        slider_h = h//3
        slider_y = y + (h - slider_h)//2
        self.canvas.create_rectangle(x+2, slider_y, x+w-2, slider_y+slider_h, fill="gray", outline="darkgray", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_frame(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        relief = elem.props.get("relief", "groove")
        if relief == "groove": self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        elif relief == "raised": self._draw_raised_rect(elem, x, y, w, h, bg, outline, outline_w)
        elif relief == "sunken": self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        else: self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)

    def _draw_labelframe(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        text = elem.props.get("text", "LabelFrame")
        self.canvas.create_rectangle(x+10, y-6, x+min(w-10, 10 + len(text)*8), y+6, fill=bg, outline="", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_text(x+14, y, text=text, fill=fg, font=font, anchor="w", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_notebook(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self.canvas.create_rectangle(x, y+26, x+w, y+h, fill=bg, outline="gray", tags=("element", f"elem_{elem.elem_id}"))
        tabs = elem.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
        active = int(elem.props.get("active_tab", 0) or 0)
        active = max(0, min(active, len(tabs) - 1))
        tab_width = max(58, min(120, int((w - 10) / max(1, min(len(tabs), 4)))))
        tab_x = x + 5
        for i, title in enumerate(tabs):
            if tab_x >= x + w - 4:
                break
            tw = min(tab_width, x + w - 4 - tab_x)
            fill = "#ffffff" if i == active else "#e0e0e0"
            text_fill = "#333333" if i == active else "#666666"
            self.canvas.create_rectangle(tab_x, y+4, tab_x+tw, y+26, fill=fill, outline="gray", tags=("element", f"elem_{elem.elem_id}"))
            self.canvas.create_text(tab_x+tw/2, y+15, text=str(title), fill=text_fill, font=font, tags=("element", f"elem_{elem.elem_id}"))
            tab_x += tw + 3

    def _draw_panedwindow(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        orient = elem.props.get("orient", "horizontal")
        if orient == "vertical":
            sash_y = y + h//2
            self.canvas.create_line(x+10, sash_y, x+w-10, sash_y, fill="gray", width=2, tags=("element", f"elem_{elem.elem_id}"))
        else:
            sash_x = x + w//2
            self.canvas.create_line(sash_x, y+10, sash_x, y+h-10, fill="gray", width=2, tags=("element", f"elem_{elem.elem_id}"))

    def _draw_separator(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        orient = elem.props.get("orient", "horizontal")
        if orient == "vertical":
            self.canvas.create_line(x + w//2, y, x + w//2, y + h, fill="gray", width=2, tags=("element", f"elem_{elem.elem_id}"))
        else:
            self.canvas.create_line(x, y + h//2, x + w, y + h//2, fill="gray", width=2, tags=("element", f"elem_{elem.elem_id}"))

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
        self.canvas.create_rectangle(x, y, x+w, y+row_h, fill="#E0E0E0", outline="gray", tags=("element", f"elem_{elem.elem_id}"))
        for i, col in enumerate(columns):
            self.canvas.create_line(x + (i+1)*col_w, y, x + (i+1)*col_w, y+row_h, fill="gray", tags=("element", f"elem_{elem.elem_id}"))
            self.canvas.create_text(x + i*col_w + col_w/2, y + row_h/2, text=col, fill=fg, font=font, tags=("element", f"elem_{elem.elem_id}"))
        rows = min(5, max(0, int(h - row_h) // 20))
        for r in range(rows):
            ry = y + row_h + r*20
            self.canvas.create_rectangle(x, ry, x+w, ry+20, outline="gray", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_fallback(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg, font)

    def _draw_flat_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        elem.rect_id = self.canvas.create_rectangle(
            x, y, x+w, y+h, fill=fill, outline=outline, width=outline_w,
            tags=("element", f"elem_{elem.elem_id}")
        )

    def _draw_sunken_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline=outline, width=outline_w, tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+1, y+1, x+w-2, y+1, fill="gray", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+1, y+1, x+1, y+h-2, fill="gray", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+w-2, y+2, x+w-2, y+h-2, fill="white", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+2, y+h-2, x+w-2, y+h-2, fill="white", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_raised_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline=outline, width=outline_w, tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+1, y+1, x+w-2, y+1, fill="white", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+1, y+1, x+1, y+h-2, fill="white", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+w-2, y+2, x+w-2, y+h-2, fill="gray", tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_line(x+2, y+h-2, x+w-2, y+h-2, fill="gray", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_groove_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline=outline, width=outline_w, tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_rectangle(x+2, y+2, x+w-2, y+h-2, outline="gray", width=1, tags=("element", f"elem_{elem.elem_id}"))

    def _render_text_on_canvas(self, elem, x, y, w, h, text, color, font, anchor="center"):
        if anchor == "center":
            elem.text_id = self.canvas.create_text(
                x + w//2, y + h//2, text=text, fill=color, font=font, tags=("element", f"elem_{elem.elem_id}")
            )
        elif anchor == "w":
            elem.text_id = self.canvas.create_text(
                x+2, y + h//2, text=text, fill=color, font=font, anchor="w", tags=("element", f"elem_{elem.elem_id}")
            )

    def erase_element(self, elem: DesignElement) -> None:
        self.canvas.delete(f"elem_{elem.elem_id}")
        for hid in elem.handle_ids.values():
            self.canvas.delete(hid)
        elem.rect_id = 0
        elem.text_id = 0
        elem.handle_ids = {}

    def redraw_element(self, elem: DesignElement) -> None:
        self.erase_element(elem)
        self.draw_element(elem)

    def snap_to_grid(self, x: int, y: int) -> Tuple[int, int]:
        return int(round(x / GRID_SIZE) * GRID_SIZE), int(round(y / GRID_SIZE) * GRID_SIZE)

# ─── GUIBuilderApp ──────────────────────────────────────────────────────────

class GUIBuilderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.window_title = "My Application"
        self.current_file_path: Optional[str] = None
        self._is_modified = False
        self.full_code: Optional[str] = None
        self._current_code: str = ""

        self._update_window_title_display()
        self.root.geometry("1400x800")
        self.root.minsize(1000, 600)

        try:
            self.root.state('zoomed')
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)
            except tk.TclError:
                pass

        self.CANVAS_W = 800
        self.CANVAS_H = 600
        self.CANVAS_BG = "#FAFAFA"
        
        self.canvas_imports = "import tkinter as tk\nfrom tkinter import ttk"

        self.elements: List[DesignElement] = []
        self.selected_elems: List[DesignElement] = []
        self.clipboard: List[DesignElement] = []
        
        self.next_id = 1
        self.reusable_ids = set()
        
        self.undo_stack = []
        self.redo_stack = []
        
        self.pending_type: Optional[str] = None
        self.code_visible = False
        self.prop_context_var = tk.StringVar(value="Container: None")
        self._just_resized = False

        self.drag_mode = "none"
        self.drag_elem = None
        self.mouse_down_pos = None
        self.elem_origs = {}
        self.active_handle = None
        self.selection_box_id = None

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

        # Ctrl+A for canvas selection (on canvas itself)
        self.canvas.bind("<Control-a>", self._select_all)

        self._update_code()
        self._update_element_count()
        self._update_status("Ready — pick a tool and click canvas, or double-click elements to edit code.")
        self._show_properties(None)
        
        self._save_state()

    def _update_window_title_display(self):
        filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled.tvd"
        dirty_marker = "*" if self._is_modified else ""
        self.root.title(f"Tkinter Visual Designer - [{filename}{dirty_marker}]")

    def _build_ui(self):
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_toolbar()

        self.v_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.v_paned.grid(row=1, column=0, sticky="nsew")

        self.main_paned = ttk.PanedWindow(self.v_paned, orient=tk.HORIZONTAL)
        self.v_paned.add(self.main_paned, weight=3)

        self.toolbox_frame = ttk.Frame(self.main_paned, width=220)
        self.toolbox_frame.pack_propagate(False)
        self.main_paned.add(self.toolbox_frame, weight=0)
        self._build_toolbox()

        center_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(center_frame, weight=1)
        
        self.canvas_scroll_y = ttk.Scrollbar(center_frame, orient=tk.VERTICAL)
        self.canvas_scroll_x = ttk.Scrollbar(center_frame, orient=tk.HORIZONTAL)
        self.canvas = tk.Canvas(
            center_frame, bg=self.CANVAS_BG, width=self.CANVAS_W, height=self.CANVAS_H,
            yscrollcommand=self.canvas_scroll_y.set, xscrollcommand=self.canvas_scroll_x.set,
            takefocus=1          # <-- ADD THIS
        )
        self.canvas_scroll_y.config(command=self.canvas.yview)
        self.canvas_scroll_x.config(command=self.canvas.xview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas_scroll_y.grid(row=0, column=1, sticky="ns")
        self.canvas_scroll_x.grid(row=1, column=0, sticky="ew")
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)

        self.canvas.config(scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H))
        self.renderer = CanvasRenderer(self.canvas)

        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)

        # # Ensure Ctrl+A works on canvas
        # self.canvas.bind("<Control-a>", self._select_all)   # already present, keep it
        
        self.prop_frame = ttk.Frame(self.main_paned, width=300)
        self.prop_frame.pack_propagate(False)
        self.main_paned.add(self.prop_frame, weight=0)
        self._build_property_inspector()

        self.code_frame = ttk.Frame(self.v_paned)
        self.code_frame.grid_rowconfigure(0, weight=0)
        self.code_frame.grid_rowconfigure(1, weight=1)
        self.code_frame.grid_columnconfigure(0, weight=1)

        code_header = ttk.Frame(self.code_frame)
        code_header.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ttk.Label(code_header, text="LIVE CODE", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.code_text = scrolledtext.ScrolledText(
            self.code_frame, font=("Courier New", 9), bg="#1E1E1E", fg="#D4D4D4", wrap=tk.NONE
        )
        self.code_text.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.code_text.config(state=tk.DISABLED)

        self.status_var = tk.StringVar()
        self.count_var = tk.StringVar()
        status_bar = ttk.Frame(self.root)
        status_bar.grid(row=2, column=0, sticky="ew")
        ttk.Label(status_bar, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(status_bar, textvariable=self.count_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.RIGHT)

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        
        ttk.Button(toolbar, text="📄 New Design", command=self._new_design).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Load Design", command=self._load_design).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save Design", command=self._save_design).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        ttk.Button(toolbar, text="↶ Undo", command=self._undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↷ Redo", command=self._redo).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        ttk.Button(toolbar, text="🗑️ Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🧹 Clear Canvas", command=self._clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)

        ttk.Button(toolbar, text="📋 Copy Code", command=self._copy_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▶ Run Preview", command=self._run_preview).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        ttk.Button(toolbar, text="👁️ Toggle Code", command=self._toggle_code_view).pack(side=tk.LEFT, padx=2)

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
        ttk.Label(self.toolbox_frame, text="TOOLBOX", font=("Segoe UI", 10, "bold")).pack(pady=(5, 10))

        canvas_toolbox = tk.Canvas(self.toolbox_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.toolbox_frame, orient=tk.VERTICAL, command=canvas_toolbox.yview)
        scrollable_frame = ttk.Frame(canvas_toolbox)
        scrollable_frame.bind("<Configure>", lambda e: canvas_toolbox.configure(scrollregion=canvas_toolbox.bbox("all")))
        canvas_toolbox.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_toolbox.configure(yscrollcommand=scrollbar.set)

        canvas_toolbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("ToolboxItem.TFrame", background="#F8F9FA", relief="raised", borderwidth=1)
        style.configure("ToolboxHover.TFrame", background="#E9ECEF", relief="raised", borderwidth=1)

        categories = {}
        for name, spec in ELEMENT_TYPES.items():
            cat = spec.get("category", "Other")
            categories.setdefault(cat, []).append((name, spec))

        for cat in sorted(categories.keys()):
            ttk.Label(scrollable_frame, text=cat, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, padx=5, pady=(10,2))
            for name, spec in sorted(categories[cat], key=lambda x: x[0]):
                display_str = spec["display"]
                parts = display_str.split(" ", 1)
                icon = parts[0] if len(parts) > 1 else ""
                elem_name = parts[1] if len(parts) > 1 else display_str

                item_frame = ttk.Frame(scrollable_frame, style="ToolboxItem.TFrame", cursor="hand2")
                item_frame.pack(fill=tk.X, padx=5, pady=2)
                
                lbl_icon = ttk.Label(item_frame, text=icon, anchor="w")
                lbl_icon.pack(side=tk.LEFT, padx=6, pady=4)
                
                lbl_name = ttk.Label(item_frame, text=elem_name, anchor="e")
                lbl_name.pack(side=tk.RIGHT, padx=6, pady=4)

                def on_click(e, t=name):
                    self._tool_selected(t)
                def on_enter(e, f=item_frame):
                    f.configure(style="ToolboxHover.TFrame")
                def on_leave(e, f=item_frame):
                    f.configure(style="ToolboxItem.TFrame")

                for widget in (item_frame, lbl_icon, lbl_name):
                    widget.bind("<Button-1>", on_click)
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)

                setattr(self, f"_tool_btn_{name}", item_frame)

        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

    def _highlight_active_tool(self, active_name: str):
        for name in ELEMENT_TYPES:
            frame = getattr(self, f"_tool_btn_{name}", None)
            if frame:
                style_name = "ToolboxActive.TFrame" if name == active_name else "ToolboxItem.TFrame"
                frame.configure(style=style_name)
        ttk.Style().configure("ToolboxActive.TFrame", background="#FF6B35", relief="sunken")

    def _reset_tool_colors(self):
        for name in ELEMENT_TYPES:
            frame = getattr(self, f"_tool_btn_{name}", None)
            if frame:
                frame.configure(style="ToolboxItem.TFrame")

    def _build_property_inspector(self):
        ttk.Label(self.prop_frame, text="PROPERTIES", font=("Segoe UI", 10, "bold")).pack(pady=(5, 6))
        self.prop_title_label = ttk.Label(self.prop_frame, text="No element selected.", wraplength=255)
        self.prop_title_label.pack(anchor=tk.W, padx=6, pady=(0, 2), fill=tk.X)
        self.prop_context_var = tk.StringVar(value="Container: None")
        ttk.Label(self.prop_frame, textvariable=self.prop_context_var, wraplength=255, foreground="#555555").pack(anchor=tk.W, padx=6, pady=(0, 5), fill=tk.X)

        prop_canvas = tk.Canvas(self.prop_frame, highlightthickness=0, width=270)
        prop_scroll = ttk.Scrollbar(self.prop_frame, orient=tk.VERTICAL, command=prop_canvas.yview)
        self.prop_scrollable = ttk.Frame(prop_canvas)
        self.prop_scrollable.bind("<Configure>", lambda e: prop_canvas.configure(scrollregion=prop_canvas.bbox("all")))
        prop_window = prop_canvas.create_window((0, 0), window=self.prop_scrollable, anchor="nw", width=270)
        prop_canvas.bind("<Configure>", lambda e: prop_canvas.itemconfigure(prop_window, width=max(230, e.width - 2)))
        prop_canvas.configure(yscrollcommand=prop_scroll.set)

        prop_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        prop_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.prop_rows = []
        for i in range(20):
            frame = ttk.Frame(self.prop_scrollable)
            lbl = ttk.Label(frame, text="", width=12, anchor=tk.W)
            lbl.pack(side=tk.LEFT, padx=(2, 4))
            control_frame = ttk.Frame(frame)
            control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.prop_rows.append({
                "frame": frame, "label": lbl, "control_frame": control_frame,
                "widget": None, "visible": False,
            })

    def _move_with_keys(self, event):
        if not self.selected_elems: return
        
        if event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
            return
            
        dx, dy = 0, 0
        if event.keysym == "Up": dy = -1
        elif event.keysym == "Down": dy = 1
        elif event.keysym == "Left": dx = -1
        elif event.keysym == "Right": dx = 1
        
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
        # For moved elements, we update their place lines in the full code.
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
        self.canvas_imports = data.get("canvas_imports", "import tkinter as tk\nfrom tkinter import ttk")
        self.full_code = data.get("full_code")
        
        self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H, bg=self.CANVAS_BG, scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H))
        
        for elem_data in data.get("elements", []):
            elem = DesignElement.from_dict(elem_data)
            self.elements.append(elem)
            
        self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
        self._redraw_all_elements()
        self._reorder_elements()
        self._show_properties(None)
        self._update_code()
        self._update_element_count()

    def _undo(self, event=None):
        if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
            return 
            
        if len(self.undo_stack) > 1:
            curr = self.undo_stack.pop()
            self.redo_stack.append(curr)
            prev = self.undo_stack[-1]
            self._load_state(prev)
            self._update_status("Undo successful.")

    def _redo(self, event=None):
        if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
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
            parent = next((e for e in self.elements if e.elem_id == current.parent_id), None)
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
        depths = {e.elem_id: 0 for e in self.elements}
        changed = True
        while changed:
            changed = False
            for e in self.elements:
                if e.parent_id is not None and e.parent_id in depths:
                    if depths[e.elem_id] <= depths[e.parent_id]:
                        depths[e.elem_id] = depths[e.parent_id] + 1
                        changed = True

        sorted_elems = sorted(visible, key=lambda e: depths.get(e.elem_id, 0))
        for e in sorted_elems:
            self.canvas.tag_raise(f"elem_{e.elem_id}")
        self.canvas.tag_raise("handle")

    def _tool_selected(self, tool_name: str):
        self.pending_type = tool_name
        self._highlight_active_tool(tool_name)
        self._update_status(f"{ELEMENT_TYPES[tool_name]['display']} selected — click canvas to place it.")

    def _notebook_tab_at(self, elem: DesignElement, x: float, y: float) -> Optional[int]:
        if elem.elem_type != "Notebook":
            return None
        if not (elem.x <= x <= elem.x + elem.canvas_w and elem.y <= y <= elem.y + 26):
            return None
        tabs = elem.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
        tab_width = max(58, min(120, int((elem.canvas_w - 10) / max(1, min(len(tabs), 4)))))
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
            if elem.elem_type not in ("Frame", "LabelFrame", "PanedWindow", "Notebook"):
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
                p = next((e for e in self.elements if e.elem_id == cur.parent_id), None)
                if not p:
                    break
                depth += 1
                cur = p
            containers.append((depth, -area, elem))
        if not containers:
            return None
        containers.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return containers[0][2]

    def _set_notebook_active_tab(self, notebook: DesignElement, tab_index: int):
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
            self._update_status(f"Notebook ID {notebook.elem_id}: {tabs[tab_index]} selected.")

    def _on_canvas_click(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        ctrl_held = (event.state & 0x0004) != 0 or (event.state & 0x0001) != 0

        if self.pending_type:
            tool = self.pending_type
            self.pending_type = None
            self._reset_tool_colors()
            self._add_element(tool, x, y)
            return

        if getattr(self, "_just_resized", False):
            self._just_resized = False
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
        else:
            self._select_element(None, clear=not ctrl_held)
            self._reset_drag_state()
            self.drag_mode = "select_box"
            self.mouse_down_pos = (x, y)
            self.selection_box_id = self.canvas.create_rectangle(x, y, x, y, dash=(4, 4), outline="blue")
        
        self.canvas.focus_set()

    def _find_element_at(self, x: int, y: int) -> Optional[DesignElement]:
        for elem in reversed(self._visible_elements()):
            if elem.contains_point(x, y): return elem
        return None

    def _on_canvas_drag(self, event):
        if not self.mouse_down_pos:
            return
        mx, my = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        cum_dx, cum_dy = mx - self.mouse_down_pos[0], my - self.mouse_down_pos[1]

        if self.drag_mode == "move":
            moved_ids = set()
            for elem in self.selected_elems:
                if elem.elem_id in moved_ids or elem.elem_id not in self.elem_origs:
                    continue
                ox, oy, _, _ = self.elem_origs[elem.elem_id]
                new_x, new_y = self.renderer.snap_to_grid(ox + cum_dx, oy + cum_dy)
                dx, dy = new_x - ox, new_y - oy
                elem.x = max(0, min(new_x, self.CANVAS_W - elem.canvas_w))
                elem.y = max(0, min(new_y, self.CANVAS_H - elem.canvas_h))
                self.renderer.redraw_element(elem)
                moved_ids.add(elem.elem_id)
                if elem.elem_type in ("Frame", "LabelFrame", "PanedWindow", "Notebook"):
                    for child in self.elements:
                        if child.parent_id == elem.elem_id and child.elem_id not in moved_ids:
                            cox, coy, _, _ = self.elem_origs.get(child.elem_id, (child.x, child.y, child.canvas_w, child.canvas_h))
                            child.x = max(0, min(cox + dx, self.CANVAS_W - child.canvas_w))
                            child.y = max(0, min(coy + dy, self.CANVAS_H - child.canvas_h))
                            self.renderer.redraw_element(child)
                            moved_ids.add(child.elem_id)
            self._update_code_for_moved_elements()
            self._update_code()

        elif self.drag_mode == "resize":
            for elem in self.selected_elems:
                if elem.elem_id in self.elem_origs:
                    ox, oy, ow, oh = self.elem_origs[elem.elem_id]
                    nx, ny, nw, nh = self._compute_resize(self.active_handle, ox, oy, ow, oh, cum_dx, cum_dy)
                    elem.x, elem.y, elem.canvas_w, elem.canvas_h = nx, ny, nw, nh
                    self.renderer.redraw_element(elem)
            self._update_code_for_moved_elements()
            self._update_code()

        elif self.drag_mode == "select_box" and self.selection_box_id:
            self.canvas.coords(self.selection_box_id, self.mouse_down_pos[0], self.mouse_down_pos[1], mx, my)

    def _on_canvas_release(self, event):
        if self.drag_mode == "select_box":
            mx, my = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            x1, y1 = min(self.mouse_down_pos[0], mx), min(self.mouse_down_pos[1], my)
            x2, y2 = max(self.mouse_down_pos[0], mx), max(self.mouse_down_pos[1], my)
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
                    if elem.elem_type in ("Frame", "LabelFrame", "PanedWindow", "Notebook"):
                        continue
                    cx = elem.x + elem.canvas_w / 2
                    cy = elem.y + elem.canvas_h / 2
                    parent = self._container_at(cx, cy)
                    old_parent = elem.parent_id
                    elem.parent_id = parent.elem_id if parent else None
                    if parent and parent.elem_type == "Notebook":
                        elem.parent_tab = int(parent.props.get("active_tab", 0) or 0)
                    elif old_parent != elem.parent_id:
                        elem.parent_tab = None
                self._update_code_for_moved_elements()
                self._update_code()
            else:
                self._just_resized = True

            self._reorder_elements()
            self._save_state()

        self._reset_drag_state()

    def _on_canvas_double_click(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        elem = self._find_element_at(x, y)
        if elem:
            self._open_code_editor(elem)

    def _compute_resize(self, handle, ox, oy, ow, oh, cum_dx, cum_dy):
        nx, ny, nw, nh = ox, oy, ow, oh
        if "W" in handle: nw = max(MIN_W, ow - cum_dx); nx = ox + ow - nw
        if "E" in handle: nw = max(MIN_W, ow + cum_dx)
        if "N" in handle: nh = max(MIN_H, oh - cum_dy); ny = oy + oh - nh
        if "S" in handle: nh = max(MIN_H, oh + cum_dy)
        nx = max(0, min(nx, self.CANVAS_W - nw))
        ny = max(0, min(ny, self.CANVAS_H - nh))
        nw = min(nw, self.CANVAS_W - nx)
        nh = min(nh, self.CANVAS_H - ny)
        return nx, ny, nw, nh

    def _reset_drag_state(self):
        self.drag_mode, self.drag_elem, self.mouse_down_pos, self.elem_origs, self.active_handle = "none", None, None, {}, None

    def _add_element(self, elem_type: str, x: int, y: int):
        self._invalidate_full_code()
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
        elem = DesignElement(elem_type=elem_type, x=sx, y=sy, props=props, elem_id=new_id, canvas_w=w, canvas_h=h)
        parent = self._container_at(sx + w / 2, sy + h / 2)
        if parent is not None:
            elem.parent_id = parent.elem_id
            if parent.elem_type == "Notebook":
                elem.parent_tab = int(parent.props.get("active_tab", 0) or 0)
        
        event_name = DEFAULT_EVENT_MAP.get(elem_type)
        if event_name:
            code = f'"""\n'
            code += f'Event handler for {elem_type} (ID: {elem.elem_id}).\n'
            code += f'Triggered by: {event_name}\n'
            code += f'Access widget instance via: self._elem_{elem.elem_id}\n'
            code += f'"""\n'
            code += f'pass'
            elem.handler_code = code

        self.elements.append(elem)
        if self._is_element_visible(elem):
            self.renderer.draw_element(elem)
            self._select_element(elem, clear=True)
        else:
            self._select_element(None, clear=True)
        self._update_code()
        self._update_element_count()
        self._update_status(f"Added {ELEMENT_TYPES[elem_type]['display']}.")
        self._save_state()

    def _select_element(self, elem: Optional[DesignElement], clear: bool = True):
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
        self.prop_title_label.config(text=f"[{len(self.selected_elems)} elements selected - Common Properties]")

        common_fields = [
            ("font", "Font", "font"),
            ("fg", "Foreground", "color"),
            ("bg", "Background", "color"),
            ("width", "Width", "entry"),
            ("height", "Height", "entry"),
        ]

        row_index = 0
        for field_key, label, widget_type in common_fields:
            if row_index >= len(self.prop_rows): break
            row = self.prop_rows[row_index]
            row["label"].config(text=label + " (All):")
            row["field_key"] = field_key
            
            for child in row["control_frame"].winfo_children(): child.destroy()

            var = tk.StringVar(value="")
            
            if widget_type in ("entry", "color"):
                var.trace_add("write", lambda *args, r=row: self._on_live_multi_prop_change(r))
                row["var"] = var
                
                if widget_type == "entry": ttk.Entry(row["control_frame"], textvariable=var).pack(fill=tk.X)
                elif widget_type == "color":
                    frame = ttk.Frame(row["control_frame"])
                    frame.pack(fill=tk.X)
                    ttk.Entry(frame, textvariable=var, width=10).pack(side=tk.LEFT, fill=tk.X, expand=True)
                    ttk.Button(frame, text="Pick", command=lambda v=var: self._pick_color(v)).pack(side=tk.RIGHT)

            elif widget_type == "font":
                frame = ttk.Frame(row["control_frame"])
                frame.pack(fill=tk.X)
                family_var = tk.StringVar(value="Segoe UI")
                size_var = tk.StringVar(value="9")

                def update_font(*args, target_var=var, f_var=family_var, s_var=size_var):
                    target_var.set(f"('{f_var.get()}', {s_var.get()})")

                family_var.trace_add("write", update_font)
                size_var.trace_add("write", update_font)
                
                try: families = sorted(list(tkfont.families()))
                except: families = ["Arial", "Segoe UI"]

                ttk.Combobox(frame, textvariable=family_var, values=families, width=12, state="readonly").pack(side=tk.LEFT, padx=(0, 2))
                ttk.Combobox(frame, textvariable=size_var, values=[8,9,10,11,12,14,16,18,20,24], width=3).pack(side=tk.LEFT)
                
                var.trace_add("write", lambda *args, r=row: self._on_live_multi_prop_change(r))
                row["var"] = var

            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            row_index += 1

    def _on_live_multi_prop_change(self, row):
        if len(self.selected_elems) <= 1 or not row.get("visible"): return
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None: return
        value = var.get()
        if not value: return

        for elem in self.selected_elems:
            if field_key in elem.props or field_key in ("width", "height"):
                if field_key == "width":
                    try: elem.canvas_w = int(value)
                    except: pass
                elif field_key == "height":
                    try: elem.canvas_h = int(value)
                    except: pass
                elif field_key == "font":
                    try:
                        parsed = ast.literal_eval(value)
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
        if not self.selected_elems: return
        self.clipboard = [copy.deepcopy(e) for e in self.selected_elems]
        self._update_status(f"Copied {len(self.clipboard)} element(s) to clipboard.")

    def _paste_elements(self, event=None):
        if not self.clipboard: return
        self._invalidate_full_code()
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
            if self._is_element_visible(new_elem):
                self.renderer.draw_element(new_elem)
            pasted.append(new_elem)
            
        for e in pasted:
            if self._is_element_visible(e):
                self._select_element(e, clear=False)
            
        self._update_code()
        self._update_element_count()
        self._update_status(f"Pasted {len(pasted)} element(s).")
        self._save_state()

    def _delete_selected(self, event=None):
        if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry", "TEntry", "Text"):
            return
            
        if not self.selected_elems: return
        
        if not messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected element(s)?\nNote: Deleting a Container deletes all enclosed children elements."): 
            return
            
        to_delete = list(self.selected_elems)
        
        for elem in self.selected_elems:
            if elem.elem_type in ("Frame", "LabelFrame", "PanedWindow", "Notebook"):
                for child in self.elements:
                    if child.parent_id == elem.elem_id and child not in to_delete:
                        to_delete.append(child)
        
        for elem in to_delete:
            self.renderer.erase_element(elem)
            if elem in self.elements: 
                self.elements.remove(elem)
                self.reusable_ids.add(elem.elem_id)
                
        self.selected_elems.clear()
        self._invalidate_full_code()
        self._reset_drag_state()
        self._show_properties(None)
        self._update_code()
        self._update_element_count()
        self._update_status("Element(s) deleted.")
        self._save_state()

    def _clear_all(self):
        if not self.elements: return
        if not messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire canvas? All unsaved progress will be lost."): 
            return
            
        self._invalidate_full_code()
        for elem in self.elements: self.renderer.erase_element(elem)
        self.elements.clear()
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

    def _show_properties(self, elem: Optional[DesignElement]):
        for row in self.prop_rows:
            row["frame"].pack_forget()
            row["visible"] = False

        if elem is None:
            self.prop_title_label.config(text="Canvas Settings")
            self.prop_context_var.set("Container: None")
            self._show_canvas_properties()
            return

        spec = ELEMENT_TYPES[elem.elem_type]
        self.prop_title_label.config(text=f"{spec['display']} [id={elem.elem_id}]")
        self.prop_context_var.set(self._parent_description(elem))
        fields = PROPERTY_FIELDS.get(elem.elem_type, [])
        row_index = 0

        for fielddef in fields:
            if row_index >= len(self.prop_rows):
                break
            field_key, label, widget_type = fielddef[0], fielddef[1], fielddef[2]
            options = fielddef[3] if len(fielddef) > 3 else None
            row = self.prop_rows[row_index]
            row["label"].config(text=label + ":")
            row["field_key"] = field_key
            for child in row["control_frame"].winfo_children():
                child.destroy()

            if field_key == "canvas_w":
                value = elem.canvas_w
            elif field_key == "canvas_h":
                value = elem.canvas_h
            elif field_key == "active_tab" and elem.elem_type == "Notebook":
                value = int(elem.props.get("active_tab", 0) or 0) + 1
                options = [str(i + 1) for i in range(max(1, len(elem.props.get("tabs", []))))]
            else:
                value = elem.props.get(field_key, "")

            if field_key == "tabs" and elem.elem_type == "Notebook":
                value = ", ".join(str(v) for v in (elem.props.get("tabs") or ["Tab 1"]))

            display_val = "" if value is None else str(value)
            var = tk.StringVar(value=display_val)

            if elem.elem_type == "Table" and field_key == "file":
                var.trace_add("write", lambda *args, r=row: self._on_live_prop_change(r))
                row["var"] = var
                file_frame = ttk.Frame(row["control_frame"])
                file_frame.pack(fill=tk.X)
                ttk.Entry(file_frame, textvariable=var, width=14).pack(side=tk.LEFT, fill=tk.X, expand=True)
                ttk.Button(file_frame, text="…", width=3, command=lambda v=var: self._browse_table_file(v)).pack(side=tk.LEFT, padx=(3, 0))
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                row_index += 1
                continue

            if field_key == "tabs" and elem.elem_type == "Notebook":
                var.trace_add("write", lambda *args, r=row: self._on_live_prop_change(r))
                row["var"] = var
                tabs_frame = ttk.Frame(row["control_frame"])
                tabs_frame.pack(fill=tk.X)
                ttk.Entry(tabs_frame, textvariable=var, width=18).pack(side=tk.LEFT, fill=tk.X, expand=True)
                ttk.Button(tabs_frame, text="+", width=3, command=lambda e=elem: self._add_notebook_tab(e)).pack(side=tk.LEFT, padx=(3, 0))
                ttk.Button(tabs_frame, text="−", width=3, command=lambda e=elem: self._remove_notebook_tab(e)).pack(side=tk.LEFT, padx=(2, 0))
            elif widget_type in ("entry", "combobox", "color"):
                var.trace_add("write", lambda *args, r=row: self._on_live_prop_change(r))
                row["var"] = var
                if widget_type == "entry":
                    ttk.Entry(row["control_frame"], textvariable=var, width=20).pack(fill=tk.X)
                elif widget_type == "combobox":
                    ttk.Combobox(row["control_frame"], textvariable=var, values=options or [], width=18, state="readonly").pack(fill=tk.X)
                else:
                    cf = ttk.Frame(row["control_frame"])
                    cf.pack(fill=tk.X)
                    ttk.Entry(cf, textvariable=var, width=12).pack(side=tk.LEFT, fill=tk.X, expand=True)
                    ttk.Button(cf, text="Pick", width=5, command=lambda v=var: self._pick_color(v)).pack(side=tk.RIGHT, padx=(3, 0))
            elif widget_type == "text":
                text_w = tk.Text(row["control_frame"], height=4, width=22, font=("Segoe UI", 9), wrap=tk.WORD)
                text_w.pack(fill=tk.X)
                text_w.insert("1.0", display_val)
                text_w.bind("<KeyRelease>", lambda event, target_var=var, tw=text_w: target_var.set(tw.get("1.0", "end-1c")))
                var.trace_add("write", lambda *args, r=row: self._on_live_prop_change(r))
                row["var"] = var
            elif widget_type == "font":
                frame = ttk.Frame(row["control_frame"])
                frame.pack(fill=tk.X)
                family_var = tk.StringVar()
                size_var = tk.StringVar()
                if isinstance(value, (tuple, list)):
                    f_family = str(value[0]) if value else "Segoe UI"
                    f_size = str(value[1]) if len(value) > 1 else "9"
                else:
                    try:
                        parsed = ast.literal_eval(str(value))
                        f_family = str(parsed[0]) if isinstance(parsed, (tuple, list)) and parsed else "Segoe UI"
                        f_size = str(parsed[1]) if isinstance(parsed, (tuple, list)) and len(parsed) > 1 else "9"
                    except Exception:
                        f_family, f_size = "Segoe UI", "9"
                family_var.set(f_family)
                size_var.set(f_size)
                def update_font(*args, target_var=var, f_var=family_var, s_var=size_var):
                    target_var.set(f"('{f_var.get()}', {s_var.get()})")
                family_var.trace_add("write", update_font)
                size_var.trace_add("write", update_font)
                try:
                    families = sorted(list(tkfont.families()))
                except Exception:
                    families = ["Arial", "Segoe UI"]
                ttk.Combobox(frame, textvariable=family_var, values=families, width=11, state="readonly").pack(side=tk.LEFT, padx=(0, 2))
                ttk.Combobox(frame, textvariable=size_var, values=[8,9,10,11,12,14,16,18,20,24,28,36,48], width=3).pack(side=tk.LEFT)
                var.trace_add("write", lambda *args, r=row: self._on_live_prop_change(r))
                row["var"] = var
            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            row_index += 1

    def _browse_table_file(self, var: tk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv"), ("All Files", "*.*")]
        )
        if path:
            var.set(path)

    def _parent_description(self, elem: DesignElement) -> str:
        if elem.parent_id is None:
            return "Container: None (root)"
        parent = next((e for e in self.elements if e.elem_id == elem.parent_id), None)
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
        for child in self.elements:
            if child.parent_id == elem.elem_id and child.parent_tab is not None and child.parent_tab >= len(tabs):
                child.parent_tab = len(tabs) - 1
        elem.props["active_tab"] = min(int(elem.props.get("active_tab", 0) or 0), len(tabs) - 1)
        self._invalidate_full_code()
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._update_code()
        self._save_state()

    def _show_canvas_properties(self):
        row_index = 0
        
        row = self.prop_rows[row_index]
        row["label"].config(text="Window Title:")
        for child in row["control_frame"].winfo_children(): child.destroy()
        self.title_var = tk.StringVar(value=self.window_title)
        title_entry = ttk.Entry(row["control_frame"], textvariable=self.title_var)
        title_entry.pack(fill=tk.X)
        title_entry.bind("<KeyRelease>", lambda e: self._window_title_changed())
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].config(text="Canvas Width:")
        for child in row["control_frame"].winfo_children(): child.destroy()
        var_w = tk.StringVar(value=str(self.CANVAS_W))
        ttk.Entry(row["control_frame"], textvariable=var_w).pack(fill=tk.X)
        var_w.trace_add("write", lambda *a: self._apply_canvas_size_from_props(var_w, None, None))
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].config(text="Canvas Height:")
        for child in row["control_frame"].winfo_children(): child.destroy()
        var_h = tk.StringVar(value=str(self.CANVAS_H))
        ttk.Entry(row["control_frame"], textvariable=var_h).pack(fill=tk.X)
        var_h.trace_add("write", lambda *a: self._apply_canvas_size_from_props(None, var_h, None))
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].config(text="Background:")
        for child in row["control_frame"].winfo_children(): child.destroy()
        var_bg = tk.StringVar(value=self.CANVAS_BG)
        frame_bg = ttk.Frame(row["control_frame"])
        frame_bg.pack(fill=tk.X)
        ttk.Entry(frame_bg, textvariable=var_bg, width=10).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame_bg, text="Pick", command=lambda v=var_bg: self._pick_color(v)).pack(side=tk.RIGHT)
        var_bg.trace_add("write", lambda *a: self._apply_canvas_size_from_props(None, None, var_bg))
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

    def _apply_canvas_size_from_props(self, var_w, var_h, var_bg):
        try:
            if var_w: self.CANVAS_W = int(var_w.get())
            if var_h: self.CANVAS_H = int(var_h.get())
            if var_bg: self.CANVAS_BG = var_bg.get()
            self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H, bg=self.CANVAS_BG, scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H))
            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
            self._update_code_for_canvas_change()
            self._update_code()
            if hasattr(self, "_prop_save_timer"):
                self.root.after_cancel(self._prop_save_timer)
            self._prop_save_timer = self.root.after(500, self._save_state)
        except ValueError:
            pass

    def _update_code_for_canvas_change(self):
        # Update the root.geometry and root.configure lines
        if self.full_code:
            # Replace root.geometry line
            self.full_code = re.sub(
                r'root\.geometry\([^\)]+\)',
                f'root.geometry("{self.CANVAS_W}x{self.CANVAS_H}")',
                self.full_code
            )
            # Replace root.configure bg
            self.full_code = re.sub(
                r'root\.configure\(bg=[^\)]+\)',
                f'root.configure(bg="{self.CANVAS_BG}")',
                self.full_code
            )
        else:
            self._invalidate_full_code()
            self._update_code()

    def _on_live_prop_change(self, row):
        if not self.selected_elems or len(self.selected_elems) > 1 or not row.get("visible"): return
        elem = self.selected_elems[0]
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None: return

        value = var.get()

        if field_key == "orient" and elem.elem_type in ("Scale", "Separator", "Progressbar", "Scrollbar"):
            if value == "vertical" and elem.canvas_w > elem.canvas_h:
                elem.canvas_w, elem.canvas_h = elem.canvas_h, elem.canvas_w
            elif value == "horizontal" and elem.canvas_h > elem.canvas_w:
                elem.canvas_w, elem.canvas_h = elem.canvas_h, elem.canvas_w

        if field_key == "canvas_w":
            try: elem.canvas_w = int(value)
            except ValueError: pass
        elif field_key == "canvas_h":
            try: elem.canvas_h = int(value)
            except ValueError: pass
        elif field_key == "font":
            try:
                parsed = ast.literal_eval(value)
                elem.props["font"] = parsed if isinstance(parsed, tuple) else value
            except:
                elem.props["font"] = value
        elif field_key in ("values", "items"):
            elem.props[field_key] = [v.strip() for v in value.split(",") if v.strip()]
        elif elem.elem_type == "Notebook" and field_key == "tabs":
            tabs = [v.strip() for v in value.split(",") if v.strip()] or ["Tab 1"]
            elem.props["tabs"] = tabs
            elem.props["active_tab"] = min(int(elem.props.get("active_tab", 0) or 0), len(tabs) - 1)
            for child in self.elements:
                if child.parent_id == elem.elem_id and child.parent_tab is not None and child.parent_tab >= len(tabs):
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
            try: elem.props[field_key] = int(value)
            except ValueError:
                try: elem.props[field_key] = float(value)
                except ValueError: elem.props[field_key] = value

        self.renderer.redraw_element(elem)
        # Update the code for this element only, without invalidating full_code
        self._update_code_for_element(elem)
        self._update_code()  # This updates the code_text widget
        
        if hasattr(self, "_prop_save_timer"):
            self.root.after_cancel(self._prop_save_timer)
        self._prop_save_timer = self.root.after(500, self._save_state)

    def _update_code_for_element(self, elem: DesignElement):
        """
        Update the widget creation and place lines for the given element
        in the current full_code, without touching other parts.
        """
        if not self.full_code:
            # If full_code is not yet generated, we need to generate it fully
            self._invalidate_full_code()
            self._update_code()
            return

        # Generate the new lines for this element
        widget_line, place_line, extra_lines = CodeGenerator.generate_element_lines(elem, self.elements)

        # We'll replace the lines that belong to this element.
        # First, find the widget creation line and place line.
        # The widget line starts with '        self._elem_{id} = '
        # The place line starts with '        self._elem_{id}.place('
        widget_pattern = rf'        self\._elem_{elem.elem_id} = .+'
        place_pattern = rf'        self\._elem_{elem.elem_id}\.place\(.+'

        # We'll also need to handle extra lines (e.g., Notebook tabs) – we'll replace them as a block.
        # For simplicity, we'll find the block of lines that are related to this element.
        # A safe approach: find the lines between the widget line and the place line (inclusive),
        # and replace them with the new lines.
        # We'll also include any extra lines that come after the place line? Actually the extra lines (like Listbox insert)
        # come before the place line in the generator? In generate, extra lines are placed after widget creation and before place.
        # But in the generated code, the order is: widget creation, extra lines (if any), then place line.
        # So we can find the range from the widget line to the place line (inclusive) and replace with the new block.

        lines = self.full_code.splitlines(keepends=True)
        new_lines = []
        widget_found = False
        place_found = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if not widget_found and re.match(widget_pattern, line):
                widget_found = True
                # We'll replace from this line until we hit the place line for this element.
                # We'll collect the block.
                block_lines = []
                block_start = i
                # Also include extra lines that might be between widget and place.
                # They are indented with 8 spaces (or 4? Actually they are indented with 8 because inside method).
                # We'll gather until we find the place line or we find a line that is not indented or starts with '        self._elem_' (next element).
                # We'll stop when we hit place line for this element or the next element creation.
                while i < len(lines):
                    current = lines[i]
                    # If we find the place line for this element, include it and break.
                    if re.match(place_pattern, current):
                        block_lines.append(current)
                        i += 1
                        place_found = True
                        break
                    # If we find the start of another element, break (should not happen inside a block)
                    if re.match(r'        self\._elem_\d+ = ', current) and current != lines[block_start]:
                        break
                    block_lines.append(current)
                    i += 1
                # Now we have the block to replace.
                # Generate the new block: widget_line, then extra_lines, then place_line.
                new_block = [widget_line]
                if extra_lines:
                    new_block.extend(extra_lines)
                new_block.append(place_line)
                # Add each line with a newline
                new_lines.extend([l + '\n' for l in new_block])
                # Continue after the block we just processed.
                # (i is already advanced past the block)
                continue
            else:
                new_lines.append(line)
                i += 1

        if not widget_found or not place_found:
            # If we couldn't find the lines, fall back to full regeneration
            self._invalidate_full_code()
            self._update_code()
        else:
            self.full_code = ''.join(new_lines)
            # Also update the in-memory current code
            self._current_code = self.full_code

    def _pick_color(self, var: tk.StringVar):
        color = colorchooser.askcolor(initialcolor=var.get() or "#ffffff", title="Select Color")
        if color[1]: var.set(color[1])

    def _update_code(self):
        if self.full_code is not None:
            code = self.full_code
        else:
            code = CodeGenerator.generate(
                self.elements, self.window_title, (self.CANVAS_W, self.CANVAS_H), 
                self.CANVAS_BG, self.canvas_imports
            )
            self.full_code = code
        self._current_code = code
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, code)
        self.code_text.config(state=tk.DISABLED)

    def _window_title_changed(self):
        if hasattr(self, "title_var"):
            self.window_title = self.title_var.get()
            # Update the title in full_code
            if self.full_code:
                # Replace root.title line
                self.full_code = re.sub(
                    r'root\.title\([^\)]+\)',
                    f'root.title({json.dumps(self.window_title)})',
                    self.full_code
                )
                self._current_code = self.full_code
                self.code_text.config(state=tk.NORMAL)
                self.code_text.delete("1.0", tk.END)
                self.code_text.insert(tk.END, self.full_code)
                self.code_text.config(state=tk.DISABLED)
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
                filetypes=[("Tkinter Visual Design", "*.tvd"), ("All Files", "*.*")]
            )
            if path:
                self._save_to_path(path)

    def _load_design(self):
        path = filedialog.askopenfilename(
            filetypes=[("Tkinter Visual Design", "*.tvd"), ("All Files", "*.*")]
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
                self._update_status(f"Loaded design from {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Load Error", str(e))

    def _new_design(self):
        if self._is_modified:
            if not messagebox.askyesno("Confirm New", "You have unsaved changes. Create new design anyway?"):
                return
        self.current_file_path = None
        self._is_modified = False
        self.elements.clear()
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
        code = self._current_code
        fd, temp_path = tempfile.mkstemp(suffix=".py")
        os.close(fd)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        try:
            subprocess.Popen([sys.executable, temp_path])
            self._update_status("Running Code Preview...")
        except Exception as e:
            messagebox.showerror("Run Preview Error", str(e))

    def _open_code_editor(self, elem: DesignElement):
        top = tk.Toplevel(self.root)
        top.title(f"Code Editor - {elem.elem_type} (ID: {elem.elem_id})")
        top.geometry("900x680")
        top.minsize(650, 450)

        editor_frame = ttk.Frame(top)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        text_widget = tk.Text(editor_frame, font=("Consolas", 10), bg="white", fg="black", wrap=tk.NONE, undo=True, padx=8, pady=6)
        y_scroll = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=text_widget.yview)
        x_scroll = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        text_widget.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        full_code = self._current_code
        text_widget.insert("1.0", full_code)

        method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
        target = text_widget.search(f"def {method_name}", "1.0", tk.END) or text_widget.search(f"self._elem_{elem.elem_id}", "1.0", tk.END)
        if target:
            target = text_widget.index(f"{target} linestart")
            text_widget.mark_set("insert", target)
            text_widget.see(target)
            text_widget.xview_moveto(0.0)
            text_widget.tag_add("highlight", target, f"{target} lineend")
            text_widget.tag_config("highlight", background="#FFF2CC", foreground="black")

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        def save_code():
            edited_code = text_widget.get("1.0", "end-1c")
            self.full_code = edited_code
            try:
                lines = edited_code.splitlines()
                def_index = next(i for i, line in enumerate(lines) if line.startswith(f"    def {method_name}("))
                end_index = len(lines)
                for i in range(def_index + 1, len(lines)):
                    if lines[i].startswith("    def ") or lines[i].startswith("if __name__ =="):
                        end_index = i
                        break
                body_lines = lines[def_index + 1:end_index]
                cleaned = []
                for line in body_lines:
                    cleaned.append(line[8:] if line.startswith("        ") else ("" if not line.strip() else line.strip()))
                elem.handler_code = "\n".join(cleaned).strip() or "pass"
            except (StopIteration, ValueError):
                pass
            self._update_code()
            self._save_state()
            self._update_status(f"Saved full code and handler for {elem.elem_type} ID {elem.elem_id}.")
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
                self._update_status("Opened temporary generated code in VS Code.")
            except Exception as e:
                messagebox.showerror("Execution Error", f"Could not launch VS Code. Ensure 'code' is in PATH.\n\n{e}", parent=top)

        ttk.Button(btn_frame, text="💾 Save", command=save_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💻 Open in VS Code", command=open_in_vscode).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Close", command=top.destroy).pack(side=tk.RIGHT, padx=2)
        text_widget.bind("<Control-s>", lambda event: (save_code(), "break")[1])
        text_widget.focus_set()

    # ─── Ctrl+A: select all elements on canvas ─────────────────────────────
    def _select_all(self, event=None):
        """Select all visible elements on the canvas."""
        all_visible = self._visible_elements()
        if not all_visible:
            return
        self._select_element(None, clear=True)  # clear current selection
        for elem in all_visible:
            self._select_element(elem, clear=False)
        self._update_status(f"Selected {len(all_visible)} elements.")


if __name__ == "__main__":
    root = tk.Tk()
    app = GUIBuilderApp(root)
    root.mainloop()