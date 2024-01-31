from __future__ import absolute_import, unicode_literals
import octoprint.plugin
from octoprint.events import Events
from .videostreamer import VideoStreamer
from .comm import CommManager
from .inferencer import Inferencer
from .printer import PrinterControl
from .ad import AD
import asyncio


class PrintWatchPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.ShutdownPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.EventHandlerPlugin,
                       octoprint.plugin.SimpleApiPlugin
       ):


    def __init__(self) -> None:
        self.streamer = VideoStreamer(self)
        self.inferencer = Inferencer(self)
        self.comm_manager = CommManager(self)
        self.controller = PrinterControl(self)
        self.ad = AD(self)


    def on_after_startup(self) -> None:
        self._logger.info("Loading PrintWatch...")
        self.inferencer._init_op()
        self.comm_manager._init_op()
        self.comm_manager.start_service()

    def get_update_information(self) -> None:
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

    def on_settings_save(self, data) -> None:
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        if self.inferencer.warning_notification:
            self.inferencer.begin_cooldown()
        self._settings.save()
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="onSave"))
        asyncio.ensure_future(self.comm_manager._send('api/v2/heartbeat', include_settings=True, force=True))



    def get_settings_defaults(self) -> dict:
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
            api_key = '',
            printer_id = None,
            enable_flashing_icon = False,
            camera_rotation = "0" #parse as string from UI
            )

    def get_template_configs(self) -> list:
        return [
            dict(type="settings", custom_bindings=False)
        ]


    def get_assets(self) -> list:
        return dict(
            js=["js/printwatch.js"],
            css=["css/printwatch.css"]
        )


    def on_event(self, event, payload) -> None:
        if event == Events.PRINT_STARTED:
            self.inferencer.start_service()
            self.comm_manager.kill_service()
            self.comm_manager.new_ticket()
            self.ad.start_service()
            self.ad.tx_ = self.comm_manager.parameters.get('ticket')
            self._plugin_manager.send_plugin_message(
                self._identifier,
                dict(type="resetPlot")
            )
        elif event == Events.PRINT_RESUMED:
            if self.inferencer.triggered:
                self.controller.restart()
            self.inferencer.start_service()
            self.ad.start_service()
            self.comm_manager.kill_service()
            self.comm_manager.event_feedback(str(event))
        elif event in (
            Events.PRINT_PAUSED,
            Events.PRINT_CANCELLED,
            Events.PRINT_DONE,
            Events.PRINT_FAILED
            ):
            if self.inferencer.triggered:
                self.inferencer.shutoff_event()
            self.inferencer.kill_service()
            self.ad.kill_service()
            self.comm_manager.start_service()
            self.comm_manager.event_feedback(str(event))

            if event is not Events.PRINT_PAUSED:
                self._plugin_manager.send_plugin_message(
                    self._identifier,
                    dict(type="resetPlot")
                )




    def on_shutdown(self) -> None:
        self.inferencer.run_thread = False
        self.comm_manager.aio.run_until_complete(self.comm_manager._send('api/v2/heartbeat', force_state=500))
        self._logger.info('Forced printer state OFF')


__plugin_name__ = "PrintWatch"
__plugin_version__ = "1.3.01"
__plugin_description__ = "PrintWatch watches your prints for defects and optimizes your 3D printers using Artificial Intelligence."
__plugin_pythoncompat__ = ">=3.6,<4"
__plugin_implementation__ = PrintWatchPlugin()


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrintWatchPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
