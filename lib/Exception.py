class PiraException(Exception):

  def __init__(self, message):
    super().__init__()
    self._message = message

  def __str__(self):
    return self._message
