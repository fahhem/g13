import sys
import threading
import time

import usb1
import libusb1

from g13 import G13, MissingG13Error


G13_KEYS = [ # Which bit should be set
    # /* byte 3 */
    'G01',
    'G02',
    'G03',
    'G04',

    'G05',
    'G06',
    'G07',
    'G08',

    # /* byte 4 */
    'G09',
    'G10',
    'G11',
    'G12',

    'G13',
    'G14',
    'G15',
    'G16',

    # /* byte 5 */
    'G17',
    'G18',
    'G19',
    'G20',

    'G21',
    'G22',
    'UN1', # 'UNDEF1',
    'LST', # 'LIGHT_STATE',

    # /* byte 6 */
    'BD',
    'L1',
    'L2',
    'L3',

    'L4',
    'M1',
    'M2',
    'M3',

    # /* byte 7 */
    'MR',
    'LFT',
    'DWN',
    'TOP',

    'UN2', # 'UNDEF2',
    'LT1', # 'LIGHT',
    'LT2', # 'LIGHT2',
    # 'MISC_TOGGLE',
]


class TerminalUI(object):
  BASE_X, BASE_Y = 0, 10
  scale_x, scale_y = 64, 32

  def __init__(self):
    self.prev_x, self.prev_y = 0, 0
    self.prev_keys = {k: 1 for k in G13_KEYS}

  def init_stick(self):
    self.reset()
    sys.stdout.write('-'*(self.scale_x+2) + '\n')
    for l in range(self.scale_y):
      sys.stdout.write('|' + ' ' * self.scale_x + '|\n')
    sys.stdout.write('-'*(self.scale_x+2) + '\n')

  def reset(self):
    self.goto(0, 0)
  def goto(self, x, y):
    sys.stdout.write('\033[%s;%sH' % (self.BASE_Y + y, self.BASE_X + x))
  def down(self, num):
    sys.stdout.write('\033[%sB' % num)
  def right(self, num):
    sys.stdout.write('\033[%sC' % num)
  def print_at(self, x, y, s):
    self.goto(x + 1, y + 1)
    sys.stdout.write(s)
  def flush(self):
    sys.stdout.flush()

  def print_stick(self, x, y):
    x /= 4
    y /= 8

    self.print_at(self.prev_x + 1, self.prev_y, ' ')
    self.print_at(x + 1, y, 'x')

    self.prev_x, self.prev_y = x, y

  def clear_keys(self):
    if not any(self.prev_keys.values()):
      return
    for i in range(5):
      self.print_at(0, self.scale_y + 1 + i, ' '*(4*8))

  def set_key(self, key, value):
    if self.prev_keys[key] != value:
      idx = G13_KEYS.index(key)
      y = self.scale_y + 1 + idx / 8
      x = (idx % 8) * 4
      if value:
        out = key
      else:
        out = '    '
      self.print_at(x, y, out)

    self.prev_keys[key] = value


class G13UI(object):
  def __init__(self, g13):
    self.prev_x, self.prev_y = 0, 0
    self.g13 = g13

  def print_block(self, x, y, val):
    self.g13.set_pixel(x, y, val)
    self.g13.set_pixel(x+1, y, val)
    self.g13.set_pixel(x, y+1, val)
    self.g13.set_pixel(x+1, y+1, val)

  def print_stick(self, x, y):
    x = x * 158 / 255
    y = y *  41 / 255
    self.print_block(self.prev_x, self.prev_y, 0)
    self.print_block(x, y, 1)
    self.prev_x, self.prev_y = x, y


class G13Wrapper(G13):
  def __init__(self):
    super(G13Wrapper, self).__init__()
    self.lock = threading.Lock()

  def write_lcd_bg(self):
    threading.Thread(target=self.write_lcd).start()

  def write_lcd(self):
    if self.lock.acquire(False):
      super(G13Wrapper, self).write_lcd()
      self.lock.release()


def main(argv):
  g13 = G13Wrapper()
  try:
    g13.open()
  except MissingG13Error:
    print 'No G13 found.'
    return

  g13.set_mode_leds(int(time.time() % 16))
  g13.set_color((255, 0, 0))
  time.sleep(0.1)
  g13.set_mode_leds(int(time.time() % 16))
  g13.set_color((255, 255, 255))

  ui = TerminalUI()
  ui.init_stick()
  g13ui = G13UI(g13)

  try:
    while True:
      try:
        keys = g13.get_keys()

        g13ui.print_stick(keys.stick_x, keys.stick_y)
        ui.print_stick(keys.stick_x, keys.stick_y)

        parse_keys(ui, keys)

        ui.flush()
        write_lcd_bg(g13)
      except libusb1.USBError as e:
        if e.value == -7:
          pass
  except Exception as e:
    print e
  except KeyboardInterrupt:
    print '^C'

  g13.close()


def parse_keys(ui, keys):
  if not any(keys.keys):
    ui.clear_keys()
    return

  for i, key in enumerate(G13_KEYS):
    b = keys.keys[i/8]
    ui.set_key(key, b & 1 << (i%8))


if __name__ == '__main__':
  main(sys.argv[1:])

