import octoprint.plugin
from time import time, sleep
from datetime import datetime
from threading import Thread
import asyncio
import aiohttp
from base64 import b64encode
from uuid import uuid4
from io import BytesIO
import PIL.Image as Image
from PIL import ImageDraw
from typing import Union
from .utils import *


DEFAULT_ROUTE = 'https://octoprint.printpal.io'
ANOMALY_DETECTION_ROUTE = 'http://ad.printpal.io'

PRINTING_STATES = [
                    'printing',
                    'finishing',
                    'printing from sd',
                    'sending file to sd'
                    ]

PAUSED_STATES = [
                'paused',
                'pausing',
                'resuming'
                ]
ONLINE_STATES = [
                'connecting',
                'operational',
                'closed',
                'transferring_file',
                'starting print from sd',
                'starting to send file to sd',
                'connecting',
                'opening serial connection',
                'detecting serial connection',
                'connecting',
                'starting',
                'cancelling'
                ]

class CommManager(octoprint.plugin.SettingsPlugin):
    def __init__(self, plugin):
        self.plugin = plugin
        self.heartbeat_interval = 30.0
        self.timeout = 10.0
        self.response = None
        self.aio = None
        self.parameters = {
                            'ticket' : '',
                            'last_t' : 0.0,
                            'route' : DEFAULT_ROUTE,
                            'bad_responses' : 0,
                            'notification' : ''
                            }

    def _init_op(self) -> None:
        if self.plugin._settings.get(["printer_id"]) is None:
            self.plugin._settings.set(['printer_id'], uuid4().hex)

    def _heartbeat(self) -> None:
        init = True
        while self.plugin._settings.get(["enable_detector"]) and self.heartbeat:
            sleep(1.0)
            if time() - self.parameters['last_t'] > self.heartbeat_interval:
                r_ = get_all_stats(self.plugin._printer)
                self.plugin._logger.info('All stats: {}'.format(r_))
                try:
                    self.aio.run_until_complete(self._send('api/v2/heartbeat', include_settings=init))
                    if not isinstance(self.response, bool) and self.response is not None:
                        self._check_action(self.response)
                        init = False
                except Exception as e:
                    self.plugin._logger.info(
                        "Error with Heartbeat: {}".format(str(e))
                    )

                self.parameters['last_t'] = time()
        self.plugin._logger.info("Heartbeat loop closed")



    def _create_payload(self,
            image=None,
            force_state : int = 0,
            include_settings : bool = False,
            force : bool = False,
            notify : bool = False,
            notification_level : str = '',
            event : str = None
        ) -> dict:

        if force_state > 0:
            state = force_state
        else:
            s = self.plugin._printer.get_state_string()
            if s.lower() in PRINTING_STATES:
                state = 0
            elif s.lower() in PAUSED_STATES:
                state = 1
            elif s.lower() in ONLINE_STATES:
                state = 2
            else:
                state = 500

        r = {
            'api_key' : self.plugin._settings.get(["api_key"]),
            'printer_id' : self.plugin._settings.get(["printer_id"]),
            'state' : state,
            'version' : self.plugin._plugin_version,
            'ticket_id' : self.parameters['ticket']
        }

        r['force'] = 'True' if force else 'False'

        if image is not None:
            print_job_info = self.plugin._printer.get_current_data()
            r['image_array'] = image
            r['conf'] = int(self.plugin._settings.get(["confidence"]))/100.0
            r['buffer_length'] = int(self.plugin._settings.get(["buffer_length"]))
            r['buffer_percent'] = int(self.plugin._settings.get(["buffer_percent"]))
            r['thresholds'] = [int(self.plugin._settings.get(["notification_threshold"]))/100.0, int(self.plugin._settings.get(["action_threshold"]))/100.0]
            r['scores'] = self.plugin.inferencer.scores
            r['printTime'] = print_job_info.get('progress').get('printTime')
            r['printTimeLeft'] = print_job_info.get('progress').get('printTimeLeft')
            r['progress'] = print_job_info.get('progress').get('completion')
            r['job_name'] = self.plugin._printer.get_current_job().get('file').get('name')
            r['sma_spaghetti'] = self.plugin.inferencer.smas[-1][0] if len(self.plugin.inferencer.smas) > 0 else 0.
            r['enable_feedback_images'] = self.plugin._settings.get(['enable_feedback_images'])

        if include_settings:
            r['settings'] = {
                'detection_threshold' : int(self.plugin._settings.get(["confidence"])),
                'buffer_length' : int(self.plugin._settings.get(["buffer_length"])),
                'notification_threshold' : int(self.plugin._settings.get(["notification_threshold"])),
                'action_threshold' : int(self.plugin._settings.get(["action_threshold"])),
                'enable_notification' : self.plugin._settings.get(["enable_email_notification"]),
                'email_address' : self.plugin._settings.get(["email_addr"]),
                'pause_print' : self.plugin._settings.get(["enable_shutoff"]),
                'cancel_print' : self.plugin._settings.get(["enable_stop"]),
                'extruder_heat_off' : self.plugin._settings.get(["enable_extruder_shutoff"]),
                'enable_feedback_images' : self.plugin._settings.get(['enable_feedback_images'])
            }

        if notify:
            print_job_info = self.plugin._printer.get_current_data()
            r['printTime'] = print_job_info.get('progress').get('printTime')
            r['printTimeLeft'] = print_job_info.get('progress').get('printTimeLeft')
            r['progress'] = print_job_info.get('progress').get('completion')
            r['job_name'] = self.plugin._printer.get_current_job().get('file').get('name')
            r['email_addr'] = self.plugin._settings.get(["email_addr"])
            r['notification'] = notification_level
            r['time'] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        if event is not None:
            print_job_info = self.plugin._printer.get_current_data()
            event_package = {
                'type': event,
                'time': time(),
                'time_elapsed': print_job_info.get('progress').get('printTime'),
                'time_left': print_job_info.get('progress').get('printTimeLeft'),
                'level': self.plugin.inferencer.smas[-1][0] if len(self.plugin.inferencer.smas) > 0 else 0,
                'timestamp' : datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            }
            r['event'] = event_package


        return r


    async def _send(self,
            endpoint : str = 'api/v2/infer',
            force_state : int = 0,
            include_settings : bool = False,
            force : bool = False,
            notification_level : str = '',
            event=None
        ) -> Union[dict, bool]:
        key = self.plugin._settings.get(['api_key'])
        if key not in ['', None] and \
          self.plugin._settings.get(['printer_id']) not in ['', None] and \
          (key.startswith("fmu_") or key.startswith("sub_")):

            if endpoint =='api/v2/heartbeat':
                data = self._create_payload(force_state=force_state,
                                include_settings=include_settings,
                                force=force
                        )
            elif endpoint == 'api/v2/notify':
                data = self._create_payload(None,
                                include_settings=include_settings,
                                force=force,
                                notify=True,
                                notification_level=notification_level
                        )
            elif endpoint == 'api/v2/print/event':
                data = self._create_payload(None,
                            include_settings=include_settings,
                            force=force,
                            notify=True,
                            notification_level=notification_level,
                            event=event
                        )
            else:
                 data = self._create_payload(image=b64encode(self.image).decode('utf8'),
                            include_settings=include_settings,
                            force=force
                        )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                                '{}/{}'.format(self.parameters['route'], endpoint),
                                json = data,
                                headers={'User-Agent': 'Mozilla/5.0'},
                                timeout=aiohttp.ClientTimeout(total=self.timeout if endpoint is not 'api/v2/notify' else 30.0)
                            ) as response:
                            r = await response.json()
            self.response = r

            return r
        else:
            self.reponse = False
            return False

    def _check_action(self, response : dict) -> None:
        action = response.get('action')
        if action == 'pause':
            while not ((self.plugin._printer.is_pausing() and self.plugin._printer.is_printing()) or self.plugin._printer.is_paused()):
                self.plugin._printer.pause_print()
        elif action == 'cancel':
            while not (self.plugin._printer.is_cancelling() and self.plugin._printer.is_printing()):
                self.plugin._printer.cancel_print()
        elif action == 'resume':
            if self.plugin._printer.is_paused():
                while not self.plugin._printer.is_printing():
                    self.plugin._printer.resume_print()

        if response.get('settings') not in [None, False]:
            self.plugin._settings.set(['confidence'], response.get('settings').get('detection_threshold'), self.plugin._settings.get(['confidence']))
            self.plugin._settings.set(['buffer_length'], response.get('settings').get('buffer_length'), self.plugin._settings.get(['buffer_length']))
            self.plugin._settings.set(['notification_threshold'], response.get('settings').get('notification_threshold'), self.plugin._settings.get(['notification_threshold']))
            self.plugin._settings.set(['action_threshold'], response.get('settings').get('action_threshold'), self.plugin._settings.get(['action_threshold']))
            self.plugin._settings.set(['enable_email_notification'], response.get('settings').get('enable_notification'), self.plugin._settings.get(['enable_email_notification']))
            self.plugin._settings.set(['email_addr'], response.get('settings').get('email_address'), self.plugin._settings.get(['email_addr']))
            self.plugin._settings.set(['enable_shutoff'], response.get('settings').get('pause_print'), self.plugin._settings.get(['enable_shutoff']))
            self.plugin._settings.set(['enable_stop'], response.get('settings').get('cancel_print'), self.plugin._settings.get(['enable_stop']))
            self.plugin._settings.set(['enable_extruder_shutoff'], response.get('settings').get('extruder_heat_off'), self.plugin._settings.get(['enable_extruder_shutoff']))
            self.plugin._settings.set(['enable_feedback_images'], response.get('settings').get('enable_feedback_images') , self.plugin._settings.get(['enable_feedback_images']))
            self.plugin._settings.save(force=True, trigger_event=True)

    def _create_ticket(self) -> None:
        ticket = uuid4().hex
        self.parameters['ticket'] = ticket
        self.plugin._logger.info(
            "Ticket {} created for print job".format(ticket)
        )

    def _appends(self, response : dict) -> None:
        self.plugin.inferencer.circular_buffer.append([eval(response['defect_detected']), time()])
        self.plugin.inferencer.scores.append(response['score'])
        self.plugin.inferencer.action_level = response['levels']
        self.plugin.inferencer.smas.append(response['smas'][0])

    def start_service(self) -> None:
        self.heartbeat = True
        if self.plugin._settings.get(["enable_detector"]):
            if self.plugin.inferencer.inference_loop is None:
                self.heartbeat_loop = Thread(target=self._heartbeat)
                self.heartbeat_loop.daemon = True
                self.heartbeat_loop.start()
                self.aio = asyncio.new_event_loop()
                asyncio.set_event_loop(self.aio)
                self.plugin._logger.info("PrintWatch heartbeat service started")
                if self.plugin.inferencer.triggered:
                    self.plugin.inferencer.notification_event('action')


    def kill_service(self) -> None:
        self.heartbeat = False
        self.heartbeat_loop = None
        self.plugin._logger.info("PrintWatch heartbeat service terminated")


    async def send_request(self) -> None:
        self.image = self.plugin.streamer.grab_frame()
        if not isinstance(self.image, bool):
            try:
                response = await self._send()
                if not isinstance(response, bool):
                    self.parameters['last_t'] = time()
                    if response['statusCode'] == 200:
                        self._appends(response)
                        self._check_action(response)
                        self.parameters['bad_responses'] = 0
                        self.plugin.inferencer.REQUEST_INTERVAL = 10.0 if self.plugin._settings.get(["api_key"]).startswith("sub_") else response.get("interval", 30.0)
                        self.timeout = 10.0
                        boxes = response['boxes']
                        self.plugin._plugin_manager.send_plugin_message(
                            self.plugin._identifier,
                            dict(
                                type="display_frame",
                                image=self.draw_boxes(boxes)
                            )
                        )
                        if self.plugin._settings.get(["enable_flashing_icon"]):
                            self.plugin._plugin_manager.send_plugin_message(
                                self.plugin._identifier,
                                dict(
                                    type="icon",
                                    icon='plugin/printwatch/static/img/printwatch-green.gif'
                                )
                            )
                        self.plugin.inferencer._buffer_check()
                    elif response['statusCode'] == 213:
                        self.plugin.inferencer.REQUEST_INTERVAL= 300.0
                    else:
                        self.plugin.inferencer.pred = False
                        self.parameters['bad_responses'] += 1
                        self.plugin.inferencer.REQUEST_INTERVAL = 10.0 + self.parameters['bad_responses'] * 5.0 if self.parameters['bad_responses'] < 10 else 120.
                        self.plugin._logger.info(
                            "Payload: {} {}".format(
                                self.plugin._settings.get([]),
                                self.parameters
                            )
                        )
                        self.plugin._logger.info(
                            "Response: {}".format(response)
                        )
                else:
                    self.plugin._logger.info(
                        "Invalid API key or printer ID"
                    )

            except Exception as e:
                self.plugin._logger.info(
                    "Error retrieving server response: {}".format(str(e))
                )
                self.parameters['bad_responses'] += 1
                self.plugin.inferencer.REQUEST_INTERVAL = 10.0 + self.parameters['bad_responses'] * 5.0 if self.parameters['bad_responses'] < 10 else 120.
                self.timeout = 10.0 + self.parameters['bad_responses'] * 5.0 if self.parameters['bad_responses'] < 4 else 30.
                self.plugin.inferencer.pred = False
                self.parameters['last_t'] = time()
        else:
            self.parameters['bad_responses'] += 1
            self.plugin.inferencer.REQUEST_INTERVAL = 10.0 + self.parameters['bad_responses'] * 5.0 if self.parameters['bad_responses'] < 10 else 120.
            self.plugin._logger.info('Issue acquiring the snapshot frame from the URL provided in the settings. - {}'.format(self.image))

    def draw_boxes(self, boxes : list) -> str:
        pil_img = Image.open(BytesIO(self.image))
        process_image = ImageDraw.Draw(pil_img)
        width, height = pil_img.size

        for i, det in enumerate(boxes):
            det = [j / 640 for j in det]
            x1 = det[0] * width
            y1 = det[1] * height
            x2 = det[2] * width
            y2 = det[3] * height
            process_image.rectangle([(x1, y1), (x2, y2)], fill=None, outline="red", width=4)

        out_img = BytesIO()
        pil_img.save(out_img, format='PNG')
        contents = b64encode(out_img.getvalue()).decode('utf8')
        return 'data:image/png;charset=utf-8;base64,' + contents.split('\n')[0]

    async def email_notification(self, notification_level : str) -> None:
        if self.plugin._settings.get(["enable_email_notification"]):
            try:
                response = await self._send('api/v2/notify', notification_level=notification_level)
                if not isinstance(response, bool):
                    self.plugin._logger.info(
                        "Notification sent to {}".format(self.plugin._settings.get(["email_addr"]))
                    )
                else:
                    self.plugin._logger.info(
                        "Invalid API key or printer ID"
                    )
            except Exception as e:
                self.plugin._logger.info(
                    "Error retrieving server response for email notification: {}".format(str(e))
                )

    def event_feedback(self, event : str) -> None:
        self.aio.run_until_complete(self._send('api/v2/print/event', event=event))

    def new_ticket(self) -> None:
        self._create_ticket()
