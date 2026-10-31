# Dough Calculator v6 — Ubuntu + Android

## Ubuntu (22.04 / 24.04 or newer)
Download `dough-calculator_6.0_all.deb` from the [Releases](../../releases) page, then:
    sudo apt install ./dough-calculator_6.0_all.deb
Then open **Dough Calculator** from the app menu, or run `dough-calculator`.
Command-line mode: `dough-calculator --cli --size 14 --count 4 --thickness thin [--gf]`
Remove: `sudo apt remove dough-calculator`

## Windows 10 / 11
Download `DoughCalculator.exe` from the [Releases](../../releases) page and double-click it — no install or Python needed.
If SmartScreen says "Windows protected your PC", choose **More info → Run anyway** (the exe isn't code-signed).
The exe is built automatically by GitHub Actions (`.github/workflows/windows-exe.yml`) whenever a release is published.

## Android only tested on (Pixel 9a) 
1. Download `DoughCalculator-6.0.apk` from the [Releases](../../releases) page and copy it to the phone (Drive, USB, email…), or `adb install DoughCalculator-6.0.apk`.
2. Tap it in Files. When prompted, allow "Install unknown apps" for that app.
3. If Play Protect warns about an unknown developer, choose **More details → Install anyway**.
Works fully offline. "Share / save" opens the Android share sheet (Drive, Files, Messages, Keep…).

## Layout
- `src/dough_calculator.py` – Python/Tkinter source (rebuilt from the .exe; bytecode-identical)
- `web/` – phone port (HTML/JS, same formulas; also works as an installable web app if hosted over HTTPS)
- `android/` – Android Studio/Gradle project wrapping `web/` (`./gradlew assembleRelease`)
- `android/dough-release.jks` – signing key (**not in this repo**; keep a private backup). Future updates must be signed with the same key. Set `DOUGH_KS_PASS` before `./gradlew assembleRelease`.
- `packaging/ubuntu/` – .deb control file, launcher and .desktop entry
