$(function() {
    function PrintwatchViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];

        self.contents = ko.observable();

        self.onDataUpdaterPluginMessage = function(plugin, data){
          self.contents(data.image);
        }
        // this will be called when the user clicks the "Go" button and set the iframe's URL to
        // the entered URL

        // This will get called before the PrintwatchViewModel gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.
    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        PrintwatchViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],
        ["#tab_plugin_printwatch"]

    ]);
});
