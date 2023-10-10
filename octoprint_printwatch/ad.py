import asyncio
from threading import Thread
from time import time, sleep
from .utils import *
from uuid import uuid4
import csv
import aiohttp
import os

ANOMALY_DETECTION_ROUTE = 'http://ad.printpal.io'
GENERAL_OCTOPRINT_NAME = 'OCTOPRINT'

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

async def send_buffer(buffer : list, payload : dict) -> dict:
    '''
    Send data rows for inference or training
    '''
    try:
        # Payload prepare
        file = None

        data_ = {
            'api_key' : payload.get("api_key"),
            'table' : GENERAL_OCTOPRINT_NAME,
            'uid' : '{}-{}-{}'.format(payload.get("printer_id"), payload.get('tx_id'), payload.get("inc")),
            'overwrite' : False
        }

        fn_ = '{}.csv'.format(uuid4().hex)

        with open(fn, 'w') as f:
            write = csv.writer(f)
            write.writerows(buffer)

        fu = open(fn, 'rb')

        files = {
            'file' : ('data.csv', fu)
        }

        r = None
        async with aiohttp.ClientSession() as session:
            async with session.post(
                            '{}/{}'.format(ANOMALY_DETECTION_ROUTE, 'api/v1/file/upload'),
                            files = files,
                            data = data_,
                            headers={'User-Agent': 'Mozilla/5.0'},
                            timeout=aiohttp.ClientTimeout(total=10.0)
                        ) as response:
                        r = await response.json()

        fu.close()
        os.remove(fn)
        print('AD response: {}'.format(r))
        return r
    except Exception as e:
        return str(e)

class AD():
    def __init__(self, plugin) -> None:
        self.run_thread = False
        self.loop = None
        self.aio = None
        self.buffer_ = []
        self.INTERVAL = 60.0
        self.buffer_max_size_ = 128
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
            if self.plugin._printer.is_printing():
                # Get current printer state data
                self.buffer_.append(get_all_stats(self.plugin._printer))
                # Flush buffer
                if time() - self.last_interval_ > self.INTERVAL or len(self.buffer_) > self.buffer_max_size_:
                    pl_ = {
                        'api_key' : self.plugin._settings.get(["api_key"]),
                        'printer_id' : self.plugin._settings.get(["printer_id"]),
                        'tx_id' : self.tx_,
                        'inc' : self.inc_
                    }
                    self.aio.run_until_complete(send_buffer(buffer=self.buffer_, payload=pl_))
                    self.inc_ += 1
                    self.buffer_ = []
                    self.last_interval_ = time()


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
                self.aio = get_or_create_eventloop()
                asyncio.set_event_loop(self.aio)
                self.plugin._logger.info("PrintWatch anomaly detection service started")



    def kill_service(self) -> None:
        '''
        Kill analysis process
        '''
        self.run_thread = False
        self.loop = None
        self.buffer_ = []
        self.plugin._logger.info("PrintWatch anomaly detection service terminated")
