"""Action helper for plugins to use.

ActionHelper handles plugins' requested actions, such as listening to window
titles, pressing/releasing/tapping keys, and mouse actions.

WindowWatcher and its platform-specific subclasses, for which it's replaced on
instantiation via __new__, does the actual window title watching.
"""
import platform
import threading
import time

import autopy

if platform.system() == 'Windows':
  import win32gui
elif platform.system() == 'Linux':
  import subprocess


class ActionHelper(object):
  def __init__(self):
    self.window_registration = {}

  # Window title functions
  def register_window_listener(self, filter_func, activate_cb):
    self.window_registration[filter_func] = activate_cb
  def unregister_window_listener(self, filter_func):
    del self.window_registration[filter_func]
  def start_window_listener(self, state_obj):
    self.window_watcher = WindowWatcher(self.window_registration, state_obj)
    self.window_watcher.start()
  def stop_window_listener(self):
    self.window_watcher.stop()

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
    return self.window_watcher.get_active_window_title()

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


class WindowWatcher(threading.Thread):
  def __new__(cls, *args):
    if platform.system() == 'Windows':
      cls = WindowsWindowWatcher
    elif platform.system() == 'Linux':
      cls = LinuxWindowWatcher
    return object.__new__(cls, *args)

  def __init__(self, registration, state_obj):
    self.registration = registration
    self.state_obj = state_obj
    self.stopped = False
    super(WindowWatcher, self).__init__()

  def run(self):
    while not self.stopped:
      if not self.registration:
        time.sleep(1)
        continue
      title = self.get_active_window_title()
      for filter_func, activate_cb in self.registration.items():
        if filter_func(title):
          activate_cb(self.state_obj, title)

  def stop(self):
    self.stopped = True

  def get_active_window_title(self):
    raise NotImplementedError()

class WindowsWindowWatcher(WindowWatcher):
  def get_active_window_title(self):
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())

class LinuxWindowWatcher(WindowWatcher):
  def get_active_window_title(self):
    with open('/dev/null', 'w') as devnull:
      return subprocess.Popen(
          ('xdotool', 'getwindowfocus', 'getwindowname'),
          stdout=subprocess.PIPE, stderr=devnull).communicate()[0]


