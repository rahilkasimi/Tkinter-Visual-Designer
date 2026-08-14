# Tkinter Visual GUI Designer

A full-featured drag-and-drop GUI builder and Python code generator built using standard Tkinter. This application allows developers to visually design user interfaces, modify widget properties, manage container hierarchies, and generate clean object-oriented Python code.

---

## 🚀 Key Features

* **Visual Drag-and-Drop Canvas**: Easily position and resize widgets on an interactive canvas with snap-to-grid support.


* **Rich Component Catalogue**: Supports 19 standard Tkinter and TTK widgets split across Input, Display, and Container categories.


* **Container Hierarchy & Nesting**: Nest components directly inside `Frame`, `LabelFrame`, `PanedWindow`, and tabbed `Notebook` widgets.


* **Property Inspector**: Edit widget properties in real time, including text, geometry, colors (via integrated color picker), and fonts.


* **Live Code Generator**: Generates standalone, structured Python code using an object-oriented `MainApplication` class pattern.


* **Interactive Event Handlers**: Assign event bindings and write custom Python logic for widgets directly within the app.


* **Tabular Data Preview**: View and load Excel (`.xlsx`, `.xls`) or CSV datasets inside `ttk.Treeview` tables using Pandas integration.


* **Design File Persistence**: Save and reload project files using standard JSON (`.tvd`) format.


* **Full Editing Controls**: Complete support for Undo/Redo (`Ctrl+Z` / `Ctrl+Y`), multi-element selection, arrow key nudging, and Copy/Paste clipboard functionality (`Ctrl+C` / `Ctrl+V`).



---

## 📦 Supported Widgets Catalogue

The designer provides built-in support for the following UI components:

### ✍️ Input Controls

* **Label**: Static text display widget with font and alignment customization.


* **Entry**: Single-line text input field supporting password masking and variable binding.


* **Button**: Action trigger button with custom command handlers.


* **Radiobutton**: Radio option selector linked to string or integer variables.


* **Checkbutton**: Toggle checkbox supporting integer or boolean variable binding.


* **Scale**: Horizontal or vertical slider control with range and resolution parameters.


* **Combobox**: TTK dropdown selection menu.


* **Spinbox**: Numerical range input field with step arrows.



### 📝 Display Controls

* **Listbox**: Multi-item scrollable list selector.


* **Text**: Multi-line text editing field with custom word-wrapping modes.


* **Canvas**: Standard drawing area widget.


* **Progressbar**: Progress bar supporting horizontal and vertical orientations.


* **Scrollbar**: Standard scrollbar component.


* **Separator**: Visual dividing line for UI sections.


* **Table**: Data view treeview component with optional CSV/Excel file loading.



### 🖼️ Containers

* **Frame**: Structural background container with customizable border relief styles.


* **LabelFrame**: Bordered container box with an integrated title label.


* **Notebook**: Tabbed container interface allowing multi-page tab management.


* **PanedWindow**: Split-pane container supporting horizontal and vertical resizable panes.



---

## ⚙️ Requirements & Installation

### Prerequisites

* Python 3.8+


* Tkinter (included in standard Python installations on Windows/macOS)


* `pandas` and `openpyxl` (optional, required only if loading Excel files into Table widgets)



### Installation

Clone or download the source code file:

```bash
git clone https://github.com/your-username/tkinter-visual-designer.git
cd tkinter-visual-designer

```

Install optional dependencies for Excel table imports:

```bash
pip install pandas openpyxl

```

### Running the Application

Run the Python script directly:

```bash
python tkinter_designer.py

```

---

## ⌨️ Shortcuts & Controls

| Action | Shortcut / Mouse Gesture | Description |
| --- | --- | --- |
| **Add Widget** | Click Tool → Click Canvas | Selects a component from the toolbox and places it onto the canvas grid.

 |
| **Multi-Select** | `Ctrl` + Click | Adds or removes individual widgets to the selection group.

 |
| **Box Select** | Click & Drag on Canvas | Creates a drag box to select multiple widgets simultaneously.

 |
| **Move / Nudge** | Arrow Keys | Nudges selected widgets by 1 px (or 10 px when holding `Shift`).

 |
| **Copy Elements** | `Ctrl + C` | Copies selected elements to the internal clipboard.

 |
| **Paste Elements** | `Ctrl + V` | Pastes copied elements onto the active design canvas.

 |
| **Delete** | `Delete` key / Red 'X' | Deletes selected widgets and any contained child elements.

 |
| **Undo** | `Ctrl + Z` | Reverts the last layout or property change.

 |
| **Redo** | `Ctrl + Y` | Reapplies the previously undone action.

 |
| **Save Project** | `Ctrl + S` | Saves the full project to a `.tvd` JSON file.

 |
| **Load Project** | `Ctrl + O` | Opens an existing `.tvd` project file.

 |
| **New Design** | `Ctrl + N` | Resets the workspace for a new design layout.

 |
| **Code Editor** | Double-Click Widget | Opens the custom code editor window for the widget.

 |

---

## 📄 Project File Format (`.tvd`)

Project files are saved as structured JSON documents (`.tvd`) containing all canvas element definitions, parent-child container IDs, geometry coordinates, widget properties, and custom Python event logic.

---

## 💻 Generated Code Structure

The visual designer outputs modular Python code following strict object-oriented best practices:

```python
"""Generated by Tkinter Visual Designer."""

import tkinter as tk
from tkinter import ttk

class MainApplication:
    def __init__(self, root):
        self.root = root
        root.title("My Application")
        root.geometry("800x600")
        root.configure(bg="#FAFAFA")

        # Widget Instantiation & Placement
        self._elem_1 = tk.Button(root, text="Click Me", command=self._on_Button_1)
        self._elem_1.place(x=100, y=100, width=100, height=34)

    def _on_Button_1(self, event=None):
        """
        Event handler for Button (ID: 1).
        Triggered by: command
        Access widget instance via: self._elem_1
        """
        print("Button clicked!")

if __name__ == '__main__':
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

```
