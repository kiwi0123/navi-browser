[join our discord server for more information](https://discord.gg/2ps9Fq6fpH)

## .exe
you can download v2.0 at [here](https://github.com/kiwi0123/navi-browser/blob/main/NaviBrowser.exe).
windows will refuse to run, just click "more" and "run anyway"

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

# features
## privacy:
Blocks trackers and advertising domains
Blocks third-party cookies
Enables HTTPS-upgrade behavior
Removes tracking parameters such as utm_*, fbclid, and gclid
Can block WebGL to reduce fingerprinting
Blocks browser permission requests such as location, camera, and microphone
Keeps cookies in memory and does not save browsing history.

## search engine availability:

   " Mainstream:
        Google
        Bing
        Brave
        DuckDuckGo
        Yahoo
    
  " Privacy & Indie:
        Startpage
        Qwant
        Searx
        Mojeek
        Swisscows
        Gigablast
        Metager
    
 " Eco & Social:
        Ecosia
        OceanHero
        GiveWater
        Ekosearch
    
   " AI & Research:
        Perplexity
        Phind
        You.com
        Consensus
        Google Scholar
        Wolfram Alpha
        Dimensions
    
   " Global & Specialized:
        Wikipedia
        Baidu
        Naver
        Yandex
        Ask
        YouTube
        GitHub
        Reddit
        Wayback
        Amazon
        Twitter

# more
Tor/SOCKS support: can route traffic through Tor on ports 9050 or 9150, after a restart.

Bookmarks and search history-free navigation.

Download protection: prompts before downloading executable or script formats such as .exe, .bat, .apk, and .sh.

Panic mode: Ctrl+Shift+Delete clears cookies/cache and closes extra tabs.

Dark, light, and neon themes.

Local HTML websites: users can create and store HTML/CSS/JavaScript pages on their own computer under custom .pw-navi-style names.

Name store: spend a built-in “Navit” reward currency to register local site-name suffixes.

Extension lab: write and enable JavaScript snippets, similar to simple browser extensions.

Standard browser shortcuts for tabs, address-bar focus, reload, find, zoom, and navigation.

# yo yo yo
after a year of not doing shit, i added a lot of privacy features. have fun, i'll probably be gone for months now.
