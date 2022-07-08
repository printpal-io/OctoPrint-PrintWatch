from threading import Thread
from time import time, sleep

MIN_MULTIPLIER = 0.5
MAX_MULTIPLIER = 4

class Inferencer():
    def __init__(self, plugin):
        self.plugin = plugin
        self.circular_buffer = []
        self.scores = []
        self.current_percent = 0.0
        self.triggered = False
        self.warning_notification = False
        self.pred = False
        self.REQUEST_INTERVAL = 10.0
        self.inference_loop = None
        self.action_level = []
        self.cooldown_time = 0.0
        self.smas = []

    def _buffer_check(self):
        buffer_length = int(self.plugin._settings.get(["buffer_length"]))
        if len(self.smas) > 0:
            self.plugin._plugin_manager.send_plugin_message(self.plugin._identifier, dict(type="score", scores=self.smas[-1], pop=len(self.scores) > int(buffer_length * MAX_MULTIPLIER)))
        while len(self.circular_buffer) > buffer_length:
            self.circular_buffer.pop(0)
        while len(self.scores) > int(buffer_length * MAX_MULTIPLIER):
            self.scores.pop(0)
            self.smas.pop(0)

        self.current_percent = [i[0] for i in self.circular_buffer].count(True) / buffer_length if len(self.circular_buffer) == buffer_length else 0.0
        self.action_level = self.action_level if len(self.scores) >= buffer_length else [False, False, False]
        self._action_check()

    def _action_check(self):
        self.warning_notification = time() - self.cooldown_time < 600 and self.cooldown_time > 0.0 if self.cooldown_time > 0.0 else self.warning_notification #10 minute cooldown
        if self.action_level[1]:
            #pause/stop the print
            if not self.triggered:
                self.plugin._logger.info("Action level reached")
                if self.plugin._settings.get(["enable_stop"]):
                    self._attempt_action('cancel')
                    self.triggered = True
                elif self.plugin._settings.get(["enable_shutoff"]):
                    self._attempt_action('pause')
                    self.triggered = True
        elif self.action_level[0]:
            if not self.warning_notification:
                self.plugin._logger.info("Notification level reached")
                if self.plugin._settings.get(["enable_email_notification"]):
                    self.notification_event('warning')
                    self.warning_notification = True
                    self.cooldown_time = 0.0

    def _attempt_action(self, action):
        if action == 'cancel':
            self.plugin._printer.cancel_print()
        else:
            self.plugin._printer.pause_print()
        self.plugin._logger.info("Print {} command sent to OctoPrint.".format(action))


    def _inferencing(self):
        self.plugin._logger.info("PrintWatch Inference Loop starting...")
        while self.run_thread and self.plugin._settings.get(["enable_detector"]):
            sleep(0.1) #prevent cpu overload
            if self.plugin._printer.is_printing() and not self.triggered:
                if time() - self.plugin.comm_manager.parameters['last_t'] > self.REQUEST_INTERVAL:
                    self.plugin.comm_manager.send_request()
                    self._buffer_check()

                if self.plugin.comm_manager.parameters['bad_responses'] >= int(self.plugin._settings.get(["buffer_length"])):
                    self.plugin._logger.info("Too many bad response from server. Disabling PrintWatch monitoring")
                    self.kill_service()

    def start_service(self):
        self.triggered = False
        self.warning_notification = False
        self.plugin.comm_manager.parameters['notification'] =  ''
        if self.plugin._settings.get(["enable_detector"]):
            if self.inference_loop is None:
                self.run_thread = True
                self.inference_loop = Thread(target=self._inferencing)
                self.inference_loop.daemon = True
                self.inference_loop.start()
                self.plugin._logger.info("PrintWatch inference service started")
                self.plugin._plugin_manager.send_plugin_message(self.plugin._identifier, dict(type="icon", icon='plugin/printwatch/static/img/printwatch-green.gif'))

    def kill_service(self):
        self.run_thread = False
        self.inference_loop = None
        self.REQUEST_INTERVAL = 10.0
        self.plugin.comm_manager.parameters['bad_responses'] = 0
        self.circular_buffer = []
        self.action_level = []
        self.scores = []
        self.current_percent = 0.0
        self.plugin._logger.info("PrintWatch inference service terminated")
        self.plugin._plugin_manager.send_plugin_message(self.plugin._identifier, dict(type="icon", icon='plugin/printwatch/static/img/printwatch-grey.png'))

    def shutoff_event(self):
        self.plugin.controller.shutoff_actions(self.plugin._settings.get(["enable_extruder_shutoff"]))
        if self.triggered:
            self.notification_event('action')

    def notification_event(self, notification_level):
        self.plugin.comm_manager.email_notification(notification_level)

    def begin_cooldown(self):
        self.cooldown_time = time()
