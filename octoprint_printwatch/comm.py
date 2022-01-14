import octoprint.plugin
from urllib.request import Request, urlopen
from socket import gethostbyname, gethostname
from time import time, sleep
from threading import Lock
from json import loads, dumps
from base64 import b64encode
from uuid import uuid4

DEFAULT_ROUTE = 'http://printwatch-printpal.pythonanywhere.com'

class CommManager(octoprint.plugin.SettingsPlugin):
    def __init__(self, plugin):
        self.plugin = plugin
        self.parameters = {
                            'last_t' : 0.0,
                            'ip' : gethostbyname(gethostname()),
                            'route' : DEFAULT_ROUTE,
                            'nms' : False,
                            'id' : self.plugin._settings.global_get(["accessControl", "salt"]) if self.plugin._settings.global_get(["accessControl", "salt"]) is not None else uuid4().hex,
                            'bad_responses' : 0
                            }

    def email_notification(self):
        if self.plugin._settings.get(["enable_email_notification"]):
            self.parameters['nms'] = True
            sleep(self.plugin.inferencer.REQUEST_INTERVAL)
            self.send_request()
            self.plugin._logger.info("Email notification sent to {}".format(self.plugin._settings.get(["email_addr"])))

    def send_request(self):
        with Lock():
            image = b64encode(bytearray(self.plugin.streamer.jpg)).decode('utf8')
        inference_request = Request('{}/inference/'.format(
            self.parameters['route']),
            data=self._create_payload(image),
            method='POST'
        )

        try:
            response = loads(urlopen(inference_request).read())
            if response['statusCode'] == 200:
                self.plugin.inferencer.pred = eval(response['defect_detected'])
                self.parameters['bad_responses'] = 0
                self.plugin.inferencer.REQUEST_INTERVAL = 10.0
            elif response['statusCode'] == 213:
                self.plugin.inferencer.REQUEST_INTERVAL= 300.0
            else:
                self.plugin.inferencer.pred = False
                self.parameters['bad_responses'] += 1

        except Exception as e:
            self.plugin._logger.info("Error retrieving server response: {}".format(str(e)))
            self.parameters['bad_responses'] += 1
            self.plugin.inferencer.pred = False
        self.parameters['last_t'] = time()


    def _create_payload(self, image):
        return dumps({
                            'image_array' : image,
                            'settings' : self.plugin._settings.get([]),
                            'parameters' : self.parameters,
                            'job' : self.plugin._printer.get_current_job(),
                            'data' : self.plugin._printer.get_current_data()
                            }).encode('utf8')
