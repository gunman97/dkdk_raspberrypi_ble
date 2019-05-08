import dbus
import dbus.mainloop.glib
from gpiozero import PWMOutputDevice
from time import sleep, time

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

from bluez_components import *

mainloop = None

def int_to_hex(int_value):
    return {
        0: '0',
        1: '1',
        2: '2',
        3: '3',
        4: '4',
        5: '5',
        6: '6',
        7: '7',
        8: '8',
        9: '9',
        10: 'a',
        11: 'b',
        12: 'c',
        13: 'd',
        14: 'e',
        15: 'f'
    }.get(int_value, '0')

def set_vib(motor, row, pulse_time):
    while True:
      motor.value = 0.9
      sleep(0.5)

class RowChrc(Characteristic):
    ROW_UUID = '37836416-3783-6416-3783-64163783001'

    def __init__(self, bus, index, service, row, motor):
        Characteristic.__init__(
            self, bus, index,
            self.ROW_UUID + int_to_hex(row),  # use the row number to build the UUID
            ['read', 'write'],
            service)
        self.value = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.row = row
        self.motor = motor

    def ReadValue(self, options):
        print('RowCharacteristic Read: Row: ' + str(self.row) + ' ' + repr(self.value))
        return self.value

    def WriteValue(self, value, options):
        print('RowCharacteristic Write: Row: ' + str(self.row) + ' ' + repr(value))
        #set_vib(self.motor, value[:2])


class MotorService(Service):
    DKDK_SVC_UUID = '37836416-3783-6416-3783-641637830000'

    def __init__(self, bus, index, motor):
        Service.__init__(self, bus, index, self.DKDK_SVC_UUID, True)
        self.add_characteristic(RowChrc(bus, 0, self, 0, motor))


class MotorApplication(Application):
    def __init__(self, bus, motor):
        Application.__init__(self, bus)
        self.add_service(MotorService(bus, 0, motor))


class MotorAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(MotorService.DKDK_SVC_UUID)
        self.include_tx_power = True


def setup_motor():
    motor = PWMOutputDevice(14)
    return motor


def register_ad_cb():
    """
    Callback if registering advertisement was successful
    """
    print('Advertisement registered')


def register_ad_error_cb(error):
    """
    Callback if registering advertisement failed
    """
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()


def register_app_cb():
    """
    Callback if registering GATT application was successful
    """
    print('GATT application registered')


def register_app_error_cb(error):
    """
    Callback if registering GATT application failed.
    """
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def main():
    global mainloop
    global motor

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    # Get ServiceManager and AdvertisingManager
    service_manager = get_service_manager(bus)
    ad_manager = get_ad_manager(bus)

    # Create gatt services
    motor = setup_motor()
    app = MotorApplication(bus, motor)

    # Create advertisement
    dkdk_advertisement = MotorAdvertisement(bus, 0)

    mainloop = GObject.MainLoop()

    # Register gatt services
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)

    # Register advertisement
    ad_manager.RegisterAdvertisement(dkdk_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Finished")


if __name__ == '__main__':
    main()


