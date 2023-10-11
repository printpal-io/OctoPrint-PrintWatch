import requests
from threading import Thread
from time import time, sleep
from .utils import *
from uuid import uuid4
import csv
import os


ANOMALY_DETECTION_ROUTE = 'https://ad.printpal.io'
GENERAL_OCTOPRINT_NAME = 'OCTOPRINT'

def send_buffer(buffer : list, payload : dict) -> dict:
    '''
    Send data rows for inference or training
    '''
    try:
        # Payload prepare
        file = None

        data_ = {
            'api_key' : payload.get("api_key"),
            'table' : GENERAL_OCTOPRINT_NAME,
            'uid' : '{}-{}'.format(payload.get("printer_id"), payload.get('tx_id')),
            'overwrite' : False
        }

        fn_ = '{}.csv'.format(uuid4().hex)
        with open(fn_, 'w', newline='') as f:
            write = csv.writer(f)
            write.writerows(buffer)
        #df = pd.DataFrame(buffer[1:], columns=[buffer[0]])
        #df.to_csv(fn_, index=False)
        fu = open(fn_, 'rb')

        files = {
            'file' : ('data{}.csv'.format(payload.get("inc")), fu)
        }

        r = requests.post('{}/{}'.format(ANOMALY_DETECTION_ROUTE, 'api/v1/file/upload'), files=files, data=data_)

        fu.close()
        os.remove(fn_)
        if r.status_code!= 200:
            return ''
        return r.json()
    except Exception as e:
        return str(e)

class AD():
    def __init__(self, plugin) -> None:
        self.run_thread = False
        self.loop = None
        self.buffer_ = []
        self.INTERVAL = 20.0
        self.buffer_max_size_ = 32
        self.last_interval_ = 0.0
        self.tx_ = ''
        self.inc_ = 0
        self.plugin = plugin


    def _get_model_stats(self) -> dict:
        '''
        BETA: all model analysis on WebApp for now
        '''
        return

    def _analyzing(self) -> None:
        '''
        Main process for Anomaly Detector

        Run every second until buffer is full, then
        run inference or train with data if
        printer is not matured.
        '''
        while self.run_thread and self.plugin._settings.get(["enable_detector"]):
            sleep(1.0)
            self.plugin._logger.info('AD main loop: {} | {} | {}'.format(self.run_thread, self.plugin._settings.get(["enable_detector"]), self.plugin._printer.is_printing()))
            if self.plugin._printer.is_printing():
                # Get current printer state data
                self.plugin._logger.info('Attempting to get all stats')
                all_stats_ = get_all_stats(self.plugin._printer)
                self.plugin._logger.info("All stats: {}".format(all_stats_))
                self.buffer_.append(all_stats_)
                # Flush buffer
                if time() - self.last_interval_ > self.INTERVAL or len(self.buffer_) > self.buffer_max_size_:
                    pl_ = {
                        'api_key' : self.plugin._settings.get(["api_key"]),
                        'printer_id' : self.plugin._settings.get(["printer_id"]),
                        'tx_id' : self.tx_,
                        'inc' : self.inc_
                    }
                    tb_ = [list(self.buffer_[0].keys())]
                    tb_.extend([[val if val is not None else -1 for val in list(ele.values())] for ele in self.buffer_])
                    if self.plugin._settings.get(["api_key"]).startswith(tuple(['sub_', 'fmu_'])):
                        r_ = send_buffer(buffer=tb_, payload=pl_)
                        if not isinstance(r_, dict):
                            self.plugin._logger.info('Issue with Anomaly Detector: {}'.format(r_))
                    self.inc_ += 1
                    self.buffer_ = []
                    self.last_interval_ = time()
        self.plugin._logger.info("AD loop broke for some reason: {} | {} | {}".format(self.run_thread, self.plugin._settings.get(["enable_detector"]), self.plugin._printer.is_printing()))


    def start_service(self) -> None:
        '''
        Start analysis service
        '''
        if self.plugin._settings.get(["enable_detector"]):
            if self.loop is None:
                self.run_thread = True
                self.loop = Thread(target=self._analyzing)
                self.loop.daemon = True
                self.loop.start()
                self.plugin._logger.info("PrintWatch anomaly detection service started")



    def kill_service(self) -> None:
        '''
        Kill analysis process
        '''
        self.run_thread = False
        self.loop = None
        self.buffer_ = []
        self.plugin._logger.info("PrintWatch anomaly detection service terminated")
