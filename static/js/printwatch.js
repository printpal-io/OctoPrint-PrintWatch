$(function() {
    function PrintwatchViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.contents = ko.observable();
        self.statusIcon = ko.observable();

        self.onBeforeBinding = function() {
            self.statusIcon("plugin/printwatch/static/img/printwatch-grey.png");
        }

        self.onDataUpdaterPluginMessage = function(plugin, data){
          if(plugin=="printwatch" && data.type=="display_frame"){
            self.contents(data.image);
          } else if(plugin=="printwatch" && data.type=="icon") {
            self.statusIcon(data.icon);
          }
          return ;
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        PrintwatchViewModel,
        ["settingsViewModel"],
        ["#navbar_plugin_printwatch", "#tab_plugin_printwatch"]
    ]);
});