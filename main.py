import _thread
import pyudev

class USBDetector():
    ''' Monitor udev for detection of usb '''
 
    def __init__(self):
        self._listen()

    def _listen(self):
        while True:
            ''' Runs the actual loop to detect the events '''
            self.context = pyudev.Context()
            self.monitor = pyudev.Monitor.from_netlink(self.context)
            self.monitor.filter_by(subsystem='usb')
            # this is module level logger, can be ignored
            LOGGER.info("Starting to monitor for usb")
            self.monitor.start()
            for device in iter(self.monitor.poll, None):
                LOGGER.info("Got USB event: %s", device.action)
                if device.action == 'add':
                    # some function to run on insertion of usb
                    self.on_created()
                else:
                    # some function to run on removal of usb
                    self.on_deleted()

                
if __name__ == '__main__':
    print("This only executes when %s is executed rather than imported" % __file__)
    usbd = USBDetector()