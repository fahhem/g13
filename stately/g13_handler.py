import libusb1

import g13

class G13Keys(object):
  keys = {
    'G1': (0, 0),
    'G2': (0, 1),
    'G3': (0, 2),
    'G4': (0, 3),
    'G5': (0, 4),
    'G6': (0, 5),
    'G7': (0, 6),
    'G8': (0, 7),

    'G9': (1, 0),
    'G10': (1, 1),
    'G11': (1, 2),
    'G12': (1, 3),
    'G13': (1, 4),
    'G14': (1, 5),
    'G15': (1, 6),
    'G16': (1, 7),

    'G17': (2, 0),
    'G18': (2, 1),
    'G19': (2, 2),
    'G20': (2, 3),
    'G21': (2, 4),
    'G22': (2, 5),
    'UNDEF1': (2, 6),
    'LIGHT_STATE': (2, 7),

    'BD': (3, 0),
    'LCD1': (3, 1),
    'LCD2': (3, 2),
    'LCD3': (3, 3),
    'LCD4': (3, 4),
    'MACRO1': (3, 5),
    'MACRO2': (3, 6),
    'MACRO3': (3, 7),

    'MACRO_RECORD': (4, 0),
    'LEFT': (4, 1),
    'DOWN': (4, 2),
    'TOP': (4, 3),
    'UNDEF2': (4, 4),
    'LIGHT1': (4, 5),
    'LIGHT2': (4, 6),
    'MISC_TOGGLE': (4, 7),
  }
  # Reverse mapping too.
  bytes = {byte_bit: name for name, byte_bit in keys.items()}
  def __getattr__(self, key):
    return self.keys[key]
  __getitem__ = __getattr__

class G13Handler(object):
  def __init__(self):
    self.g13 = g13.G13()
    self.g13.open()
    self.old_keys = [0]*6

  def maybe_get_new_keys(self):
    try:
      new_keys = self.g13.get_keys()
    except libusb1.USBError as e:
      if e.value != -7:  # Ignore timeouts
        raise
      return None, None
    else:
      return new_keys, self.diff_keys(new_keys.keys)

  def diff_keys(self, new_keys):
    diff = bytearray(6)
    for i, (old_byte, new_byte) in enumerate(zip(self.old_keys, new_keys)):
      if old_byte != new_byte:
        diff[i] = new_byte ^ old_byte
    self.old_keys = new_keys
    return diff

