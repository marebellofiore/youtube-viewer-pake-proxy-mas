import sys
from PyQt5.QtCore import QUrl, QTimer, Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtNetwork import QNetworkProxy

class MiniBrowser(QMainWindow):
    def __init__(self, headless_mode):
        super().__init__()

        # Baca konfigurasi
        self.proxy_list = self.load_proxies('local_proxies.txt')
        self.url_list = self.load_urls('url.txt')
        self.num_tabs = self.load_num_tabs('tab.txt')
        self.play_interval = self.load_play_interval('play.txt')  # Interval dari file play.txt
        self.current_proxy_index = 0  # Indeks proxy yang digunakan

        # Setup window
        self.setWindowTitle("Mini Browser with Proxy Rotation")
        self.setGeometry(200, 200, 800, 600)

        if headless_mode:
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.setWindowOpacity(0)
            QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.handle_tab_close)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Load initial tabs
        self.tab_timers = {}  # Timer untuk auto-close
        for i in range(self.num_tabs):
            self.add_new_tab(self.url_list[i % len(self.url_list)], self.get_next_proxy())

    def load_proxies(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read().splitlines()
        except FileNotFoundError:
            print(f"File {file_path} not found. No proxy will be used.")
            return []

    def load_urls(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return file.read().splitlines()
        except FileNotFoundError:
            print(f"File {file_path} not found. Using default URL.")
            return ["http://youtube.com"]

    def load_num_tabs(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return int(file.read().strip())
        except (FileNotFoundError, ValueError):
            print(f"File {file_path} not found or invalid. Defaulting to 1 tab.")
            return 1

    def load_play_interval(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return int(file.read().strip())
        except (FileNotFoundError, ValueError):
            print(f"File {file_path} not found or invalid. Defaulting to 600 seconds.")
            return 600

    def get_next_proxy(self):
        """Mengembalikan proxy berikutnya dari daftar, dengan rotasi."""
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy

    def add_new_tab(self, url, proxy=None):
        print(f"Adding new tab: {url} with proxy: {proxy}")
        browser = QWebEngineView()

        if proxy:
            proxy_parts = proxy.split(':')
            if len(proxy_parts) == 2:
                host, port = proxy_parts[0], int(proxy_parts[1])
                network_proxy = QNetworkProxy(QNetworkProxy.HttpProxy, host, port)
                QNetworkProxy.setApplicationProxy(network_proxy)
                print(f"Using proxy {proxy} for this tab.")

        browser.setUrl(QUrl(url))
        browser.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        browser.page().loadFinished.connect(lambda: self.force_video_quality(browser))

        index = self.tabs.addTab(browser, url)
        self.tabs.setCurrentIndex(index)

        # Atur timer untuk menutup tab otomatis
        self.setup_auto_close_timer(url)

    def setup_auto_close_timer(self, url):
        """Set up timer untuk menutup tab secara otomatis."""
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.auto_close_tab(url))
        timer.start(self.play_interval * 1000)  # Interval dalam milidetik
        self.tab_timers[url] = timer
        print(f"Timer untuk tab {url} diatur selama {self.play_interval} detik.")

    def auto_close_tab(self, url):
        """Menutup tab secara otomatis dan membuka kembali dengan proxy baru."""
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == url:
                print(f"Menutup tab {url} secara otomatis.")
                self.tabs.removeTab(i)

                # Dapatkan proxy baru dan buka kembali tab
                proxy = self.get_next_proxy()
                reopen_timer = QTimer(self)
                reopen_timer.setSingleShot(True)
                reopen_timer.timeout.connect(lambda: self.add_new_tab(url, proxy))
                reopen_timer.start(self.play_interval * 1000)
                self.tab_timers[url] = reopen_timer
                print(f"Tab {url} akan dibuka kembali dengan proxy baru setelah {self.play_interval} detik.")
                break

    def force_video_quality(self, browser):
        js_script = """
        var interval = setInterval(function() {
            var player = document.querySelector('video');
            if (player) {
                player.setPlaybackQualityRange && player.setPlaybackQualityRange("small");
                clearInterval(interval);
            }
        }, 1000);
        """
        browser.page().runJavaScript(js_script)
        print("Injected JavaScript to force video quality to 144p.")

    def handle_tab_close(self, index):
        """Handle jika tab ditutup secara manual."""
        url = self.tabs.tabText(index)
        self.tabs.removeTab(index)
        print(f"Tab {url} ditutup secara manual.")

def read_headless_config():
    try:
        with open('headless.txt', 'r') as file:
            return file.read().strip().lower() == 'true'
    except FileNotFoundError:
        print("headless.txt not found. Defaulting to normal mode.")
        return False

if __name__ == "__main__":
    headless_mode = read_headless_config()

    app = QApplication(sys.argv)
    browser = MiniBrowser(headless_mode)

    if not headless_mode:
        browser.show()

    sys.exit(app.exec_())
