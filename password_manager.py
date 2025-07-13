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

# Fixed key for symmetric encryption
_KEY = b'510xYPt3EyKwn27amFGZYjbQnO83TvM44AUZ_MtKSXM='

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / 'data.vault'
LOG_FILE = BASE_DIR / 'app.log'

# Configure application wide logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

class PasswordManager(tb.Window):
    def __init__(self):
        super().__init__(themename="flatly")  # Initialize themed window
        self.title("Password Manager")
        self.geometry("900x500")
        self.resizable(False, False)

        logging.info("Application started")

        self.fernet = Fernet(_KEY)
        self.entries = []
        self._load_entries()
        self._create_widgets()
        self._populate_table()

    def _create_widgets(self):
        """Create the table and control buttons."""
        self.tree = ttk.Treeview(
            self,
            columns=("title", "username", "password", "url", "notes"),
            show="headings",
        )
        for col in ("title", "username", "password", "url", "notes"):
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=150)
        self.tree.column("notes", width=200)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)

        tb.Button(
            btn_frame,
            text="+",
            width=3,
            command=self._add_entry,
            bootstyle="success",
        ).grid(row=0, column=0, padx=5)
        tb.Button(btn_frame, text="Copy User", command=self._copy_username).grid(row=0, column=1, padx=5)
        tb.Button(btn_frame, text="Copy Pass", command=self._copy_password).grid(row=0, column=2, padx=5)
        tb.Button(
            btn_frame,
            text="Delete",
            bootstyle="danger",
            command=self._delete_entry,
        ).grid(row=0, column=3, padx=5)
        tb.Button(
            btn_frame,
            text="Guardar",
            bootstyle="primary",
            command=self._save_entries,
        ).grid(row=0, column=4, padx=5)

    def _populate_table(self):
        """Refresh the treeview with current entries."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, entry in enumerate(self.entries):
            values = (
                entry.get("title", ""),
                entry.get("username", ""),
                "******",  # mask password
                entry.get("url", ""),
                entry.get("notes", ""),
            )
            self.tree.insert("", "end", iid=str(idx), values=values)
        logging.debug("Table populated with %d entries", len(self.entries))

    def _add_entry(self):
        """Open dialog to capture a new password entry."""
        dialog = tb.Toplevel(self)
        dialog.title("Nueva entrada")
        dialog.grab_set()

        labels = ["Title", "User Name", "Password", "URL", "Notes"]
        entries = {}
        for i, text in enumerate(labels):
            ttk.Label(dialog, text=text).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            ent = ttk.Entry(dialog, width=40, show="*" if text == "Password" else "")
            ent.grid(row=i, column=1, padx=5, pady=5)
            entries[text.lower().replace(" ", "")] = ent
        def save():
            """Save the captured data into memory."""
            entry = {
                "title": entries["title"].get(),
                "username": entries["username"].get(),
                "password": entries["password"].get(),
                "url": entries["url"].get(),
                "notes": entries["notes"].get(),
            }
            self.entries.append(entry)
            logging.info("Entry added: %s", entry["title"])
            self._populate_table()
            dialog.destroy()
        ttk.Button(dialog, text="Guardar", command=save).grid(row=len(labels), column=0, columnspan=2, pady=10)

    def _delete_entry(self):
        """Delete the selected entry from memory."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Seleccione una entrada")
            return
        if not messagebox.askyesno("Confirmar", "¿Estás seguro de eliminar esta entrada?"):
            return
        idx = int(selected[0])
        removed = self.entries.pop(idx)
        logging.info("Entry deleted: %s", removed.get("title", ""))
        self._populate_table()

    def _copy_username(self):
        """Copy the selected entry's username to the clipboard."""
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        pyperclip.copy(self.entries[idx]["username"])
        logging.info("Username copied for entry: %s", self.entries[idx]["title"])

    def _copy_password(self):
        """Copy the selected entry's password to the clipboard."""
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        pyperclip.copy(self.entries[idx]["password"])
        logging.info("Password copied for entry: %s", self.entries[idx]["title"])

    def _save_entries(self):
        """Encrypt and persist entries to disk."""
        data = json.dumps(self.entries).encode()
        enc = self.fernet.encrypt(data)
        with open(DATA_FILE, "wb") as f:
            f.write(enc)
        logging.info("Entries saved")
        messagebox.showinfo("Guardado", "Datos guardados")

    def _load_entries(self):
        """Load and decrypt saved entries from disk."""
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "rb") as f:
                    data = f.read()
                decoded = self.fernet.decrypt(data)
                self.entries = json.loads(decoded.decode())
                logging.info("Loaded %d entries", len(self.entries))
            except Exception as exc:
                logging.exception("Failed to load entries: %s", exc)
                messagebox.showerror("Error", "No se pudo leer archivo de datos")
                self.entries = []
        else:
            logging.info("Data file not found, starting with empty list")

if __name__ == "__main__":
    # Entry point when running as a script
    app = PasswordManager()
    app.mainloop()
