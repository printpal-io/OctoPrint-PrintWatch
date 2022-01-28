import octoprint.plugin
from urllib.request import Request, urlopen
from socket import gethostbyname, gethostname
from time import time, sleep
from threading import Lock
from json import loads, dumps
from base64 import b64encode
from uuid import uuid4
import io
import PIL.Image as Image
from PIL import ImageDraw
import re


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


    def _create_payload(self, image):
        settings = self.plugin._settings.get([])
        if not "confidence" in settings:
            settings["confidence"] = 60
        return dumps({
                            'image_array' : image,
                            'settings' : settings,
                            'parameters' : self.parameters,
                            'job' : self.plugin._printer.get_current_job(),
                            'data' : self.plugin._printer.get_current_data()
                            }).encode('utf8')


    def email_notification(self):
        if self.plugin._settings.get(["enable_email_notification"]):
            self.parameters['nms'] = True
            sleep(self.plugin.inferencer.REQUEST_INTERVAL)
            self.send_request()
            self.plugin._logger.info("Email notification sent to {}".format(self.plugin._settings.get(["email_addr"])))

    def send_request(self):
        with Lock():
            self.image = bytearray(self.plugin.streamer.jpg)
        inference_request = Request('{}/inference/'.format(
            self.parameters['route']),
            data=self._create_payload(b64encode(self.image).decode('utf8')),
            method='POST'
        )

        try:
            response = loads(urlopen(inference_request).read())
            if response['statusCode'] == 200:
                self.plugin.inferencer.pred = eval(response['defect_detected'])
                self.parameters['bad_responses'] = 0
                self.plugin.inferencer.REQUEST_INTERVAL = 10.0
                boxes = eval(re.sub('\s+', ',', re.sub('\s+\]', ']', re.sub('\[\s+', '[', response['boxes'].replace('\n','')))))
                self.plugin._plugin_manager.send_plugin_message(self.plugin._identifier, dict(type="display_frame", image=self.draw_boxes(boxes)))
                self.plugin._plugin_manager.send_plugin_message(self.plugin._identifier, dict(type="icon", icon='plugin/printwatch/static/img/printwatch-green.gif'))
            elif response['statusCode'] == 213:
                self.plugin.inferencer.REQUEST_INTERVAL= 300.0
            else:
                self.plugin.inferencer.pred = False
                self.parameters['bad_responses'] += 1
                self.plugin.inferencer.REQUEST_INTERVAL = 10.0
                self.plugin._logger.info("Payload: {} {}".format(self.plugin._settings.get([]), self.parameters))
                self.plugin._logger.info("Response: {}".format(response))

        except Exception as e:
            self.plugin._logger.info("Error retrieving server response: {}".format(str(e)))
            self.parameters['bad_responses'] += 1
            self.plugin.inferencer.pred = False
        self.parameters['last_t'] = time()

    def draw_boxes(self, boxes):
        pil_img = Image.open(io.BytesIO(self.image))
        process_image = ImageDraw.Draw(pil_img)
        width, height = pil_img.size

        for i, det in enumerate(boxes):
            det = [j / 640 for j in det]
            x1 = (det[0] - (det[2]/2))*width
            y1 = (det[1] - (det[3]/2))* height
            x2 = (det[0] + (det[2]/2))*width
            y2 = (det[1] + (det[3]/2))*height
            process_image.rectangle([(x1, y1), (x2, y2)], fill=None, outline="red", width=4)

        out_img = io.BytesIO()
        pil_img.save(out_img, format='PNG')
        contents = b64encode(out_img.getvalue()).decode('utf8')
        return 'data:image/png;charset=utf-8;base64,' + contents.split('\n')[0]
