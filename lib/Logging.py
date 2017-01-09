class Logger:
    """
    Class to steer output
    """

    def __init__(self):
        self.state = {'debug': False, 'info': False, 'warn': False, 'error': True}
        self.tape = []

    def log(self, msg, level='info'):
        if self.state[level]:
            self.print_level(level, msg)

        self.record(level, msg)

    def set_state(self, state_id, val='True'):
        self.state[state_id] = val

    def toggle_state(self, state_id):
        self.state[state_id] = not self.state[state_id]

    def print_level(self, level, msg):
        if level is 'debug':
            self.print_debug(msg)
        elif level is 'info':
            self.print_info(msg)
        elif level is 'warn':
            self.print_warn(msg)
        elif level is 'error':
            self.print_error(msg)

    def print_debug(self, msg):
        msg_str = '[Debug] // Start\n' + str(msg) + '\n[Debug] // End'
        print(msg_str)

    def print_info(self, msg):
        msg_str = '[Info] ' + str(msg)
        print(msg_str)

    def print_warn(self, msg):
        msg_str = '[Warning!] ' + str(msg)
        print(msg_str)

    def print_error(self, msg):
        msg_str = '[Error] ' + str(msg)
        print(msg_str)

    def record(self, level, msg):
        msg_str = '[' + level + '] ' + str(msg)
        self.tape.append(msg_str)

    def dump_tape(self):
        for msg in self.tape:
            print(msg)


logger = Logger()


def get_logger():
    return logger