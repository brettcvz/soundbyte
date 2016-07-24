import CHIP_IO.GPIO as GPIO
import spidev
from MFRC522 import MFRC522

import time

class MFRC522_SPI():
    """
    A class that handles reading/writing to an MFRC522 RFID card reader
    """
    POLLING_INTERVAL = 1.0

    def __init__(self, spi_bus, spi_device, reset_pin=None):
        self.spi_bus = spi_bus
        self.spi_device = spi_device
        self.reset_pin = reset_pin

    def initialize(self):
        self.reader = MFRC522.Reader(self.spi_bus, self.spi_device, self.reset_pin)
        self.current_uid = None
        self.listening = False

    def cleanup(self):
        self.listen = False
        GPIO.output(self.reset_pin, GPIO.LOW)
        GPIO.cleanup()

    def listen(self, onnewcard):
        """
        Listen for changes, calling onnewcard when we get a new card or one changes
        """
        self.listening = True

        while self.listening:
            uid, data = self.read_card()

            #"Debounce" when we sometimes can't read a card
            if uid is None and self.current_uid is not None:
                time.sleep(self.POLLING_INTERVAL)
                uid, data = self.read_card()

            print uid
            if uid == self.current_uid:
                time.sleep(self.POLLING_INTERVAL)
                continue

            print "New card!"
            self.current_uid = uid
            onnewcard(uid, None)
            time.sleep(self.POLLING_INTERVAL)

    def read_card(self):
        status, TagType = self.reader.MFRC522_Request(self.reader.PICC_REQIDL)

        if status != self.reader.MI_OK:
            return None, None

        status, uid = self.reader.MFRC522_Anticoll()
        if status != self.reader.MI_OK or uid is None:
            return None, None

        #convert list of ints to hex string
        card_id = "".join(["%0.2X" % (val) for val in uid])

        #TODO: Figure out how to get data later
        return card_id, None
