import importlib

import g13
import libusb1
import wx

"""
Plugins are registered by a function in the plugins list by calling
the given argument's register_plugin method. This argument is the
state, and is given to the functions registered for entering/exiting
states. Plugins should call register_plugin with a dictionary of
state names to action dictionaries, which should consist of one or
more of the keys enter, exit, key_press, and key_release.

enter and exit should be functions that take a state argument and
are called when the state with the name they're registered for is
entered or exited.

key_press and key_release should be dictionaries of key names to
functions that take the state object and which key was pressed.
"""

plugins = [
  'plugins.example.register',
]

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

def import_string(modstr):
  mod, func = modstr.rsplit('.', 1)
  module = importlib.import_module(mod)
  return getattr(module, func)

class PluginState(object):
  def __init__(self, handler):
    self.handler = handler
    self.states = {}
    self.stack = []

  @property
  def current_state(self):
    return self.states[self.stack[-1]] if self.stack else None

  def register_plugin(self, states={}):
    for state_name, actions in states.items():
      if state_name not in self.states:
        self.states[state_name] = {}
      state = self.states[state_name]

      enter = actions.get('enter')
      if enter:
        state['enter'] = state.get('enter', [])
        state['enter'].append(enter)

      exit = actions.get('exit')
      if exit:
        state['exit'] = state.get('exit', [])
        state['exit'].append(exit)

      key_press = actions.get('key_press')
      if key_press:
        state['key_press'] = state.get('key_press', {})
        for key in G13Keys.keys:
          if key not in key_press:
            continue
          if key in state['key_press']:
            state['key_press'][key].append(key_press[key])
          else:
            state['key_press'][key] = [key_press[key]]

      key_release = actions.get('key_release')
      if key_release:
        state['key_release'] = state.get('key_release', {})
        for key in G13Keys.keys:
          if key not in key_release:
            continue
          if key in state['key_release']:
            state['key_release'][key].append(key_release[key])
          else:
            state['key_release'][key] = [key_release[key]]

  def handle_state_event(self, event, *args):
    handlers = self.current_state.get(event, [])
    for handler in handlers:
      handler(self, self.current_state, *args)

  def enter_state(self, state_name):
    if state_name == self.current_state:
      return

    self.stack.append(state_name)
    self.handle_state_event('enter')

  def exit_state(self, state_name):
    if state_name != self.current_state:
      return

    self.stack.pop()
    self.handle_state_event('exit')

  def key_changed(self, key, is_pressed):
    if is_pressed:
      keys = self.current_state.get('key_press', {})
    else:
      keys = self.current_state.get('key_release', {})

    funcs = keys.get(key)
    if not funcs:
      return
    [func(self, key) for func in funcs]

if __name__ == '__main__':
  handler = G13Handler()
  state = PluginState(handler)
  for plugin in plugins:
    func = import_string(plugin)
    func(state)

  try:
    wx.App()
  except:
    print 'No GUI'

  state.enter_state('default')
  for _ in range(500):
    new_keys, changed_keys = handler.maybe_get_new_keys()
    if not new_keys:  # Checking for None, not all 0s.
      continue

    # Check/call any registered events.
    for i, byte in enumerate(changed_keys):
      if not byte: # Skip byte early.
        continue
      for j in range(8):
        if byte & 1:
          key = G13Keys.bytes[(i, j)]
          state.key_changed(key, new_keys.keys[i] & (1<<j))
        byte >>= 1

    continue
    for byte in new_keys.keys:
      print hex(byte),
    print
    for byte in changed_keys:
      print hex(byte),
    print
    print
