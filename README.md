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

```bash
pyinstaller --noconfirm --onedir password_manager.py
```

The executable will be located in `dist/password_manager/`.

## GitHub Actions
The repository includes a workflow that builds the executable and attaches a zip
archive to a release when pushing to branches named `feature/**`. The workflow
grants `contents: write` permission to `GITHUB_TOKEN` so it can publish the
release automatically.
