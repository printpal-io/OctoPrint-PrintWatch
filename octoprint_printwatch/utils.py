import psutil
import platform
from time import time

def _flatten_dict(pyobj : dict, keystring : str ='') -> dict:
    if type(pyobj) == dict:
        keystring = keystring + '_' if keystring else keystring
        for k in pyobj:
            yield from _flatten_dict(pyobj[k], keystring + str(k))
    else:
        yield keystring, pyobj

def flatten_dict(input_dict : dict) -> dict:
    return {k:v for k,v in _flatten_dict(input_dict)}

def ps_util_get_stats() -> dict:
    """
    Credit:
    - function written by j7126
    - original link: https://github.com/j7126/OctoPrint-Dashboard

    Description:
    - Gets system stats using psutil
    - sets cpu_temp, cpu_percent, cpu_freq, virtual_memory_percent and disk_usage
    """
    if platform.system() == "Linux":
        temp_sum = 0
        response_ = {}
        thermal = psutil.sensors_temperatures(fahrenheit=False)
        if "cpu-thermal" in thermal:  # RPi
            response_["cpu_temp"] = float((thermal["cpu-thermal"][0][1]))
        elif "cpu_thermal" in thermal:  # RPi Alternative
            response_["cpu_temp"] = float((thermal["cpu_thermal"][0][1]))
        elif 'soc_thermal' in thermal:  # BananaPi
            response_["cpu_temp"] = float(thermal['soc_thermal'][0][1])*1000
        elif 'coretemp' in thermal:  # Intel
            for temp in range(0, len(thermal["coretemp"]), 1):
                temp_sum = temp_sum+thermal["coretemp"][temp][1]
            response_["cpu_temp"] = float(temp_sum / len(thermal["coretemp"]))
        elif 'w1_slave_temp' in thermal:  # Dallas temp sensor fix
            with open('/sys/class/thermal/thermal_zone0/temp') as temp_file:
                cpu_val = temp_file.read()
                response_["cpu_temp"] = float(cpu_val)/1000
        elif "cpu" in thermal:  # RockPi (probably all RockChip CPUs/SOCs)
            response_["cpu_temp"] = float((thermal["cpu"][0][1]))
        elif 'cpu_thermal_zone' in thermal: #OrangePI_Zero2
            response_["cpu_temp"] = float((thermal["cpu_thermal_zone"][0][1]))
        elif "scpi_sensors" in thermal: # Le Potato sbc
            response_["cpu_temp"] = float((thermal["scpi_sensors"][0][1]))
        elif "sunxi-therm-1" in thermal: # Orange Pi Zero Plus 2 H3
            response_["cpu_temp"] = float(thermal["sunxi-therm-1"][0][1] * 1000)
            if "sunxi-therm-2" in thermal:
                # ok, get max temp
                response_["cpu_temp"] = max([float(thermal["sunxi-therm-2"][0][1] * 1000), response_["cpu_temp"]])
        response_["cpu_percent"] = float(psutil.cpu_percent(interval=None, percpu=False))
        response_["cpu_freq"] = float(psutil.cpu_freq(percpu=False).current)
        response_["virtual_memory_percent"] = float(psutil.virtual_memory().percent)
        response_["disk_usage"] = float(psutil.disk_usage("/").percent)

        return response_

def oprint_get_stats(printer) -> dict:
    response_ = {}
    current_state_ = printer.get_current_data()
    response_["resends"] = current_state_.get("resends", {})
    current_temps_ = printer.get_current_temperatures()
    response_["current_temps"] = current_temps_
    return response_

def get_all_stats(printer) -> dict:
    all_stats_ = {"timestamp" : round(time())}
    cpu_stats_ = ps_util_get_stats()
    oprint_stats_ = oprint_get_stats(printer)
    all_stats_['cpu'] = cpu_stats_
    all_stats_['oprint'] = oprint_stats_
    all_stats_ = flatten_dict(all_stats_)
    return all_stats_
