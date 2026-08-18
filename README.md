# Tkinter Visual Designer

A comprehensive drag‑and‑drop GUI builder for Tkinter/CustomTkinter applications. Design interfaces visually, generate production‑ready Python code, and preview your work in real time—all without writing a single line of code manually.

---

## 📋 Overview

Tkinter Visual Designer is a complete WYSIWYG editor for building Tkinter and CustomTkinter applications. It provides a visual canvas where you can place, move, resize, and configure UI components through an intuitive point‑and‑click interface, while automatically generating the underlying Python code.

Whether you're prototyping a desktop application, teaching Python GUI development, or simply want to accelerate your workflow, this tool eliminates the tedious boilerplate of manual layout coding.

---

## ✨ Features

### Core Capabilities

- **Visual Drag‑and‑Drop Design** – Place widgets directly onto the canvas, move them freely, and resize using intuitive handles.
- **Live Code Generation** – Every design change instantly updates the generated Python code in the live preview panel.
- **Full Undo/Redo Support** – Ctrl+Z and Ctrl+Y work seamlessly across all design actions.
- **Copy/Paste Elements** – Duplicate widgets or entire containers with Ctrl+C and Ctrl+V.
- **Multi‑Select & Group Operations** – Select multiple elements and move or resize them together.
- **Snap‑to‑Grid** – Elements automatically align to a configurable grid for precise layouts.

### Widget Support

The toolbox includes a wide range of both standard Tkinter and modern CustomTkinter widgets:

| Category | Widgets |
|----------|---------|
| **Input** | Label, Entry, Button, Radiobutton, Checkbutton, Scale (Slider), Combobox, Spinbox, Listbox, Text (Multiline) |
| **Display** | Canvas, Progressbar, Scrollbar, Separator, Table (Excel/CSV), Image |
| **Containers** | Frame, LabelFrame, Notebook (Tabs), PanedWindow |

Each widget comes with sensible defaults and a full property inspector for customization.

### Property Inspector

Select any element to view and edit its properties in real time:
- Text content, fonts, colors, and dimensions
- Widget‑specific options (e.g., orientation, range values, tab lists)
- Color picker with RGB display
- Font selector with live preview of available system fonts
- Image and file pickers for Table and Image widgets

### Code Generation

- Generates clean, well‑structured Python code using CustomTkinter.
- Supports both `tkinter` and `customtkinter` widgets.
- Automatically includes necessary imports (`pandas` for tables, `PIL` for images).
- Injects a `_ToolTip` helper class for widgets with tooltips.
- Event handler stubs are created for widgets that support commands/bindings.

### Preview & Export

- **Run Preview** – Launch a temporary preview of your design with a single click.
- **Copy Code** – Copy the entire generated script to your clipboard.
- **Open in VS Code** – Export the code to a temporary file and open it in VS Code for further editing.
- **Save/Load Designs** – Project files use the `.tvd` (Tkinter Visual Design) format for round‑trip editing.

### Additional Features

- **Zoom** – Ctrl+Mouse Wheel to zoom in/out on the canvas.
- **Keyboard Shortcuts** – Arrow keys to nudge selected elements; Ctrl+A to select all.
- **Container Nesting** – Drag elements into Frames, LabelFrames, or Notebook tabs; parent‑child relationships are preserved in the generated code.
- **Notebook Tab Management** – Add/remove tabs directly from the property inspector.
- **Syntax‑Checked Code Editor** – Double‑click any element to open a dedicated code editor with syntax highlighting and real‑time error checking.

---

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Dependencies

```bash
pip install customtkinter pillow pandas
```

> **Note:** `customtkinter` is required for the modern widget set. `pillow` enables image support, and `pandas` is needed for Table (Excel/CSV) functionality.

### Running the Application

Clone the repository and run:

```bash
python gui_builder.py
```

---

## 🎮 Usage Guide

### Getting Started

1. **Launch the application** – The main window opens with a blank canvas, toolbox, and property inspector.

2. **Select a tool** – Click any widget in the toolbox (e.g., "Button", "Label", "Frame").

3. **Place the widget** – Click anywhere on the canvas to drop the selected widget.

4. **Move or resize** – Click and drag to reposition; use the corner/side handles to resize.

5. **Edit properties** – Select the widget and adjust its properties in the right panel.

6. **View the code** – Click "Toggle Code" to reveal the live‑generated Python script.

7. **Run your design** – Click "Run Preview" to launch your application in a separate window.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+C` | Copy selected elements |
| `Ctrl+V` | Paste elements |
| `Delete` | Delete selected elements |
| `Ctrl+A` | Select all visible elements |
| `Arrow Keys` | Nudge selected elements (1px or 10px with Shift held) |
| `Ctrl+Mouse Wheel` | Zoom canvas in/out |
| `Ctrl+S` | Save design |
| `Ctrl+O` | Load design |
| `Ctrl+N` | New design |

### Working with Containers

- **Frames/LabelFrames** – Drag widgets into them; they become children and are positioned relative to the container.
- **Notebook (Tabs)** – Drag widgets onto a specific tab; they will appear only when that tab is active.
- **Parent/Child relationships** are automatically tracked and reflected in the generated code.

### Adding Images

1. Place an **Image** widget on the canvas.
2. In the property inspector, click **Browse** next to the "Image File" field.
3. Select an image file (PNG, JPG, JPEG, GIF, BMP, ICO).
4. The image is copied to a `resources/` folder and embedded as a relative path.
5. The widget displays a thumbnail preview on the canvas.

### Using the Table Widget

1. Place a **Table** widget on the canvas.
2. In the property inspector:
   - **Excel/CSV File** – Browse to select a `.xlsx`, `.xls`, or `.csv` file.
   - **Sheet Name** – (For Excel) Specify the sheet name or index.
   - **Columns** – Comma‑separated list of column names (auto‑detected if left blank).
   - **Rows Visible** – Number of rows to display.
3. The generated code will load and display the first 10 rows of the data.

### Customizing Event Handlers

1. **Double‑click** any widget on the canvas to open the code editor.
2. The editor highlights the event handler method for that widget.
3. Write your custom logic inside the method body.
4. Click **Save** – the code is integrated back into the full script.
5. Click **Open in VS Code** to edit in your preferred editor.

---

## 🏗️ Architecture

The application is structured around several key components:

### `DesignElement`

A dataclass representing each widget on the canvas. Stores:
- Element type, position (`x`, `y`), dimensions (`canvas_w`, `canvas_h`)
- Properties dictionary (font, color, text, etc.)
- Parent/child relationships (`parent_id`, `parent_tab`)
- Generated handler code
- Canvas rendering IDs for efficient redraws

### `CanvasRenderer`

Handles all visual rendering on the Tkinter canvas:
- Draws each widget type with appropriate styling (flat, sunken, raised, groove)
- Manages selection handles and resize controls
- Supports zoom and grid rendering
- Efficient move operations using batched canvas translations

### `CodeGenerator`

Transforms the list of `DesignElement` objects into executable Python code:
- Orders elements by container depth for proper stacking
- Maps Tkinter properties to CustomTkinter equivalents where available
- Handles widget‑specific quirks (Notebook tabs, Progressbar values, Table loading)
- Injects tooltip helper class when needed
- Generates complete, runnable scripts

### `GUIBuilderApp`

The main application controller:
- Manages the UI (toolbox, canvas, property inspector, code panel)
- Handles user interactions (drag‑and‑drop, selection, resizing)
- Maintains undo/redo state
- Synchronizes design changes with code generation
- Manages file I/O (save/load `.tvd` files)

---

## 🛠️ Extending the Tool

### Adding a New Widget Type

1. Add an entry to `ELEMENT_TYPES` with display name, default size, and default properties.
2. Add property fields to `PROPERTY_FIELDS` for the inspector.
3. (Optional) Add a rendering method in `CanvasRenderer` (e.g., `_draw_mywidget`).
4. Map the widget to a Tkinter/CustomTkinter class in `CTK_WIDGET_MAP`.
5. Update `CTK_PROP_MAP` for property name mappings if needed.

### Customizing the Toolbox

The toolbox is dynamically built from `ELEMENT_TYPES`. Categories are inferred from the `"category"` field. Toggle between compact (icon‑only) and expanded (icon + label) modes using the "⊞ Icons" / "☰ Labels" button.

---

## 📁 File Format (`.tvd`)

Designs are saved as JSON files with the following structure:

```json
{
  "elements": [...],
  "next_id": 42,
  "reusable_ids": [...],
  "window_title": "My Application",
  "canvas_w": 800,
  "canvas_h": 600,
  "canvas_bg": "#FFFFFF",
  "canvas_imports": "import tkinter as tk\nfrom tkinter import ttk",
  "full_code": "..."
}
```

Each element in the `"elements"` array stores its type, position, dimensions, properties, handler code, and parent relationships.

---

## Live Code Generator
```
"""Generated by Tkinter Visual Designer."""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

ctk.set_appearance_mode("light")  # force light theme regardless of OS setting
ctk.set_default_color_theme("blue")

class MainApplication:
    def __init__(self, root):
        self.root = root
        root.title("My Application")
        root.geometry("800x600")
        root.configure(bg="#FFFFFF")

        self._elem_1 = ctk.CTkButton(root, text="Button", font=('Segoe UI', 9, 'bold'), text_color="#FFFFFF", fg_color="#1976D2", command=self._on_Button_1, width=100, height=34)
        self._elem_1.place(x=300, y=160)

    def _on_Button_1(self, event=None):
        """
        Event handler for Button (ID: 1).
        Triggered by: command
        Access widget instance via: self._elem_1
        """
        pass


if __name__ == '__main__':
    root = ctk.CTk()
    app = MainApplication(root)
    root.mainloop()

```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/tkinter-visual-designer.git
cd tkinter-visual-designer

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python gui_builder.py
```

---

## 📄 License

This project is open‑source and available under the MIT License.

---

## 🙏 Acknowledgements

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) – Modern, customizable widgets for Tkinter.
- [Pillow](https://python-pillow.org/) – Python Imaging Library for image support.
- [pandas](https://pandas.pydata.org/) – Data analysis library used for Table widget functionality.

---

## 📞 Support

- **Issues**: Please report bugs and request features via the [GitHub Issues](https://github.com/yourusername/tkinter-visual-designer/issues) page.
- **Discussions**: Join the conversation in the [GitHub Discussions](https://github.com/yourusername/tkinter-visual-designer/discussions) forum.

---

*Built with ❤️ for the Python community.*
