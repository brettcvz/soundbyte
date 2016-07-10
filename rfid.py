import CHIP_IO.GPIO as GPIO
import spidev


class MFRC522_SPI():
    """
    A class that handles reading/writing to an MFRC522 RFID card reader
    """
    def __init__(self, spi_bus, spi_device, reset_pin=None):
        self.spi = spidev.SpiDev()
        self.spi.open(spi_bus, spi_device)
        self.reset_pin = reset_pin

    def initialize(self):
        GPIO.setup(self.REST_PIN, GPIO.OUT)

        #HIGH = reader enabled, LOW = reader turns off
        GPIO.output(self.RESET_PIN, GPIO.HIGH)

    def cleanup(self):
        GPIO.output(self.RESET_PIN, GPIO.LOW)
        GPIO.cleanup()

    def listen(self, onnewcard):
        """
        Listen for changes, calling onnewcard when we get a new card or one changes
        """
