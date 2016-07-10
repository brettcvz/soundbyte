class SoundByteException(Exception):
    def __init__(self, message, abort=True):
        self.message = message
        self.abort = abort

    def play_error(self):
        #This would speak the error message
        print("Had error: %s, play message: %s" % (self, self.message))


class NoModuleException(SoundByteException):
    def __init__(self, module_id):
        super(NoModuleException, self).__init__("no_module.wav", abort=False)
        self.module_id = module_id
