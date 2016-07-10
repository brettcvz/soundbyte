import argparse
import ConfigParser
import signal
import os
import os.path
import importlib

import rfid
from errors import SoundByteException, NoModuleException


def type_configfile(string):
    path = os.path.abspath(os.path.expanduser(string))

    if not os.path.exists(path):
        raise argparse.ArgumentTypeError("Error - File not found: %s" % (string))

    config = ConfigParser.ConfigParser()
    config.read(path)
    return config

parser = argparse.ArgumentParser(description='A simple audio server, controlled by RFID')
parser.add_argument('-f', '--config-file', default='~/.config/soundbyte/config', type=type_configfile)


class SoundByte():
    rfid = None
    active_module = None

    def initialize(self):
        """
        Set up the audio server, start listening to RFID
        """
        if not self.rifd:
            raise Exception("Cannot initialize without an RFID reader, first call connect_rfid()")

        signal.signal(signal.SIGINT, self.cleanup)
        self.rifd.initialize()

    def connect_rfid(self, spi_bus=None, spi_device=None, reset_pin=None):
        """
        Create a connection to the RFID read/write device
        """
        self.rfid = rfid.MFRC522_SPI(spi_bus, spi_device, reset_pin)

    def cleanup(self):
        """
        Perform any necessary cleanup tasks to shut down gracefully
        """
        if self.active_module:
            self.active_module.stop()
        self.rifd.cleanup()

    def listen(self):
        """
        The primary event loop. Registers a handler for when the RFID reader reads a card,
        and when it gets a card pulls the corresponding module and activates it
        """
        def onnewcard(card_id, card_data):
            #If we no longer have a card and we have an active module, stop the current module
            if not card_id and self.active_module:
                self.active_module.stop()
                return

            # Currently we use IDs, but should switch to data instead
            module_id = card_id
            module = self.load_module(module_id)
            if not module:
                self.fetch_modules()
                module = self.load_module(module_id)
                if not module:
                    raise NoModuleException(module_id)

            module.start()
        try:
            self.rfid.listen(onnewcard)
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, e):
        #This is a bit lazy, but is easier than doing a big switch
        abort = True
        try:
            raise e
        except SoundByteException as err:
            err.play_error()
            abort = err.abort
        except Exception as err:
            print err
        finally:
            if abort:
                self.cleanup()
                exit(1)
            else:
                self.listen()

    def load_module(self, module_id):
        """
        Load the module corresponging to the passed in id
        """
        path = "modules.module_%d" % (module_id)
        try:
            mod = importlib.import_module(path)
            return mod
        except ImportError:
            return None

    def fetch_modules(self):
        """
        Connect to github and download the latest set of modules
        """

if __name__ == "__main__":
    args = parser.parse_args()
    config = args.config_file

    s = SoundByte()
    s.connect_rfid(spi_bus=config.getint("rfid", "spi_bus"),
                   spi_device=config.getint("rfid", "spi_device"),
                   reset_pin=config.get("rfid", "reset_pin"))
    s.initialize()
    s.listen()
