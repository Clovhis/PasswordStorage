"""Simple password manager application."""

import json
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import logging

import pyperclip
from cryptography.fernet import Fernet
import ttkbootstrap as tb
from ttkbootstrap.tooltip import ToolTip

DEFAULT_FONT = ("Helvetica", 10)

# Fixed key for symmetric encryption
_KEY = b'510xYPt3EyKwn27amFGZYjbQnO83TvM44AUZ_MtKSXM='

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

DATA_FILE = BASE_DIR / 'data.vault'
LOG_FILE = BASE_DIR / 'error.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


class PasswordManager(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")

        # Usar propiedad style existente sin sobrescribirla
        self.style.theme_use("flatly")
        style = self.style
        style.configure("Treeview", font=DEFAULT_FONT, rowheight=25)
        style.configure("Treeview.Heading", font=DEFAULT_FONT)
        style.map("Treeview", background=[("selected", style.colors.primary)])

        self.title("Gestor de Contraseñas")
        self.geometry("900x500")
        self.resizable(True, True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.fernet = Fernet(_KEY)
        self.entries = []
        self._load_entries()
        self._create_widgets()
        self._populate_table()

    def _create_widgets(self):
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("title", "username", "password", "url", "notes"),
            show="headings",
        )
        column_titles = {
            "title": "Título",
            "username": "Usuario",
            "password": "Contraseña",
            "url": "URL",
            "notes": "Notas",
        }
        for col in ("title", "username", "password", "url", "notes"):
            self.tree.heading(col, text=column_titles[col], anchor="center")
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("notes", width=200, anchor="center")

        ysb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, pady=5)

        add_btn = tb.Button(
            btn_frame,
            text="Agregar",
            width=10,
            command=self._add_entry,
            bootstyle="success",
        )
        user_btn = tb.Button(
            btn_frame,
            text="Copiar usuario",
            command=self._copy_username,
            width=12,
        )
        pass_btn = tb.Button(
            btn_frame,
            text="Copiar contraseña",
            command=self._copy_password,
            width=14,
        )
        del_btn = tb.Button(
            btn_frame,
            text="Eliminar",
            bootstyle="danger",
            command=self._delete_entry,
            width=10,
        )
        save_btn = tb.Button(
            btn_frame,
            text="Guardar",
            bootstyle="primary",
            command=self._save_entries,
            width=10,
        )

        for i, btn in enumerate((add_btn, user_btn, pass_btn, del_btn, save_btn)):
            btn.grid(row=0, column=i, padx=10)

        ToolTip(add_btn, text="Agregar nueva entrada")
        ToolTip(user_btn, text="Copiar usuario")
        ToolTip(pass_btn, text="Copiar contraseña")
        ToolTip(del_btn, text="Eliminar entrada")
        ToolTip(save_btn, text="Guardar cambios")

    def _populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Estilo seguro para fondo de filas pares
        self.tree.tag_configure("even", background=self.style.colors.bg)

        for idx, entry in enumerate(self.entries):
            values = (
                entry.get("title", ""),
                entry.get("username", ""),
                "******",
                entry.get("url", ""),
                entry.get("notes", ""),
            )
            tags = ("even",) if idx % 2 == 0 else ()
            self.tree.insert("", "end", iid=str(idx), values=values, tags=tags)

    def _add_entry(self):
        dialog = tb.Toplevel(self)
        dialog.title("Nueva entrada")
        dialog.grab_set()
        dialog.columnconfigure(1, weight=1)

        fields = [
            ("title", "Título"),
            ("username", "Usuario"),
            ("password", "Contraseña"),
            ("url", "URL"),
            ("notes", "Notas"),
        ]
        entries = {}
        for i, (key, label) in enumerate(fields):
            ttk.Label(dialog, text=label, font=DEFAULT_FONT).grid(
                row=i, column=0, padx=10, pady=5, sticky="e"
            )
            ent = ttk.Entry(
                dialog,
                width=40,
                show="*" if key == "password" else "",
                font=DEFAULT_FONT,
            )
            ent.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entries[key] = ent

        def save():
            entry = {
                "title": entries["title"].get(),
                "username": entries["username"].get(),
                "password": entries["password"].get(),
                "url": entries["url"].get(),
                "notes": entries["notes"].get(),
            }
            self.entries.append(entry)
            self._populate_table()
            dialog.destroy()

        ttk.Button(dialog, text="Guardar", command=save, width=10).grid(
            row=len(labels), column=0, columnspan=2, pady=10
        )

    def _delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Información", "Seleccione una entrada")
            return
        if not messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar esta entrada?"):
            return
        idx = int(selected[0])
        self.entries.pop(idx)
        self._populate_table()

    def _copy_username(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        pyperclip.copy(self.entries[idx]["username"])

    def _copy_password(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        pyperclip.copy(self.entries[idx]["password"])

    def _save_entries(self):
        data = json.dumps(self.entries).encode()
        enc = self.fernet.encrypt(data)
        with open(DATA_FILE, "wb") as f:
            f.write(enc)
        messagebox.showinfo("Guardado", "Datos guardados")

    def _load_entries(self):
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "rb") as f:
                    data = f.read()
                decoded = self.fernet.decrypt(data)
                self.entries = json.loads(decoded.decode())
            except Exception:
                logger.exception("Failed to load entries")
                messagebox.showerror("Error", "No se pudo leer archivo de datos")
                self.entries = []
        else:
            self.entries = []


if __name__ == "__main__":
    try:
        app = PasswordManager()
        app.mainloop()
    except Exception as e:
        logger.exception("Unhandled exception")
        try:
            messagebox.showerror("Error", str(e))
        except Exception:
            pass
