class PrinterControl():

    def __init__(self, plugin):
        self.plugin = plugin
        self._temperatures = None

    def _extruder_set(self, temperature=0):
        for extruder in range(self.plugin._printer_profile_manager.get_current().get('extruder').get('count', 1)):
            self.plugin._printer.set_temperature('tool{}'.format(extruder), temperature)
            self.plugin._logger.info("Temperature has been set to {} for tool {}".format(temperature, extruder))


    def _apply_temperatures(self):
        _num_extruders = self.plugin._printer_profile_manager.get_current().get('extruder').get('count', 1)
        for extruder in range(_num_extruders):
            _tool_temperature = self._temperatures['tool{}'.format(extruder)]['target']
            self.plugin._printer.commands("M109 T{} S{}".format(extruder, _tool_temperature))
        if 'bed' in self._temperatures:
            _bed_temperature = self._temperatures['bed']['target']
            self.plugin._printer.commands("M190 S{}".format(_bed_temperature))


    def restart(self):
        self._apply_temperatures()


    def shutoff_actions(self, extruders=False):
        self._temperatures = self.plugin._printer.get_current_temperatures()
        if extruders:
            self._extruder_set()
