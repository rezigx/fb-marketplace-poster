# Packaging — build a single Windows .exe

Compile the desktop app into a distributable `.exe` with PyInstaller.

## Prerequisites (on a Windows machine)
1. Install Python 3.11+ (check "Add to PATH" during install).
2. Install Playwright browsers once:
   ```
   pip install playwright
   playwright install chromium
   ```

## Build steps
```bash
cd desktop
pip install -r requirements.txt
pyinstaller --onefile --windowed --name FBPoster ^
  --add-data "facebook;facebook" ^
  main_qt.py
```

- `--onefile` → single `.exe`
- `--windowed` → no CMD console window (GUI only)
- Entry point is `main_qt.py` (PySide6 Steam-style GUI)
- Output: `desktop/dist/FBPoster.exe`

> On Linux/macOS, replace `^` line-continuation with `\` and `;` with `:` for `--add-data`.

## Notes
- The app writes `settings.json` and `products.json` next to the `.exe`.
- The Facebook login session (`fb_session.json`) is saved in the `facebook/` folder.
- The `api_base_url` must point to your deployed backend (set in Settings).

## First-run for your customer
1. Customer downloads `FBPoster.exe`.
2. Opens it → Settings → pastes the license key you gave them.
3. Logs into Facebook (once) when prompted.
4. Builds a product → clicks Post.
