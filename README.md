# PasswordStorage

Simple password manager built with Tkinter and ttkbootstrap. Data is encrypted automatically using a fixed key and stored in `data.vault` next to the executable.
The interface uses a `ttk.Treeview` table with a consistent layout and tooltips for common actions.

## Usage

Install dependencies and run the application:

```bash
pip install -r requirements.txt
python password_manager.py
```

To build a portable version, use PyInstaller:

pip install -r requirements.txt
pyinstaller --noconfirm --onedir --hidden-import pyperclip password_manager.py
The executable will be located in `dist/password_manager/`.

Logs are written to `app.log` in the same directory as the executable. Check this file if the application exits unexpectedly.