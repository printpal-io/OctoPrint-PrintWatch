import octoprint.plugin
from threading import Thread
from urllib.request import urlopen
import ssl
from time import sleep

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


class VideoStreamer(octoprint.plugin.SettingsPlugin):
    def __init__(self, plugin):
        self.plugin = plugin
        self.bytes = b''
        self.image = None
        self.a = -1
        self.b = -1
        self.stream_enabled = False
        self.stream = None
        self.queue = None
        self.jpg = None


    def start_service(self):
        if self.stream is None:
            try:
                self.stream = urlopen(self.plugin._settings.get(["stream_url"]), context = CTX)
                self.stream_enabled = True
                self.queue = Thread(target=self._frame_queue)
                self.queue.daemon = True
                self.queue.start()
                self.plugin._logger.info("PrintWatch stream opened successfully [url: {}, status: {}]".format(self.plugin._settings.get(["stream_url"]), self.stream.status))
            except:
                self.stream_enabled = False
                self.plugin._logger.info("PrintWatch stream failed to open [{}]".format(self.plugin._settings.get(["stream_url"])))

    def kill_service(self):
        self.stream_enabled =False
        self.queue = None
        self.stream = None
        self.plugin._logger.info("PrintWatch stream closed")


    def _frame_queue(self):
        self.plugin._logger.info("PrintWatch stream starting...")
        while self.stream_enabled and self.plugin._settings.get(["enable_detector"]):
            if self.stream.status == 200:
                sleep(0.1) #prevent cpu overload
                self.bytes += self.stream.read(262144)
                self.b = self.bytes.rfind(b'\xff\xd9')
                self.a = self.bytes.rfind(b'\xff\xd8', 0, self.b)
                if self.a != -1 and self.b != -1:
                    self.jpg = self.bytes[self.a:self.b+2]
                    self.bytes = self.bytes[self.b+2:]

            else:
                self.stream = urlopen(self.plugin._settings.get(["stream_url"]), context = CTX)
