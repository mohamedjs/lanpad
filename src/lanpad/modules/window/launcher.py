"""Native desktop application window launcher with browser fallback and crash reaping."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

SIZE = (1220, 880)


def find_chromium_browsers() -> List[str]:
    """Locate installed Chromium-family browsers supporting --app mode."""
    found = []

    if sys.platform.startswith("win"):
        roots = [
            os.environ.get("PROGRAMFILES(X86)", ""),
            os.environ.get("PROGRAMFILES", ""),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        rels = [
            r"Microsoft\Edge\Application\msedge.exe",
            r"Google\Chrome\Application\chrome.exe",
            r"BraveSoftware\Brave-Browser\Application\brave.exe",
        ]
        for r in filter(None, roots):
            for rel in rels:
                p = Path(r) / rel
                if p.is_file():
                    found.append(str(p))
        return found

    if sys.platform == "darwin":
        apps = ["Google Chrome", "Microsoft Edge", "Brave Browser", "Chromium"]
        for a in apps:
            p = Path(f"/Applications/{a}.app/Contents/MacOS/{a}")
            if p.is_file():
                found.append(str(p))
        return found

    # Linux / BSD
    names = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "microsoft-edge",
        "microsoft-edge-stable",
        "brave-browser",
    ]
    for name in names:
        p = shutil.which(name)
        if p:
            found.append(p)

    return found


def open_fallback_browser(url: str) -> None:
    """Open URL in the user's default browser."""
    if sys.platform.startswith("win"):
        subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", url])
    else:
        subprocess.Popen(["xdg-open", url])


def launch_native_window(url: str, data_dir: Optional[Path] = None) -> bool:
    """Launch the client UI in a chromeless desktop window with fallback."""
    browsers = find_chromium_browsers()
    profile_dir = (data_dir or Path.home() / ".config" / "lanpad") / "window-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    args = [
        f"--app={url}",
        f"--window-size={SIZE[0]},{SIZE[1]}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    for browser in browsers:
        try:
            proc = subprocess.Popen(
                [browser, *args],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True if not sys.platform.startswith("win") else False,
            )
            return True
        except Exception:
            continue

    # Fallback to default system browser
    open_fallback_browser(url)
    return False
