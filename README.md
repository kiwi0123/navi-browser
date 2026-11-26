[join our discord server for more information](https://discord.gg/2ps9Fq6fpH)

## .exe
you can download v2.0 at [here](https://github.com/navi-browser/blob/main/NaviBrowser.exe).
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

that below is the logo if anyone wants it

<img src="betterlogo.png">

# DISCLAIMER:

### so, navi is probably gonna get an update which is gonna make it closed-source, BUT this version stays open source and you can still use it if you want. you can see the link to the new version below (if it's not there, we aren't done making it.)

this part is honestly not necessary but i'll add it anyways. wait nvm, i got dinner. i'll finish this later.

ok im back guys, anyways. i just wanted to say that this version of navi is PyQt6, but the new version will use ImGui, which is why i added the license. you are still allowed to use this version and copy it, i really dont care, anyways, ImGui version is coming soon!

# navi has gotten a BIG update

after a year of not doing shit, i added a lot of privacy features. have fun, i'll probably be gone for months now.
