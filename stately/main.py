import importlib
import sys
sys.path.insert(0, 'deps')

from g13_handler import G13Handler, G13Keys
from actions import ActionHelper
from state import PluginState

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
  # 'plugins.example.register',
  'plugins.chrome.register',
  'plugins.os.register',
]

def import_string(modstr):
  mod, func = modstr.rsplit('.', 1)
  module = importlib.import_module(mod)
  return getattr(module, func)

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
  action_helper = ActionHelper()
  state = PluginState(handler, action_helper)
  for plugin in plugins:
    func = import_string(plugin)
    func(state)

  state.enter_state('default')
  state.action.start_window_listener(state)
  try:
    listen_for_keys(handler, state)
  finally:
    for state_name in reversed(state.stack):
      state.exit_state(state_name)
    state.action.stop_window_listener()

