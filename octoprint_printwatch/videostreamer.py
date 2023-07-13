from urllib.request import urlopen
from typing import Union

class VideoStreamer():
    def __init__(self, plugin):
        self.plugin = plugin


    def grab_frame(self) -> Union[bool, bytes]:
        url = self.plugin._settings.get(["stream_url"])
        try:
            if not url.endswith('stream'):
                snap_preview = urlopen(url, timeout=10)
                if self.plugin._settings.get(["enable_detector"]):
                    if snap_preview.status == 200:
                        return snap_preview.read()
            self.plugin._logger.info("Issue with the stream url input.")
            return False
        except Exception as e:
            self.plugin._logger.info("Issue acquiring frame from URL provided: {}".format(str(e)))
            return False
