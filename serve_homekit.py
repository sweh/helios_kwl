#!./bin/python

from pathlib import Path
from pyhap.accessory import Accessory
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_AIR_CONDITIONER
from helios_com import COM
import signal

path = Path(__file__).parent / 'helios.state'


LEVELS = {
    0: (0, 0),
    1: (1, 33),
    2: (34, 66),
    3: (67, 99),
    4: (100, 100),
}


def to_percent(level):
    min_, max_ = LEVELS[level]
    return int((min_ + max_) / 2)


def from_percent(percent):
    for level, range_ in LEVELS.items():
        min_, max_ = range_
        if percent >= min_ and percent <= max_:
            return level


def get_data():
    com = COM('10.0.1.64')
    try:
        fanLevel = com.read_fan_stage()
        outTemp, suppTemp, exhaustTemp, extractTemp = com.read_temp()
        exhaustHumid = com.read_humidity()
    finally:
        com.exit()
    return (
        to_percent(fanLevel),
        exhaustHumid,
        outTemp,
        suppTemp,
        exhaustTemp,
        extractTemp
    )


def set_level(level):
    com = COM('10.0.1.64')
    try:
        com.set_fan_stage(from_percent(level))
    finally:
        com.exit()


def get_machine_info():
    return {
        'SerialNumber': '5405',
        'Model': 'KWL EX 200W ET R',
        'Manufacturer': 'Helios',
    }


class HeliosSwitch(Accessory):
    category = CATEGORY_AIR_CONDITIONER

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_fan()
        self.add_humidity_sensor()
        self.add_outtemp_sensor()
        self.add_supptemp_sensor()
        self.add_exhausttemp_sensor()
        self.add_extracttemp_sensor()

    def add_humidity_sensor(self):
        self.humidity = self.add_preload_service(
            'HumiditySensor'
        ).configure_char('CurrentRelativeHumidity')

    def add_outtemp_sensor(self):
        self.outtemp = self.add_preload_service(
            'TemperatureSensor'
        ).configure_char('CurrentTemperature')

    def add_supptemp_sensor(self):
        self.supptemp = self.add_preload_service(
            'TemperatureSensor'
        ).configure_char('CurrentTemperature')

    def add_exhausttemp_sensor(self):
        self.exhausttemp = self.add_preload_service(
            'TemperatureSensor'
        ).configure_char('CurrentTemperature')

    def add_extracttemp_sensor(self):
        self.extracttemp = self.add_preload_service(
            'TemperatureSensor'
        ).configure_char('CurrentTemperature')

    def add_fan(self):
        serv_fan = self.add_preload_service(
            'Fan', chars=['On', 'RotationSpeed'])

        self.char_fan_on_off = serv_fan.configure_char(
            'On', setter_callback=self.set_fan_on_off)

        self.char_rotation_speed = serv_fan.configure_char(
            'RotationSpeed', setter_callback=self.set_rotation_speed)

    def add_info_service(self):
        info_service = self.driver.loader.get_service('AccessoryInformation')
        info_service.configure_char('Name', value='Lüfter')
        for name, value in get_machine_info().items():
            info_service.configure_char(name, value=value)
        self.add_service(info_service)

    @Accessory.run_at_interval(10)
    def run(self):

        level, humidity, out, supp, exhaust, extract = get_data()

        self.humidity.value = humidity
        self.humidity.notify()

        self.outtemp.value = out
        self.outtemp.notify()

        self.supptemp.value = supp
        self.supptemp.notify()

        self.exhausttemp.value = exhaust
        self.exhausttemp.notify()

        self.extracttemp.value = extract
        self.extracttemp.notify()

        if self.char_rotation_speed.value != level:
            self.char_rotation_speed.value = level
            self.char_rotation_speed.notify()

        if not self.char_fan_on_off.value and level:
            self.char_fan_on_off.value = True
            self.char_fan_on_off.notify()

        if self.char_fan_on_off.value and not level:
            self.char_fan_on_off.value = False
            self.char_fan_on_off.notify()

    def set_rotation_speed(self, level):
        set_level(level)

    def set_fan_on_off(self, status):
        if not status:
            set_level(0)
        else:
            set_level(50)


if __name__ == '__main__':
    driver = AccessoryDriver(
        # port=random.randint(50000, 51000),
        port=8088,
        persist_file=path.resolve(),
    )
    driver.add_accessory(accessory=HeliosSwitch(driver, 'Helios'))

    signal.signal(signal.SIGTERM, driver.signal_handler)
    driver.start()
