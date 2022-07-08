from __future__ import absolute_import, unicode_literals
import octoprint.plugin
from octoprint.events import Events
from .videostreamer import VideoStreamer
from .comm import CommManager
from .inferencer import Inferencer
from .printer import PrinterControl


class PrintWatchPlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.ShutdownPlugin,
                           octoprint.plugin.TemplatePlugin,
                           octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.EventHandlerPlugin
                           ):


    def on_after_startup(self):
        self._logger.info("Loading PrintWatch...")
        self.comm_manager = CommManager(self)
        self.streamer = VideoStreamer(self)
        self.inferencer = Inferencer(self)
        self.controller = PrinterControl(self)


    def get_update_information(self):
        return dict(
            printwatch=dict(
                name=self._plugin_name,
                version=self._plugin_version,

                type="github_release",
                current=self._plugin_version,
                user="printpal-io",
                repo="OctoPrint-PrintWatch",

                pip="https://github.com/printpal-io/OctoPrint-PrintWatch/archive/{target}.zip"

            )
        )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        if self.inferencer.warning_notification:
            self.inferencer.begin_cooldown()
        self._settings.save()
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="onSave"))

    def get_settings_defaults(self):
        return dict(
            stream_url = 'http://127.0.0.1/webcam/?action=snapshot',
            enable_detector = True,
            enable_email_notification = False,
            email_addr = '',
            enable_shutoff = False,
            enable_stop = False,
            enable_extruder_shutoff = False,
            notification_threshold = 40,
            action_threshold = 60,
            confidence = 60,
            buffer_length = 16,
            buffer_percent = 80,
            enable_feedback_images = True,
            api_key = ''
            )

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]


    def get_assets(self):
        return dict(
            js=["js/printwatch.js"],
            css=["css/printwatch.css"]
        )


    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self.inferencer.start_service()
            self.comm_manager.kill_service()
            self.comm_manager.new_tcket()
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="resetPlot"))
        elif event == Events.PRINT_RESUMED:
            if self.inferencer.triggered:
                self.controller.restart()
            self.inferencer.start_service()
            self.comm_manager.kill_service()
        elif event in (
            Events.PRINT_PAUSED,
            Events.PRINT_CANCELLED,
            Events.PRINT_DONE,
            Events.PRINT_FAILED
            ):
            if self.inferencer.triggered:
                self.inferencer.shutoff_event()
            self.inferencer.kill_service()

            if event == Events.PRINT_PAUSED:
                self.comm_manager.start_service()
            else:
                self.comm_manager.kill_service()
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="resetPlot"))



    def on_shutdown(self):
        self.inferencer.run_thread = False



__plugin_name__ = "PrintWatch"
__plugin_version__ = "1.1.1"
__plugin_description__ = "PrintWatch watches your prints for defects and optimizes your 3D printers using Artificial Intelligence."
__plugin_pythoncompat__ = ">=2.7,<4"
__plugin_implementation__ = PrintWatchPlugin()


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrintWatchPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
