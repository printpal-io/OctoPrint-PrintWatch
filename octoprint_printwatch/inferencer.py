from threading import Thread
from time import time

BUFFER_LENGTH = 16
BUFFER_PERCENTAGE = 0.80

class Inferencer():
    def __init__(self, plugin):
        self.plugin = plugin
        self.circular_buffer = []
        self.current_percent = 0.0
        self.triggered = False
        self.pred = False
        self.REQUEST_INTERVAL = 10.0
        self.inference_loop = None


    def _buffer_check(self):
        if self.pred:
            self.circular_buffer.append([True, time()])
        else:
            self.circular_buffer.append([False, time()])

        if len(self.circular_buffer) > BUFFER_LENGTH:
            self.circular_buffer.pop(0)

    def _attempt_pause(self):
        self.plugin._printer.pause_print()
        self.triggered = True
        self.plugin._logger.info("Print Pause command sent.")

    def _inferencing(self):
        self.plugin._logger.info("PrintWatch Inference Loop starting...")
        while self.run_thread and self.plugin._settings.get(["enable_detector"]):
            if self.plugin._printer.is_printing() and not self.triggered:
                if time() - self.plugin.comm_manager.parameters['last_t'] > self.REQUEST_INTERVAL:
                    if self.plugin.streamer.jpg is not None:
                        self.plugin.comm_manager.send_request()
                        self._buffer_check()

                        if len(self.circular_buffer) == BUFFER_LENGTH:
                            self.current_percent = [i[0] for i in self.circular_buffer].count(True) / BUFFER_LENGTH
                            if self.current_percent >= BUFFER_PERCENTAGE:
                                pause_condition = (not self.triggered or (not self.plugin._printer.is_pausing() and self.plugin._printer.is_printing())) and self.plugin._settings.get(["enable_shutoff"])
                                if pause_condition:
                                    self.plugin._logger.info("Failure Detected. Pausing Print.")
                                    self._attempt_pause()

                if self.plugin.comm_manager.parameters['bad_responses'] >= BUFFER_LENGTH:
                    self.plugin._logger.info("Too many bad response from server. Disabling PrintWatch monitoring")
                    self.plugin.streamer.kill_service()
                    self.kill_service()

    def start_service(self):
        self.triggered = False
        if self.plugin._settings.get(["enable_detector"]):
            if self.inference_loop is None and self.plugin.streamer.stream is not None:
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
        self.current_percent = 0.0
        self.plugin.comm_manager.parameters['nms'] = False
        self.plugin._logger.info("PrintWatch inference service terminated")
        self.plugin._plugin_manager.send_plugin_message(self.plugin._identifier, dict(type="icon", icon='plugin/printwatch/static/img/printwatch-grey.png'))

    def shutoff_event(self):
        self.plugin.controller.shutoff_actions()
        if self.triggered:
            self.plugin.comm_manager.email_notification()
