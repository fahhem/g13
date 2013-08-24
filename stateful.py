import importlib
import threading
import time
import platform

import g13
import libusb1

import autopy
if platform.system() == 'Windows':
  import win32gui
elif platform.system() == 'Linux':
  import subprocess

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
  'plugins.chrome.register',
  'plugins.os.register',
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

class ActionHelper(object):
  def __new__(cls, *args):
    if platform.system() == 'Windows':
      cls = WindowsActionHelper
    elif platform.system() == 'Linux':
      cls = LinuxActionHelper
    return object.__new__(cls, *args)
  def __init__(self, state_obj):
    self.window_registration = {}
    self.state_obj = state_obj

  # Window title functions
  def register_window_listener(self, filter_func, activate_cb):
    self.window_registration[filter_func] = activate_cb
  def unregister_window_listener(self, filter_func):
    del self.window_registration[filter_func]
  def start_window_listener(self):
    self.stop = False
    threading.Thread(target=self.check_window).start()
  def stop_window_listener(self):
    self.stop = True
  def check_window(self):
    while not self.stop:
      if not self.window_registration:
        time.sleep(1)
        continue
      title = self.get_active_window_title()
      for filter_func, activate_cb in self.window_registration.items():
        if filter_func(title):
          activate_cb(self.state_obj, title)
  def press_key(self, key, modifiers=0):
    autopy.key.toggle(key, True, modifiers)
  def release_key(self, key, modifiers=0):
    autopy.key.toggle(key, False, modifiers)
  def tap_key(self, key, modifiers=0):
    autopy.key.tap(key, modifiers)
  # Mouse functions
  def mouse_relative(self, x, y):
    mx, my = autopy.mouse.get_pos()
    try:
      autopy.mouse.move(mx + x, my + y)
    except ValueError:
      pass
  def mouse_toggle(self, down, button):
    autopy.mouse.toggle(down, button)
  # Platform-specific functions
  def get_active_window_title(self):
    pass

# Constants pulled in from autopy for now, we reserve the right to change their
# values, so always pull them from the state object's action instance. To make
# sure, some of the attribute names don't match autopy's. :P
for attr in dir(autopy.key) + dir(autopy.mouse):
  if attr.startswith('MOD_'):
    setattr(ActionHelper, attr, getattr(autopy.key, attr))
  elif attr.startswith('K_'):
    setattr(ActionHelper, 'KEY_' + (attr[2:]), getattr(autopy.key, attr))
  elif attr.endswith('_BUTTON'):
    setattr(ActionHelper,
            'MOUSE_' + attr.split('_')[0],
            getattr(autopy.mouse, attr))

class WindowsActionHelper(ActionHelper):
  def get_active_window_title(self):
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())

class LinuxActionHelper(ActionHelper):
  def get_active_window_title(self):
    return subprocess.Popen(
        ('xdotool', 'getwindowfocus', 'getwindowname'),
        stdout=subprocess.PIPE).communicate()[0]


class PluginState(object):
  def __init__(self, handler):
    self.handler = handler
    self.states = {}
    self.stack = []
    self.action = ActionHelper(self)

  @property
  def current_state(self):
    return self.states[self.current_state_name] if self.stack else None
  @property
  def current_state_name(self):
    return self.stack[-1] if self.stack else None

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

      joystick = actions.get('joystick')
      if joystick:
        state['joystick'] = state.get('joystick', [])
        state['joystick'].append(joystick)

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

  def handle_state_event(self, event):
    handlers = self.current_state.get(event, [])
    for handler in handlers:
      handler(self, self.current_state)

  def enter_state(self, state_name):
    if state_name == self.current_state_name:
      return

    self.stack.append(state_name)
    if state_name not in self.states:
      print 'WARNING: Entering unregistered state:', state_name
      self.states[state_name] = {}
    self.handle_state_event('enter')

  def exit_state(self, state_name):
    # Only pop off states.
    if state_name != self.current_state_name:
      return

    self.handle_state_event('exit')
    self.stack.remove(state_name)

  def key_changed(self, key, is_pressed):
    local_stack = list(self.stack)
    while local_stack:
      state = local_stack.pop()
      if is_pressed:
        keys = self.states[state].get('key_press', {})
      else:
        keys = self.states[state].get('key_release', {})

      funcs = keys.get(key)
      if not funcs:
        # If nothing's registered, try the previous state.
        continue
      [func(self, key) for func in funcs]
      break

  def joystick(self, stick_x, stick_y):
    # Similar to key_changed, but collapsing them will cause a huge
    # hit to readability since joystick isn't a dict while
    # key_press/release is.
    local_stack = list(self.stack)
    while local_stack:
      state = local_stack.pop()
      funcs = self.states[state].get('joystick', [])

      if not funcs:
        continue
      [func(self, stick_x, stick_y) for func in funcs]
      break


def listen_for_keys(handler, state):
  while True: # for _ in range(500):
    new_keys, changed_keys = handler.maybe_get_new_keys()
    if not new_keys:  # Checking for None, not all 0s.
      continue

    # Check/call any registered events.
    state.joystick(new_keys.stick_x, new_keys.stick_y)
    for i, byte in enumerate(changed_keys):
      if not byte: # Skip byte early.
        continue
      for j in range(8):
        if byte & 1:
          key = G13Keys.bytes[(i, j)]
          state.key_changed(key, new_keys.keys[i] & (1<<j))
        byte >>= 1

if __name__ == '__main__':
  handler = G13Handler()
  state = PluginState(handler)
  for plugin in plugins:
    func = import_string(plugin)
    func(state)

  state.enter_state('default')
  state.action.start_window_listener()
  try:
    listen_for_keys(handler, state)
  finally:
    for state_name in reversed(state.stack):
      state.exit_state(state_name)
    state.action.stop_window_listener()

