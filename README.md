[join our discord server for more information](https://discord.gg/2ps9Fq6fpH)

## .exe

you can download v2.0 [here](https://github.com/kiwi0123/navi-browser/raw/main/NaviBrowser.exe). this is V2.0 so further version wont be available there until i update it.

windows will refuse to run it at first, just click "More info" and then "Run anyway".

## 🛠️ How to Build

### Windows

Before you start, make sure you have Git and Python installed on your computer.

First, open a terminal (PowerShell or Command Prompt) and run:

```
git clone https://github.com/kiwi0123/navi-browser.git
```

Then:

```
cd navi-browser
```

Then:

```
pip install -r requirements.txt
```

Last step:

```
python n_main.py
```

### Linux

Before you start, make sure you have Git and Python 3 installed. Don't run Navi as root, because the browser engine refuses to start that way.

1. Clone the repo:

```bash
git clone https://github.com/kiwi0123/navi-browser.git
```

2. Go into the folder:

```bash
cd navi-browser
```

3. Create and activate a virtual environment:

```bash
python3 -m venv venv && source venv/bin/activate
```

4. Install the requirements:

```bash
pip install PyQt6 PyQt6-WebEngine
```

5. Run Navi:

```bash
python n_main.py
```

Next time, you only need to run these two commands from the `navi-browser` folder:

```bash
source venv/bin/activate
python n_main.py
```

**If Navi won't start**, you are probably missing a system library. The usual fix:

```bash
# Debian / Ubuntu
sudo apt install libnss3 libxcb-cursor0 libegl1

# Fedora
sudo dnf install nss xcb-util-cursor

# Arch
sudo pacman -S nss xcb-util-cursor
```

If the window looks broken on Wayland, try `QT_QPA_PLATFORM=xcb python n_main.py`.

**Tor mode on Linux:** install Tor (`sudo apt install tor`, or your distro's equivalent), make sure it is running, then pick Tor in Settings and restart Navi.

# Features

## Privacy

- Blocks common tracker and advertising domains (built-in list, and you can add your own hosts-format list)
- Blocks third-party cookies
- HTTPS-only: upgrades `http://` links to `https://` and asks before falling back to HTTP
- Removes tracking parameters such as `utm_*`, `fbclid` and `gclid` from links you open
- Sends the Global Privacy Control and Do Not Track signals
- Stops WebRTC from leaking your real IP address
- Rejects invalid HTTPS certificates, with no click-through
- Always denies permission requests (location, camera, microphone, notifications), and autoplay needs a click
- Optional WebGL blocking to reduce fingerprinting (off by default, it can break 3D sites)
- Shield button in the toolbar: turn protection off for one site if it breaks
- No browsing history is saved, and cookies and cache are kept in memory only

## Search engines

- **Mainstream:** Google, Bing, Brave, DuckDuckGo, Yahoo
- **Privacy & Indie:** Startpage, Qwant, Searx, Mojeek, Swisscows, Gigablast, Metager
- **Eco & Social:** Ecosia, OceanHero, GiveWater, Ekosearch
- **AI & Research:** Perplexity, Phind, You.com, Consensus, Google Scholar, Wolfram Alpha, Dimensions
- **Global & Specialized:** Wikipedia, Baidu, Naver, Yandex, Ask, YouTube, GitHub, Reddit, Wayback, Amazon, Twitter

## More

- **Tor/SOCKS support:** route all traffic through Tor on port 9050 or 9150 (Tor must be installed and running, and switching needs a restart)
- **Bookmarks:** saved on your device (Ctrl+D)
- **Download protection:** you choose where each file is saved, and Navi asks first for risky types such as `.exe`, `.bat`, `.apk` and `.sh`
- **Panic mode:** Ctrl+Shift+Delete clears cookies and cache and closes extra tabs
- **Themes:** dark, light and neon
- **Local websites:** create HTML/CSS/JavaScript pages that are stored on your own computer, with names like `mysite.pw-navi` or `mysite.fav`
- **Name store:** spend Navits (a reward counter you earn by browsing) on site-name endings for your local websites
- **Extension lab:** write and switch on JavaScript snippets, similar to simple browser extensions
- **Shortcuts:** the usual ones for tabs, address bar, reload, find, zoom and navigation

## Limitations

- Navi doesn't protect you from browser fingerprinting beyond the optional WebGL block, so sites can still tell your browser apart from others
- Tor mode hides your IP address, but it isn't the same as Tor Browser, which also disguises your browser fingerprint
- The tracker list is much smaller than a full ad blocker like uBlock Origin, so some ads and trackers will get through
- Navi is built on QtWebEngine (Chromium), so its security depends on the PyQt6-WebEngine version, and the `.exe` is only as up to date as when it was built
- Your settings, bookmarks, local websites and extensions are stored unencrypted in the Navi data folder
- Local websites exist only on your computer, they are not shared with anyone
- Extensions run on every page you visit while they are switched on, so only add code you trust
- Navits are a local counter, not real currency
- Some search engines on the list are small independent services and may change or go offline, switch engine in Settings if one stops working

# yo yo yo

after a year of not doing shit, i added a lot of privacy features. have fun, i'll probably be gone for months now.
