import subprocess

class SoundByteException(Exception):
    def __init__(self, message, abort=True):
        self.message = message
        self.abort = abort

    def play_error(self):
        subprocess.call(["aplay", "-q", "messages/%s" % (self.message)])


class NoModuleException(SoundByteException):
    def __init__(self, module_id):
        super(NoModuleException, self).__init__("not_found.wav", abort=False)
        self.module_id = module_id

class CannotReadCardException(SoundByteException):
    def __init__(self):
        super(CannotReadCardException, self).__init__("cannot_read_card.wav", abort=False)
