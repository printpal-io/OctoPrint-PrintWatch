$(function() {
    function PrintwatchViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.contents = ko.observable();
        self.statusIcon = ko.observable();
        self.smas = [];
        self.chart_exists = false;
        self.plotIndex = 0;

        const arrayColumn = (arr, n) => arr.map(x => x[n]);

        self.onBeforeBinding = function() {
            self.statusIcon("plugin/printwatch/static/img/printwatch-grey.png");
            self.chart = self.initRenderChart();
        }

        self.onDataUpdaterPluginMessage = function(plugin, data){
          if(plugin=="printwatch" && data.type=="display_frame"){
            self.contents(data.image);
          } else if(plugin=="printwatch" && data.type=="icon") {
            self.statusIcon(data.icon);
          } else if (plugin=="printwatch" && data.type=="score") {
            self.renderChart(self.chart, data.scores, data.pop);
            self.smas.push(data.scores);
          } else if(plugin=="printwatch" && data.type=="resetPlot") {
            self.smas = [];
            self.plotIndex = 0;
            self.initRenderChart();
          } else if (plugin=="printwatch" && data.type=="onSave") {
            if (self.settings.settings.plugins.printwatch.notification_threshold()/100.0 != self.chart.data.datasets[2].data[0] || self.settings.settings.plugins.printwatch.action_threshold()/100.0 != self.chart.data.datasets[3].data[0]) {
              self.plotThresholds();
            }
            if (self.settings.settings.plugins.printwatch.buffer_length()*4 != self.chart.data.labels.length) {
              self.smas = [];
              self.plotIndex = 0;
              self.initRenderChart();
              self.plotThresholds();
              self.chart.options.scales.x.max = buffer_length * 4;
              self.chart.options.scales.x.ticks.callback = function(value, index, labels) {
                                                              return;
                                                            }
              self.chart.update();

            }
          }
          return ;
        }

        self.renderChart = function(chart, data, pop) {
          buffer_length = self.settings.settings.plugins.printwatch.buffer_length()
          chart.data.datasets[0].data.push(data[0]);
          chart.data.datasets[1].data.push(data[2]);
          if (chart.data.datasets[0].data.length > buffer_length * 4) {
            chart.data.datasets[0].data.shift();
            chart.data.datasets[1].data.shift();
            chart.options.scales.x.ticks.callback = function(value, index, labels)  {
              if (index == buffer_length * 4) {
                return
              } else if (index%buffer_length==0 && index !=0) {
                return (-(((buffer_length * 4 - index)%(buffer_length*4)) * 12.0)/60.0).toString() + ' min'
              }
            }
          } else {
            chart.options.scales.x.ticks.callback = function(value, index, labels)  {
              buffer_length = self.settings.settings.plugins.printwatch.buffer_length()
              if (index == self.plotIndex) {
                return
              } else if (self.plotIndex - index > 0 && index != 0 && (self.plotIndex - index)%buffer_length == 0) {
                return (-((self.plotIndex - index)%self.plotIndex *12.0) / 60.0).toString() + ' min'
              }
            }
            if (self.plotIndex < buffer_length * 4) {
            self.plotIndex ++;
            }
          }
          chart.update();
        }


        self.plotThresholds = function() {
          buffer_length = self.settings.settings.plugins.printwatch.buffer_length();
          self.chart.data.labels = Array.from(Array(buffer_length*4).keys());
          self.chart.data.datasets[2].data = Array(buffer_length*4).fill(self.settings.settings.plugins.printwatch.notification_threshold() / 100.0);
          self.chart.data.datasets[3].data = Array(buffer_length*4).fill(self.settings.settings.plugins.printwatch.action_threshold() / 100.0);
          self.chart.update();
        }

        self.initRenderChart = function() {
          buffer_length = self.settings.settings.plugins.printwatch.buffer_length();
          if (self.chart_exists) {
            self.chart.data.datasets[0].data = [];
            self.chart.data.datasets[1].data = [];
            self.chart.data.labels = Array.from(Array(buffer_length*4).keys());
            self.chart.update();
          } else {
            var options = {
            type: 'line',
            data: {
              labels: Array.from(Array(buffer_length*4).keys()),
              datasets: [
                {
                  label: ['s1'],
                  data: arrayColumn(self.smas, 0),
                  borderWidth: 4,
                  lineTension: 0.4,
                  backgroundColor: "#0099ff",
                  borderColor:"#0099ff",
                  pointRadius: 0.0
                },
                {
                  label: ['s2'],
                  data: arrayColumn(self.smas, 0),
                  borderWidth: 2,
                  lineTension: 0.4,
                  backgroundColor: "#f012be",
                  borderColor:"#f012be",
                  pointRadius: 0.0
                },
                {
                  label: ['notification_threshold'],
                  data: Array(buffer_length*4).fill(self.settings.settings.plugins.printwatch.notification_threshold()/100.0),
                  borderWidth: 1,
                  borderDash: [5, 5],
                  lineTension: 0.4,
                  backgroundColor: "#ff851b",
                  borderColor:"#ff851b",
                  pointRadius: 0.0
                },
                {
                  label: ['action_threshold'],
                  data: Array(buffer_length*4).fill(self.settings.settings.plugins.printwatch.action_threshold()/100.0),
                  borderWidth: 1,
                  borderDash: [5, 5],
                  lineTension: 0.4,
                  backgroundColor: "#ff4136",
                  borderColor:"#ff4136",
                  pointRadius: 0.0
                }
              ]
            },
            options: {
              plugins: {
                legend: {
                  display: false
                }
              },
              scales: {
                y : {
                      min: -0.01,
                      max: 1,
                      grid : {drawTicks:false},
                      ticks: {
                              stepSize: 0.25,
                              callback: function(value, index, labels) {
                                if (value > 0 ) {
                                return parseInt(value * 100)
                                } else { return}
                              }
                            },
                      title : {
                        display: true,
                        text: "Threshold"
                      }
                  },
                x : {
                      min: 0,
                      max : buffer_length * 4,
                      grid : {
                        display: false,
                        drawTicker: false
                      },
                      ticks: {
                              stepSize: buffer_length,
                              callback: function(value, index, labels) {
                                  return;
                                }
                              }
                      }
                  }
              }
            }

            var ctx = document.getElementById('livePlot').getContext('2d');
            self.chart_exists = true;
            return new Chart(ctx, options);
          }

          }

    }


    OCTOPRINT_VIEWMODELS.push([
        PrintwatchViewModel,
        ["settingsViewModel"],
        ["#navbar_plugin_printwatch", "#tab_plugin_printwatch"]
    ]);
});
