import sys
import json
import os
import re
import time
import socket
import html
from datetime import datetime
from urllib.parse import quote, quote_plus, unquote, unquote_plus, urlsplit, urlunsplit
from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox, QTabWidget, QMenu, QDialog, QScrollArea,
    QHBoxLayout, QFrame, QCheckBox, QInputDialog, QPlainTextEdit,
    QProgressBar, QStatusBar, QFileDialog
)
from PyQt6.QtGui import QAction, QIcon, QFont, QColor, QPalette, QKeySequence
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineSettings,
    QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
)

APP_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~/.local/share"), "NaviBrowser")
try:
    os.makedirs(APP_DIR, exist_ok=True)
except OSError:
    APP_DIR = "."
DATA_FILE = os.path.join(APP_DIR, "navi_data.json")
LEGACY_DATA_FILE = "navi_data.json"
BLOCKLIST_FILE = os.path.join(APP_DIR, "blocklist.txt")

TLD_ALIASES = {
    ".fav": ".favourite", ".favourite": ".fav",
    ".wrn": ".warn", ".warn": ".wrn",
    ".ntw": ".network", ".network": ".ntw",
    ".glbl": ".global", ".global": ".glbl"
}

TNN_TLDS = [".fav", ".favourite", ".wrn", ".warn", ".ntw", ".network", ".glbl", ".global", ".cops", ".apples", ".pw-navi"]

SEARCH_ENGINES = {
    "Mainstream": {
        "Google": "https://www.google.com/search?q=",
        "Bing": "https://www.bing.com/search?q=",
        "Brave": "https://search.brave.com/search?q=",
        "DuckDuckGo": "https://duckduckgo.com/?q=",
        "Yahoo": "https://search.yahoo.com/search?p="
    },
    "Privacy & Indie": {
        "Startpage": "https://www.startpage.com/do/search?q=",
        "Qwant": "https://www.qwant.com/?q=",
        "Searx": "https://searx.be/search?q=",
        "Mojeek": "https://www.mojeek.com/search?q=",
        "Swisscows": "https://swisscows.com/en/web?query=",
        "Gigablast": "https://www.gigablast.com/search?q=",
        "Metager": "https://metager.org/meta/meta.ger3?eingabe="
    },
    "Eco & Social": {
        "Ecosia": "https://www.ecosia.org/search?q=",
        "OceanHero": "https://oceanhero.today/web?q=",
        "GiveWater": "https://www.givewater.com/?s=",
        "Ekosearch": "https://www.ekosearch.org/search?q="
    },
    "AI & Research": {
        "Perplexity": "https://perplexity.ai/search?q=",
        "Phind": "https://www.phind.com/search?q=",
        "You.com": "https://you.com/search?q=",
        "Consensus": "https://consensus.app/results/?q=",
        "Google Scholar": "https://scholar.google.com/scholar?q=",
        "Wolfram Alpha": "https://www.wolframalpha.com/input?i=",
        "Dimensions": "https://app.dimensions.ai/discover/publication?search_text="
    },
    "Global & Specialized": {
        "Wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search=",
        "Baidu": "https://www.baidu.com/s?wd=",
        "Naver": "https://search.naver.com/search.naver?query=",
        "Yandex": "https://yandex.com/search/?text=",
        "Ask": "https://www.ask.com/web?q=",
        "YouTube": "https://www.youtube.com/results?search_query=",
        "GitHub": "https://github.com/search?q={}&type=repositories",
        "Reddit": "https://www.google.com/search?q={}+site:reddit.com",
        "Wayback": "https://web.archive.org/web/*/",
        "Amazon": "https://www.amazon.com/s?k=",
        "Twitter": "https://twitter.com/search?q="
    }
}

ALL_ENGINES = [e for cat in SEARCH_ENGINES.values() for e in cat]
DEFAULT_ENGINE = "DuckDuckGo"

RISKY_EXTENSIONS = (".exe", ".msi", ".bat", ".cmd", ".scr", ".com", ".ps1", ".vbs", ".js", ".jar",
                    ".apk", ".dmg", ".pkg", ".sh", ".lnk", ".reg", ".hta")

PRIVACY_TOGGLES = ("block_trackers", "https_only", "block_3p_cookies", "strip_params", "block_webgl")


def get_search_url(engine_name, query):
    for cat in SEARCH_ENGINES.values():
        if engine_name in cat:
            base = cat[engine_name]
            if engine_name == "Wayback":
                return base + query
            q = quote_plus(query)
            return base.format(q) if "{}" in base else base + q
    return SEARCH_ENGINES["Mainstream"][DEFAULT_ENGINE] + quote_plus(query)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


TOR_ACTIVE = False


def read_saved_settings():
    for path in (DATA_FILE, LEGACY_DATA_FILE):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f).get("settings", {})
            except Exception:
                pass
    return {}


def configure_chromium(settings):
    global TOR_ACTIVE
    flags = [
        "--webrtc-ip-handling-policy=disable_non_proxied_udp",
        "--force-webrtc-ip-handling-policy",
    ]
    if settings.get("network_mode") == "tor":
        try:
            port = int(settings.get("tor_port", 9050))
        except (TypeError, ValueError):
            port = 9050
        flags.append(f"--proxy-server=socks5://127.0.0.1:{port}")
        TOR_ACTIVE = True
    existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (existing + " " + " ".join(flags)).strip()


def port_open(port):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.5):
            return True
    except Exception:
        return False


BUILTIN_TRACKERS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com", "google-analytics.com",
    "googletagmanager.com", "googletagservices.com", "adservice.google.com", "facebook.net",
    "scorecardresearch.com", "quantserve.com", "hotjar.com", "hotjar.io", "mixpanel.com",
    "segment.io", "amplitude.com", "fullstory.com", "mouseflow.com", "crazyegg.com",
    "taboola.com", "outbrain.com", "criteo.com", "criteo.net", "adnxs.com", "rubiconproject.com",
    "pubmatic.com", "openx.net", "casalemedia.com", "advertising.com", "adsrvr.org",
    "bluekai.com", "demdex.net", "krxd.net", "exelator.com", "rlcdn.com", "2mdn.net",
    "moatads.com", "doubleverify.com", "adsafeprotected.com", "chartbeat.com",
    "ads-twitter.com", "analytics.twitter.com", "ads.linkedin.com", "analytics.tiktok.com",
    "ads.tiktok.com", "snap.licdn.com", "bat.bing.com", "clarity.ms", "mc.yandex.ru",
    "amazon-adsystem.com", "media.net", "yieldmo.com", "smartadserver.com", "tiqcdn.com",
}

TRACKING_PARAMS = {
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "mc_eid", "mc_cid", "igshid", "yclid",
    "_hsenc", "_hsmi", "wbraid", "gbraid", "twclid", "ttclid", "vero_id", "_openstat", "s_cid",
}
TRACKING_PREFIXES = ("utm_", "pk_", "mtm_", "hsa_", "oly_")


def is_tracking_param(key):
    k = unquote_plus(key).lower()
    return k in TRACKING_PARAMS or k.startswith(TRACKING_PREFIXES)


def clean_url(url_str):
    try:
        parts = urlsplit(url_str)
    except ValueError:
        return url_str
    if not parts.query:
        return url_str
    segments = [s for s in parts.query.split("&") if s]
    kept = [s for s in segments if not is_tracking_param(s.split("=", 1)[0])]
    if len(kept) == len(segments):
        return url_str
    return urlunsplit(parts._replace(query="&".join(kept)))


def parse_blocklist(lines):
    out = set()
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("!", "[")):
            continue
        if line.startswith("||"):
            rule = line[2:].split("^", 1)[0]
            if any(c in rule for c in "/*$"):
                continue
            host = rule
        else:
            parts = line.split()
            host = parts[-1] if parts[0] in ("0.0.0.0", "127.0.0.1") and len(parts) > 1 else parts[0]
        host = host.lower().strip(".")
        if host and "." in host and host != "0.0.0.0" and " " not in host:
            out.add(host)
    return out


class PrivacyState:
    LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}

    def __init__(self, settings=None):
        self.blocklist = set(BUILTIN_TRACKERS)
        self.blocked_count = 0
        self.blocked_hosts = {}
        self.upgraded = {}
        self.http_ok = set()
        self.cert_failed = set()
        self.update(settings or {})

    def update(self, settings):
        self.block_trackers = settings.get("block_trackers", True)
        self.https_only = settings.get("https_only", True)
        self.block_3p_cookies = settings.get("block_3p_cookies", True)
        self.strip_params = settings.get("strip_params", True)
        self.block_webgl = settings.get("block_webgl", False)
        self.allow_sites = set(settings.get("allow_sites", []))

    @staticmethod
    def _suffixes(host):
        parts = host.lower().strip(".").split(".")
        return [".".join(parts[i:]) for i in range(len(parts))]

    def is_tracker(self, host):
        return bool(host) and any(s in self.blocklist for s in self._suffixes(host))

    def site_allowed(self, host):
        return bool(host) and any(s in self.allow_sites for s in self._suffixes(host))

    def top_blocked(self, n=8):
        return sorted(self.blocked_hosts.items(), key=lambda kv: kv[1], reverse=True)[:n]

    def load_blocklist_file(self, path):
        try:
            if os.path.exists(path):
                with open(path, "r", errors="ignore") as f:
                    self.blocklist |= parse_blocklist(f)
        except Exception:
            pass


class PrivacyInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state

    def interceptRequest(self, info):
        st = self.state
        url = info.requestUrl()
        scheme = url.scheme()
        if scheme not in ("http", "https"):
            return
        host = url.host()
        first_host = info.firstPartyUrl().host()
        is_main = info.resourceType() == QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame

        if st.site_allowed(first_host or host):
            return

        if st.block_trackers and not is_main and st.is_tracker(host):
            st.blocked_count += 1
            st.blocked_hosts[host] = st.blocked_hosts.get(host, 0) + 1
            info.block(True)
            return

        is_get = bytes(info.requestMethod()) == b"GET"
        original = url.toString(QUrl.ComponentFormattingOption.FullyEncoded)
        target = QUrl(url)
        changed = False

        if (is_main and is_get and st.strip_params
                and info.navigationType() != QWebEngineUrlRequestInfo.NavigationType.NavigationTypeRedirect):
            cleaned = clean_url(original)
            if cleaned != original:
                target = QUrl(cleaned)
                changed = True

        if (st.https_only and scheme == "http" and is_get
                and host not in st.LOCAL_HOSTS and host not in st.http_ok):
            if is_main:
                st.upgraded[host] = target.toString(QUrl.ComponentFormattingOption.FullyEncoded)
            target.setScheme("https")
            if target.port() == 80:
                target.setPort(-1)
            changed = True

        if changed:
            info.redirect(target)
            return

        info.setHttpHeader(b"Sec-GPC", b"1")
        info.setHttpHeader(b"DNT", b"1")


def apply_web_settings(settings, block_webgl=False):
    A = QWebEngineSettings.WebAttribute
    for name, val in (
        ("DnsPrefetchEnabled", False),
        ("PluginsEnabled", False),
        ("JavascriptCanAccessClipboard", False),
        ("WebRTCPublicInterfacesOnly", True),
        ("HyperlinkAuditingEnabled", False),
        ("PlaybackRequiresUserGesture", True),
        ("AllowRunningInsecureContent", False),
        ("AllowGeolocationOnInsecureOrigins", False),
        ("ScreenCaptureEnabled", False),
        ("WebGLEnabled", not block_webgl),
    ):
        attr = getattr(A, name, None)
        if attr is None:
            continue
        try:
            settings.setAttribute(attr, val)
        except Exception:
            pass


def make_profile(parent, state):
    profile = QWebEngineProfile(parent)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
    profile.setHttpUserAgent(re.sub(r"\s?QtWebEngine/\S+", "", profile.httpUserAgent()))
    profile.setHttpAcceptLanguage("en-US,en;q=0.9")

    profile._interceptor = PrivacyInterceptor(state, profile)
    profile.setUrlRequestInterceptor(profile._interceptor)

    def cookie_filter(req):
        if not state.block_3p_cookies or not req.thirdParty:
            return True
        return state.site_allowed(req.firstPartyUrl.host())
    profile._cookie_filter = cookie_filter
    profile.cookieStore().setCookieFilter(cookie_filter)

    apply_web_settings(profile.settings(), state.block_webgl)
    return profile


class InternalPages:
    @staticmethod
    def css(theme):
        themes = {
            "dark": {"bg": "#121212", "card": "#1e1e1e", "txt": "#ffffff", "acc": "#0d6efd", "btn_hover": "#0a58ca"},
            "light": {"bg": "#f8f9fa", "card": "#ffffff", "txt": "#212529", "acc": "#0d6efd", "btn_hover": "#0a58ca"},
            "tnn": {"bg": "#050a05", "card": "#0a110a", "txt": "#00ff41", "acc": "#008f11", "btn_hover": "#00cc33"}
        }
        c = themes.get(theme, themes["dark"])
        return f"""
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: {c['bg']}; color: {c['txt']}; margin: 0; padding: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: {c['acc']}; }}
        a {{ color: {c['acc']}; }}
        .header {{ text-align: center; padding-bottom: 50px; border-bottom: 1px solid {c['acc']}; margin-bottom: 40px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
        .card {{ background: {c['card']}; padding: 25px; border-radius: 15px; border: 1px solid {c['acc']}; transition: transform 0.3s, box-shadow 0.3s; margin-bottom: 20px; }}
        .card:hover {{ transform: translateY(-8px); box-shadow: 0 12px 24px rgba(0,0,0,0.4); }}
        .btn {{ display: inline-block; padding: 12px 24px; background: {c['acc']}; color: white; text-decoration: none; border-radius: 8px; margin-top: 15px; font-weight: bold; border: none; cursor: pointer; transition: background 0.2s; }}
        .btn:hover {{ background: {c['btn_hover']}; }}
        .nav-bar {{ display: flex; justify-content: center; gap: 20px; margin-bottom: 30px; }}
        .nav-link {{ color: {c['txt']}; text-decoration: none; font-weight: bold; padding: 5px 10px; border-radius: 5px; }}
        .nav-link:hover {{ background: rgba(128,128,128,0.2); }}
        .badge {{ background: {c['acc']}; color: white; padding: 3px 10px; border-radius: 20px; font-size: 12px; float: right; }}
        input, textarea {{ width: 100%; padding: 10px; background: {c['bg']}; color: {c['txt']}; border: 1px solid {c['acc']}; border-radius: 5px; margin-top: 10px; box-sizing: border-box; }}
        .small {{ opacity: 0.75; font-size: 13px; }}
        """

    @staticmethod
    def get_home(data, info):
        return f"""
        <html><head><style>{InternalPages.css(data['settings']['theme'])}</style></head><body>
            <div class='header'>
                <h1>NAVI ULTIMATE</h1>
                <p>Welcome back to the decentralized web. Private by default: no history, no saved cookies, trackers blocked.</p>
                <div class='nav-bar'>
                    <a href='navi://home' class='nav-link'>Home</a>
                    <a href='navi://bookmarks' class='nav-link'>Bookmarks</a>
                    <a href='navi://pw' class='nav-link'>My Sites</a>
                    <a href='navi://extensions' class='nav-link'>Extensions</a>
                    <a href='navi://store' class='nav-link'>Store</a>
                    <a href='navi://settings' class='nav-link'>Settings</a>
                </div>
                <form onsubmit='var q=document.getElementById("q").value.trim(); if(q) window.location.href="navi://search/"+encodeURIComponent(q); return false;'>
                    <input id='q' placeholder='Search with {html.escape(info['engine'])} or enter a URL' autofocus>
                </form>
            </div>
            <div class='grid'>
                <div class='card'>
                    <h3>🪙 Navit Wallet</h3>
                    <p>Current Balance: <b>{data['navits']} Navits</b></p>
                    <p>You earn 1 Navit every minute you spend browsing.</p>
                    <a href='navi://store' class='btn'>Spend Navits</a>
                </div>
                <div class='card'>
                    <h3>🌐 TNN Site Manager</h3>
                    <p>You have <b>{len(data['sites'])}</b> active decentralized sites.</p>
                    <a href='navi://pw' class='btn'>Manage Sites</a>
                </div>
                <div class='card'>
                    <h3>🛡️ Protection</h3>
                    <p>Network: <b>{html.escape(info['mode'])}</b></p>
                    <p>Trackers blocked this session: <b>{info['blocked']}</b></p>
                    <p class='small'>Tracker blocking {info['trackers']} · HTTPS-only {info['https']} · 3rd-party cookies blocked {info['cookies']} · Tracking params stripped {info['params']}</p>
                    <a href='navi://settings' class='btn'>Privacy Settings</a>
                </div>
            </div>
        </body></html>
        """


class TOSDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser - Legal Terms")
        self.setFixedSize(600, 500)
        layout = QVBoxLayout()
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setHtml("""
            <h1 style='color: #dc3545;'>Legal Disclaimer</h1>
            <p><b>1. End-User Responsibility:</b> The user acknowledges that Navi Browser provides access to decentralized networks (TNN) and the Dark Web (Tor). The creator is <b>NOT</b> responsible for any content hosted, visited, or distributed via these networks.</p>
            <p><b>2. No Censorship:</b> TNN domains (.apples, .cops, .fav, etc.) are peer-to-peer. Content is stored on users' local machines. The creator has no power to remove content.</p>
            <p><b>3. Illegal Activity:</b> Any illegal activity performed while using Navi is the sole liability of the user.</p>
            <p><b>4. Data P2P:</b> Your IP address may be used to facilitate connections in TNN mode.</p>
            <hr>
            <p align='center'><i>Clicking "Accept" or simply using this app constitutes a binding agreement that you alone carry all legal liability.</i></p>
        """)
        layout.addWidget(self.content)
        self.btn = QPushButton("I Accept and Understand the Risks")
        self.btn.setStyleSheet("background: #28a745; color: white; padding: 15px; font-weight: bold; border-radius: 10px;")
        self.btn.clicked.connect(self.accept)
        layout.addWidget(self.btn)
        self.setLayout(layout)


class CodeEditor(QWidget):
    def __init__(self, main, mode="site", key=None):
        super().__init__()
        self.main, self.mode, self.key = main, mode, key
        self.setWindowTitle(f"Navi {mode.title()} Editor")
        self.resize(1000, 750)
        layout = QVBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter name/domain (e.g. awesome-site)")
        self.code_input = QPlainTextEdit()
        self.code_input.setPlaceholderText("Paste HTML, CSS, and JS here...")

        if key:
            self.title_input.setText(key)
            self.title_input.setReadOnly(True)
            src = main.data['sites' if mode == "site" else 'extensions'].get(key, {})
            self.code_input.setPlainText(src.get('html_content', src.get('code', '')))

        self.save_btn = QPushButton("🚀 Save & Deploy to Network")
        self.save_btn.setStyleSheet("background: #0d6efd; color: white; padding: 15px; font-weight: bold;")
        self.save_btn.clicked.connect(self.save_data_logic)

        layout.addWidget(QLabel("<b>Identity/Domain:</b>"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("<b>Source Code:</b>"))
        layout.addWidget(self.code_input)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

    def save_data_logic(self):
        name = self.title_input.text().strip()
        code = self.code_input.toPlainText()
        if not name or not code: return
        if self.mode == "site":
            if not any(name.endswith(tld) for tld in TNN_TLDS): name += ".pw-navi"
            self.main.data['sites'][name] = {"html_content": code, "public": True, "created": str(datetime.now())}
        else:
            self.main.data['extensions'][name] = {"code": code, "active": True}
        self.main.save_data()
        QMessageBox.information(self, "Success", f"{self.mode.title()} saved successfully!")
        self.close()


class NaviView(QWebEngineView):
    def createWindow(self, _type):
        return self.main.add_tab(None)


class NaviWebPage(QWebEnginePage):
    def __init__(self, profile, view):
        super().__init__(profile, view)
        self.view = view
        self.internal = False
        self.certificateError.connect(self._on_certificate_error)
        if hasattr(self, "permissionRequested"):
            self.permissionRequested.connect(lambda perm: perm.deny())
        else:
            self.featurePermissionRequested.connect(self._deny_feature)

    def _deny_feature(self, origin, feature):
        self.setFeaturePermission(origin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)

    def _on_certificate_error(self, error):
        try:
            self.view.main.state.cert_failed.add(error.url().host())
        except Exception:
            pass
        error.rejectCertificate()

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() in ["navi", "app"]:
            if isMainFrame and self.url().scheme() not in ("http", "https"):
                self.view.main.handle_cmd(
                    url.toString(QUrl.ComponentFormattingOption.FullyEncoded),
                    self.view, trusted=self.internal)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)


class NaviBrowser(QMainWindow):
    SAFE_CMDS = {"", "home", "pw", "extensions", "store", "settings", "bookmarks"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser Ultimate Elite")
        self.resize(1400, 900)

        self.data = {
            'sites': {}, 'extensions': {}, 'navits': 50, 'tos_agreed': False,
            'tnn_registry': {}, 'last_reward': 0, 'bookmarks': [],
            'settings': {
                'theme': 'dark', 'engine': DEFAULT_ENGINE, 'network_mode': 'cleanweb',
                'tor_port': 9050, 'block_trackers': True, 'https_only': True,
                'block_3p_cookies': True, 'strip_params': True, 'block_webgl': False,
                'allow_sites': []
            }
        }
        self.load_data()

        if not self.data.get('tos_agreed'):
            if TOSDialog().exec():
                self.data['tos_agreed'] = True
                self.save_data()
            else: sys.exit()

        self.state = PrivacyState(self.data['settings'])
        self.state.load_blocklist_file(BLOCKLIST_FILE)
        self.profile = make_profile(self, self.state)
        self.profile.downloadRequested.connect(self.on_download)

        self.setup_ui()
        self.apply_network_settings()
        self.add_tab(QUrl("navi://home"))

        self.shield_timer = QTimer(self)
        self.shield_timer.timeout.connect(self.update_shield)
        self.shield_timer.start(1000)
        QTimer.singleShot(600, self.warn_if_tor_down)

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)

        self.tb = QToolBar("Navigation")
        self.tb.setIconSize(QSize(18, 18))
        self.addToolBar(self.tb)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate)
        self.lock_label = QLabel("")

        back_btn = QAction("←", self); back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        next_btn = QAction("→", self); next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        reload_btn = QAction("↻", self); reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        home_btn = QAction("🏠", self); home_btn.triggered.connect(lambda: self.handle_cmd("navi://home", self.tabs.currentWidget()))
        new_tab_btn = QAction("+", self); new_tab_btn.triggered.connect(lambda: self.add_tab(QUrl("navi://home")))
        star_btn = QAction("☆", self); star_btn.setToolTip("Bookmark this page (Ctrl+D)"); star_btn.triggered.connect(self.add_bookmark)
        panic_btn = QAction("🧹", self); panic_btn.setToolTip("Clear cookies and cache, close extra tabs (Ctrl+Shift+Del)"); panic_btn.triggered.connect(self.panic)
        self.shield = QAction("🛡 0", self)
        self.shield.triggered.connect(self.toggle_site_protection)

        self.tb.addAction(back_btn); self.tb.addAction(next_btn); self.tb.addAction(reload_btn); self.tb.addAction(home_btn)
        self.tb.addWidget(self.lock_label)
        self.tb.addWidget(self.url_bar)
        self.tb.addAction(star_btn)
        self.tb.addAction(self.shield)
        self.tb.addAction(panic_btn)
        self.tb.addAction(new_tab_btn)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.update_styles()
        self.setup_shortcuts()

    def setup_shortcuts(self):
        def bind(keys, fn):
            act = QAction(self)
            act.setShortcut(QKeySequence(keys))
            act.triggered.connect(lambda: fn())
            self.addAction(act)

        def current(fn):
            def run():
                v = self.tabs.currentWidget()
                if v is not None:
                    fn(v)
            return run

        bind("Ctrl+T", lambda: self.add_tab(QUrl("navi://home")))
        bind("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex()))
        bind("Ctrl+L", self.focus_url_bar)
        bind("Ctrl+F", self.find_in_page)
        bind("Ctrl+D", self.add_bookmark)
        bind("Ctrl+R", current(lambda v: v.reload()))
        bind("F5", current(lambda v: v.reload()))
        bind("Alt+Left", current(lambda v: v.back()))
        bind("Alt+Right", current(lambda v: v.forward()))
        bind("Ctrl+=", lambda: self.zoom(0.1))
        bind("Ctrl++", lambda: self.zoom(0.1))
        bind("Ctrl+-", lambda: self.zoom(-0.1))
        bind("Ctrl+0", lambda: self.zoom(None))
        bind("Ctrl+Tab", lambda: self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count()))
        bind("Ctrl+Shift+Tab", lambda: self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % self.tabs.count()))
        bind("Ctrl+Shift+Delete", self.panic)

    def update_styles(self):
        self.setStyleSheet(BrowserStyles.get(self.data['settings']['theme']))

    def on_tab_changed(self, i):
        v = self.tabs.widget(i)
        if v is not None:
            self.url_bar.setText(v.url().toString())

    def focus_url_bar(self):
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    def find_in_page(self):
        v = self.tabs.currentWidget()
        if v is None:
            return
        text, ok = QInputDialog.getText(self, "Find in page", "Find:")
        if ok:
            v.findText(text)

    def zoom(self, delta):
        v = self.tabs.currentWidget()
        if v is None:
            return
        v.setZoomFactor(1.0 if delta is None else max(0.25, min(5.0, v.zoomFactor() + delta)))

    def update_shield(self):
        v = self.tabs.currentWidget()
        url = v.url() if v is not None else None
        host = url.host() if url is not None else ""
        scheme = url.scheme() if url is not None else ""
        off = self.state.site_allowed(host)
        self.shield.setText(f"🛡 {self.state.blocked_count}" + (" off" if off else ""))
        self.shield.setToolTip(
            f"{self.state.blocked_count} trackers blocked this session.\n"
            + ("Protection is OFF for this site. Click to turn it back on." if off
               else "Click to turn protection off for this site (use if a site breaks).")
        )
        if scheme == "https":
            self.lock_label.setText("🔒")
            self.lock_label.setToolTip("Connection is encrypted (HTTPS)")
        elif scheme == "http":
            self.lock_label.setText("⚠")
            self.lock_label.setToolTip("Connection is NOT encrypted (HTTP)")
        else:
            self.lock_label.setText("")
            self.lock_label.setToolTip("")

    def toggle_site_protection(self):
        v = self.tabs.currentWidget()
        host = v.url().host() if v is not None else ""
        if not host:
            self.status.showMessage("Open a website first.", 3000)
            return
        allow = self.data['settings'].setdefault('allow_sites', [])
        match = next((e for e in allow if host == e or host.endswith("." + e)), None)
        if match:
            allow.remove(match)
            self.status.showMessage(f"Protection ON for {match}", 4000)
        else:
            allow.append(host)
            self.status.showMessage(f"Protection OFF for {host}", 4000)
        self.save_data()
        self.apply_privacy_settings()
        v.reload()
        self.update_shield()

    def apply_privacy_settings(self):
        self.state.update(self.data['settings'])
        apply_web_settings(self.profile.settings(), self.state.block_webgl)
        for i in range(self.tabs.count()):
            apply_web_settings(self.tabs.widget(i).page().settings(), self.state.block_webgl)

    def clear_site_data(self):
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.profile.clearAllVisitedLinks()

    def panic(self):
        self.clear_site_data()
        while self.tabs.count() > 1:
            self.close_tab(self.tabs.count() - 1)
        self.tabs.setCurrentIndex(0)
        self.handle_cmd("navi://home", self.tabs.widget(0))
        self.status.showMessage("Cookies and cache cleared, extra tabs closed.", 5000)

    def on_download(self, download):
        name = ""
        suggested = getattr(download, "suggestedFileName", None)
        if callable(suggested):
            name = suggested()
        if not name:
            name = download.downloadFileName() or "download"
        start = os.path.join(os.path.expanduser("~/Downloads"), name)
        path, _ = QFileDialog.getSaveFileName(self, "Save download", start)
        if not path:
            download.cancel()
            return
        if path.lower().endswith(RISKY_EXTENSIONS):
            answer = QMessageBox.question(
                self, "Risky file",
                f"{os.path.basename(path)} can run code on your computer. Download it anyway?")
            if answer != QMessageBox.StandardButton.Yes:
                download.cancel()
                return
        download.setDownloadDirectory(os.path.dirname(path))
        download.setDownloadFileName(os.path.basename(path))
        download.accept()
        self.status.showMessage(f"Downloading {os.path.basename(path)}...", 4000)
        try:
            download.isFinishedChanged.connect(
                lambda: self.status.showMessage(f"Download finished: {os.path.basename(path)}", 6000))
        except Exception:
            pass

    def add_bookmark(self):
        v = self.tabs.currentWidget()
        if v is None:
            return
        u = v.url()
        if u.scheme() not in ("http", "https"):
            self.status.showMessage("Only websites can be bookmarked.", 3000)
            return
        url = u.toString()
        marks = self.data.setdefault('bookmarks', [])
        if any(isinstance(b, dict) and b.get('url') == url for b in marks):
            self.status.showMessage("Already bookmarked.", 3000)
            return
        marks.append({"title": v.page().title() or u.host(), "url": url})
        self.save_data()
        self.status.showMessage("Bookmarked.", 3000)

    def add_tab(self, url):
        view = NaviView()
        view.main = self
        view.setPage(NaviWebPage(self.profile, view))
        apply_web_settings(view.page().settings(), self.state.block_webgl)
        view.urlChanged.connect(lambda q: self.url_bar.setText(q.toString()) if view == self.tabs.currentWidget() else None)
        view.loadStarted.connect(lambda: self.status.showMessage("Loading..."))
        view.loadFinished.connect(lambda ok: self.on_load_finish(view, ok))
        idx = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(idx)
        if url is not None:
            view.setUrl(url if isinstance(url, QUrl) else QUrl(url))
        return view

    def close_tab(self, i):
        if self.tabs.count() > 1:
            w = self.tabs.widget(i)
            self.tabs.removeTab(i)
            if w is not None:
                w.deleteLater()

    def on_load_finish(self, view, ok=True):
        if not ok:
            self.status.showMessage("Load failed", 4000)
            self.offer_http_fallback(view)
            return
        self.status.showMessage("Ready", 3000)
        title = view.page().title() or view.url().host() or "New Tab"
        self.tabs.setTabText(self.tabs.indexOf(view), title[:15])
        for ext in self.data['extensions'].values():
            if ext.get('active'): view.page().runJavaScript(ext['code'])
        if time.time() - self.data['last_reward'] > 60:
            self.data['navits'] += 1
            self.data['last_reward'] = time.time()
            self.save_data()

    def offer_http_fallback(self, view):
        u = view.url()
        host, st = u.host(), self.state
        if (u.scheme() == "https" and host in st.upgraded
                and host not in st.http_ok and host not in st.cert_failed):
            body = (
                "<h1>Couldn't connect securely</h1>"
                f"<p><b>{html.escape(host)}</b> didn't load over HTTPS. Continuing over plain HTTP means "
                "anyone on the network can read or change what you send and receive.</p>"
                f"<a href='navi://allowhttp/{quote(host, safe='')}' class='btn'>Continue over HTTP</a> "
                "<a href='navi://home' class='btn'>Go home</a>"
            )
            self.show_internal(view, self.wrap(body))

    def navigate(self):
        self.open_text(self.url_bar.text().strip(), self.tabs.currentWidget())

    def open_text(self, text, view):
        if not text or view is None: return
        if text.startswith("navi://") or text.startswith("app://"):
            self.handle_cmd(text, view); return

        found_tld = next((tld for tld in TNN_TLDS if text.endswith(tld)), None)
        if found_tld:
            target = text
            if found_tld in TLD_ALIASES:
                alt = text.replace(found_tld, TLD_ALIASES[found_tld])
                if alt in self.data['sites']: target = alt
            if target in self.data['sites']:
                view.page().internal = False
                view.setHtml(self.data['sites'][target]['html_content'])
                return

        host_part = text.split("/")[0].split(":")[0]
        if " " not in text and "://" in text:
            url = text
        elif " " not in text and host_part == "localhost":
            url = "http://" + text
        elif "." not in text or " " in text:
            url = get_search_url(self.data['settings']['engine'], text)
        else:
            url = "https://" + text
        view.page().internal = False
        view.setUrl(QUrl(url))

    def wrap(self, body):
        return f"<html><head><style>{InternalPages.css(self.data['settings']['theme'])}</style></head><body>{body}</body></html>"

    def show_internal(self, view, page_html):
        view.page().internal = True
        view.setHtml(page_html)

    def privacy_summary(self):
        s, st = self.data['settings'], self.state
        wants_tor = s.get('network_mode') == 'tor'
        if TOR_ACTIVE and wants_tor:
            mode = "TOR"
        elif TOR_ACTIVE:
            mode = "TOR (restart to leave Tor)"
        elif wants_tor:
            mode = "DIRECT (restart to switch to Tor)"
        else:
            mode = s.get('network_mode', 'cleanweb').upper()
        onoff = lambda b: "ON" if b else "OFF"
        return {"mode": mode, "blocked": st.blocked_count, "trackers": onoff(st.block_trackers),
                "https": onoff(st.https_only), "cookies": onoff(st.block_3p_cookies),
                "params": onoff(st.strip_params), "engine": s.get('engine', DEFAULT_ENGINE)}

    def bookmarks_page(self):
        marks = [b for b in self.data.get('bookmarks', []) if isinstance(b, dict) and b.get('url')]
        cards = "".join(
            f"<div class='card'><h3>{html.escape(b.get('title') or b['url'])}</h3>"
            f"<p class='small'>{html.escape(b['url'])}</p>"
            f"<a href='{html.escape(b['url'], quote=True)}' class='btn'>Open</a> "
            f"<a href='navi://bm/remove/{quote(b['url'], safe='')}' class='btn'>Remove</a></div>"
            for b in marks) or "<p class='small'>No bookmarks yet. Press Ctrl+D or the ☆ button on a page.</p>"
        return self.wrap(f"<h1>Bookmarks</h1><div class='grid'>{cards}</div>")

    def settings_page(self):
        s, st = self.data['settings'], self.state
        engines = "".join(
            f"<option{' selected' if s['engine'] == e else ''}>{html.escape(e)}</option>" for e in ALL_ENGINES)

        def toggle(key, label, default=True):
            on = s.get(key, default)
            return (f"<p>{label}: <b>{'ON' if on else 'OFF'}</b> "
                    f"<a href='navi://set/toggle/{key}' class='btn'>Turn {'off' if on else 'on'}</a></p>")

        modes = " ".join(
            f"<a href='navi://set/mode/{m}' class='btn'>{label}{' ✓' if s['network_mode'] == m else ''}</a>"
            for m, label in (("cleanweb", "Direct"), ("tnn", "TNN"), ("tor", "Tor")))
        ports = " ".join(
            f"<a href='navi://set/port/{p}' class='btn'>{p}{' ✓' if int(s.get('tor_port', 9050)) == p else ''}</a>"
            for p in (9050, 9150))
        allowed = "".join(
            f"<p>{html.escape(h)} <a href='navi://site/remove/{quote(h, safe='')}'>remove</a></p>"
            for h in sorted(st.allow_sites)) or "<p class='small'>None. Use the 🛡 button in the toolbar to switch protection off for a site.</p>"
        top = "".join(
            f"<p>{html.escape(h)} <span class='small'>blocked {n}×</span></p>" for h, n in st.top_blocked()
        ) or "<p class='small'>Nothing blocked yet this session.</p>"

        body = (
            "<h1>Global Settings</h1>"
            "<div class='card'><h3>Search Engine</h3>"
            "<select id='engine' onchange='window.location.href=\"navi://set/engine/\" + encodeURIComponent(this.value)'>"
            f"{engines}</select></div>"
            "<div class='card'><h3>Theme</h3><a href='navi://set/theme/dark' class='btn'>Dark</a> "
            "<a href='navi://set/theme/light' class='btn'>Light</a> <a href='navi://set/theme/tnn' class='btn'>TNN Neon</a></div>"
            "<div class='card'><h3>🛡️ Privacy</h3>"
            + toggle('block_trackers', 'Block trackers and ads')
            + toggle('https_only', 'HTTPS-only (upgrade http:// links)')
            + toggle('block_3p_cookies', 'Block third-party cookies')
            + toggle('strip_params', 'Strip tracking parameters from links (utm_*, fbclid, gclid...)')
            + toggle('block_webgl', 'Block WebGL (reduces fingerprinting, breaks 3D sites)', False)
            + f"<p class='small'>Blocklist: {len(st.blocklist)} domains. Add more by putting a hosts-format or "
              f"one-domain-per-line list at <code>{html.escape(BLOCKLIST_FILE)}</code> and restarting.</p>"
              "<p class='small'>Navi keeps no history, and cookies are never saved to disk. Permission requests "
              "(camera, mic, location, notifications) are always denied. Autoplay needs a click.</p></div>"
            "<div class='card'><h3>Most blocked this session</h3>" + top + "</div>"
            "<div class='card'><h3>Clear data</h3>"
            "<p class='small'>Removes cookies and cache held in memory right now. Shortcut: Ctrl+Shift+Delete also closes extra tabs.</p>"
            "<a href='navi://clear' class='btn'>Clear cookies &amp; cache now</a></div>"
            "<div class='card'><h3>Network</h3>" + modes +
            "<p class='small'>Tor mode sends all traffic through a local Tor SOCKS proxy (nothing loads if Tor isn't "
            "running). Switching needs a restart. This hides your IP, but Navi's own browser fingerprint is not "
            "disguised the way Tor Browser's is, so don't rely on it for anonymity.</p>"
            "<p>Tor port: " + ports + " <span class='small'>(9050 = Tor service, 9150 = Tor Browser)</span></p></div>"
            "<div class='card'><h3>Sites with protection off</h3>" + allowed + "</div>"
        )
        return self.wrap(body)

    def handle_cmd(self, url_str, view, trusted=True):
        cmd = url_str.replace("navi://", "").replace("app://", "").strip("/")
        if not trusted and cmd not in self.SAFE_CMDS:
            self.status.showMessage("Blocked: that page isn't allowed to run Navi commands.", 5000)
            return
        arg = unquote(cmd.split("/")[-1])
        s = self.data['settings']

        if cmd in ["home", ""]:
            self.show_internal(view, InternalPages.get_home(self.data, self.privacy_summary()))

        elif cmd.startswith("search/"):
            self.open_text(arg, view)

        elif cmd == "bookmarks":
            self.show_internal(view, self.bookmarks_page())

        elif cmd.startswith("bm/remove/"):
            marks = self.data.get('bookmarks', [])
            self.data['bookmarks'] = [b for b in marks if not (isinstance(b, dict) and b.get('url') == arg)]
            self.save_data()
            self.handle_cmd("navi://bookmarks", view)

        elif cmd == "pw":
            cards = "".join(
                f"<div class='card'><span class='badge'>TNN</span><h3>{html.escape(k)}</h3><p>Online & Decentralized</p>"
                f"<a href='navi://pw/edit/{quote(k, safe='')}' class='btn'>Edit Source</a></div>"
                for k in self.data['sites'])
            self.show_internal(view, self.wrap(
                f"<h1>Site Manager</h1><a href='navi://pw/new' class='btn'>+ Create New TNN Site</a>"
                f"<div class='grid' style='margin-top:20px;'>{cards}</div>"))

        elif cmd == "pw/new":
            self.editor = CodeEditor(self, "site")
            self.editor.show()

        elif cmd.startswith("pw/edit/"):
            self.editor = CodeEditor(self, "site", arg)
            self.editor.show()

        elif cmd == "extensions":
            ext_list = "".join(
                f"<div class='card'><h3>{html.escape(k)}</h3><p>Status: {'Active' if v.get('active') else 'Inactive'}</p>"
                f"<a href='navi://ext/toggle/{quote(k, safe='')}' class='btn'>Toggle</a></div>"
                for k, v in self.data['extensions'].items())
            self.show_internal(view, self.wrap(
                f"<h1>Extension Lab</h1><a href='navi://ext/new' class='btn'>+ New Extension</a><div class='grid'>{ext_list}</div>"))

        elif cmd == "ext/new":
            self.editor = CodeEditor(self, "extension")
            self.editor.show()

        elif cmd.startswith("ext/toggle/"):
            if arg in self.data['extensions']:
                ext = self.data['extensions'][arg]
                ext['active'] = not ext.get('active')
                self.save_data()
            self.handle_cmd("navi://extensions", view)

        elif cmd == "store":
            items = "".join(
                f"<div class='card'><h3>{tld}</h3><p>Cost: 30 Navits</p><p>Secure decentralized TLD.</p>"
                f"<a href='navi://buy/{tld}' class='btn'>Register</a></div>"
                for tld in TNN_TLDS if tld != ".pw-navi")
            self.show_internal(view, self.wrap(f"<h1>Domain Registry</h1><div class='grid'>{items}</div>"))

        elif cmd.startswith("buy/"):
            tld = "." + arg.strip(".")
            if tld not in TNN_TLDS:
                return
            if self.data['navits'] >= 30:
                name, ok = QInputDialog.getText(self, "Register Domain", f"Choose your {tld} domain name:")
                name = (name or "").strip().lower()
                if ok and name:
                    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*", name):
                        QMessageBox.warning(self, "Invalid name", "Use only letters, numbers, dots and dashes.")
                        return
                    full = name + tld
                    if full in self.data['sites']:
                        QMessageBox.warning(self, "Taken", f"{full} is already registered.")
                        return
                    self.data['navits'] -= 30
                    self.data['sites'][full] = {"html_content": f"<h1>Welcome to {html.escape(full)}</h1>", "public": True}
                    self.save_data()
                    self.handle_cmd("navi://home", view)
            else:
                QMessageBox.warning(self, "Insufficient Funds", "You need 30 Navits to buy a TNN domain!")

        elif cmd == "settings":
            self.show_internal(view, self.settings_page())

        elif cmd == "clear":
            self.clear_site_data()
            self.status.showMessage("Cookies and cache cleared.", 4000)
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("set/theme/"):
            if arg in ("dark", "light", "tnn"):
                s['theme'] = arg
                self.update_styles(); self.save_data()
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("set/engine/"):
            if arg in ALL_ENGINES:
                s['engine'] = arg
                self.save_data()
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("set/toggle/"):
            if arg in PRIVACY_TOGGLES:
                s[arg] = not s.get(arg, arg != "block_webgl")
                self.apply_privacy_settings()
                self.save_data()
                if arg == "block_webgl":
                    self.status.showMessage("Reload open tabs for the WebGL change to apply.", 5000)
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("set/mode/"):
            if arg in ("cleanweb", "tnn", "tor"):
                old = s.get('network_mode')
                s['network_mode'] = arg
                self.save_data()
                self.apply_network_settings()
                if old != arg and "tor" in (old, arg):
                    QMessageBox.information(self, "Restart needed",
                                            "Restart Navi for the Tor setting to take effect.")
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("set/port/"):
            if arg.isdigit() and 1 <= int(arg) <= 65535:
                s['tor_port'] = int(arg)
                self.save_data()
                if s.get('network_mode') == 'tor':
                    QMessageBox.information(self, "Restart needed", "Restart Navi to use the new Tor port.")
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("site/remove/"):
            allow = s.setdefault('allow_sites', [])
            if arg in allow:
                allow.remove(arg)
                self.apply_privacy_settings()
                self.save_data()
            self.handle_cmd("navi://settings", view)

        elif cmd.startswith("allowhttp/"):
            if arg in self.state.upgraded:
                self.state.http_ok.add(arg)
                view.page().internal = False
                view.setUrl(QUrl(self.state.upgraded[arg]))

    def warn_if_tor_down(self):
        if TOR_ACTIVE:
            try:
                port = int(self.data['settings'].get('tor_port', 9050))
            except (TypeError, ValueError):
                port = 9050
            if not port_open(port):
                QMessageBox.warning(
                    self, "Tor not running",
                    f"Tor mode is on, but nothing is listening on 127.0.0.1:{port}.\n\n"
                    "Pages will fail to load. That's on purpose, so your traffic never leaves Tor.\n"
                    "Start Tor (or Tor Browser, which uses port 9150), or switch back to Direct in Settings and restart.")

    def apply_network_settings(self):
        if self.data['settings']['network_mode'] == "tnn":
            ip = get_local_ip()
            for d, info in self.data['sites'].items():
                if info.get('public'):
                    if d not in self.data['tnn_registry']: self.data['tnn_registry'][d] = []
                    if ip not in self.data['tnn_registry'][d]: self.data['tnn_registry'][d].append(ip)

    def load_data(self):
        for path in (DATA_FILE, LEGACY_DATA_FILE):
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        saved = json.load(f)
                    settings = saved.pop('settings', {})
                    self.data.update(saved)
                    self.data['settings'].update(settings)
                    break
                except Exception:
                    continue
        self.data['settings'].pop('user_agent', None)

    def save_data(self):
        tmp = DATA_FILE + ".tmp"
        try:
            with open(tmp, 'w') as f:
                json.dump(self.data, f)
            os.replace(tmp, DATA_FILE)
        except OSError as e:
            if hasattr(self, "status"):
                self.status.showMessage(f"Couldn't save settings: {e}", 5000)


class BrowserStyles:
    @staticmethod
    def get(theme):
        themes = {
            "dark": {"bg": "#121212", "fg": "#ffffff", "acc": "#0d6efd", "bar": "#1e1e1e", "tab": "#2b2b2b"},
            "light": {"bg": "#f8f9fa", "fg": "#212529", "acc": "#0d6efd", "bar": "#ffffff", "tab": "#e9ecef"},
            "tnn": {"bg": "#050a05", "fg": "#00ff41", "acc": "#008f11", "bar": "#0a110a", "tab": "#0d1a0d"}
        }
        c = themes.get(theme, themes["dark"])
        return f"""
        QMainWindow {{ background-color: {c['bg']}; }}
        QToolBar {{ background: {c['bar']}; border-bottom: 2px solid {c['acc']}; padding: 10px; spacing: 15px; }}
        QToolBar QLabel {{ color: {c['fg']}; font-size: 16px; }}
        QLineEdit {{ background: {c['bg']}; color: {c['fg']}; border: 1px solid {c['acc']}; border-radius: 18px; padding: 8px 18px; font-size: 14px; }}
        QTabWidget::pane {{ border: none; }}
        QTabBar::tab {{ background: {c['tab']}; color: {c['fg']}; padding: 12px 25px; border-top-left-radius: 12px; border-top-right-radius: 12px; margin-right: 3px; font-weight: bold; }}
        QTabBar::tab:selected {{ background: {c['acc']}; color: white; }}
        QStatusBar {{ background: {c['bar']}; color: {c['fg']}; font-size: 12px; }}
        """


if __name__ == '__main__':
    configure_chromium(read_saved_settings())
    app = QApplication(sys.argv)
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec())
