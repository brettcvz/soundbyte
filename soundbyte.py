from __future__ import print_function

import argparse
import ConfigParser
import signal
import os
import os.path
import importlib
import subprocess
import thread

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
parser.add_argument('-v', '--verbose', action='store_true')


class SoundByte():
    rfid = None
    active_module = None
    verbose = False

    # The one special module_id: hard refresh the list of modules
    REFRESH_MODULE_ID = "8804FC3F4F"

    def initialize(self):
        """
        Set up the audio server, start listening to RFID
        """
        if not self.rfid:
            raise Exception("Cannot initialize without an RFID reader, first call connect_rfid()")

        signal.signal(signal.SIGINT, self.cleanup)
        self.fetch_modules()
        self.rfid.initialize()
        self.modules = {}

    def log(self, *args, **kwargs):
        if self.verbose or kwargs.get("force") == True:
            print(*args)

    def connect_rfid(self, spi_bus=None, spi_device=None, reset_pin=None):
        """
        Create a connection to the RFID read/write device
        """
        self.rfid = rfid.MFRC522_SPI(spi_bus, spi_device, reset_pin)

    def cleanup(self, *args, **kwargs):
        """
        Perform any necessary cleanup tasks to shut down gracefully
        """
        self.log("Performing cleanup")
        if self.active_module:
            self.active_module.stop()
        self.rfid.cleanup()

    def listen(self):
        """
        The primary event loop. Registers a handler for when the RFID reader reads a card,
        and when it gets a card pulls the corresponding module and activates it
        """
        def onnewcard(card_id, card_data):
            self.log("New Card", card_id, card_data)
            #If we no longer have a card and we have an active module, stop the current module
            if not card_id:
                if self.active_module:
                    self.active_module.stop()
                    self.active_module = None
                    self.log("Stopping current module")

                #Either way we return
                return

            # Currently we use IDs, but should switch to data instead
            module_id = card_id

            # The one special module_id: hard refresh the list of modules
            if module_id == self.REFRESH_MODULE_ID:
                self.fetch_modules()
                self.modules = {}
                self.play("refresh_programs.wav")
                return

            if module_id not in self.modules:
                self.log("Loading module", module_id)
                #Caching, both for hits (module found) and misses
                self.modules[module_id] = self.load_module(module_id)

            module = self.modules[module_id]

            if module:
                self.log("Starting module", module_id)
                self.active_module = module
                thread.start_new_thread(module.start, (card_id, card_data))
            else:
                self.log("No available module for", module_id)
                raise NoModuleException(module_id)
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
            self.log("Unhandled Exception:", repr(err), force=True)
        finally:
            if abort:
                self.cleanup()
                self.log("Aborting")
                exit(1)
            else:
                self.listen()

    def load_module(self, module_id):
        """
        Load the module corresponging to the passed in id
        """
        path = "soundbyte-modules.module_%s" % (module_id)
        try:
            mod = importlib.import_module(path)
            return mod
        except ImportError:
            self.fetch_modules()
            try:
                mod = importlib.import_module(path)
                return mod
            except ImportError:
                return None

    def fetch_modules(self):
        """
        Connect to github and download the latest set of modules
        """
        output = subprocess.check_output(["git","submodule","foreach","(git checkout master; git pull; cd ..);"],
                stderr=subprocess.STDOUT)
        self.log(output)
        #TODO: handle output somehow

    def play(self, message):
        subprocess.call(["aplay", "-q", "messages/%s" % (message)])

if __name__ == "__main__":
    args = parser.parse_args()
    config = args.config_file

    s = SoundByte()
    s.verbose = args.verbose
    s.connect_rfid(spi_bus=config.getint("rfid", "spi_bus"),
                   spi_device=config.getint("rfid", "spi_device"),
                   reset_pin=config.get("rfid", "reset_pin"))
    s.initialize()
    s.listen()
