"""Encompasses the state stack as given to the plugins.

Plugins get registered for various actions in each state they wish. This object
is then passed into plugins that are triggered for those actions.
"""

from g13_handler import G13Keys

class PluginState(object):
  def __init__(self, handler, action_helper):
    self.handler = handler
    self.states = {}
    self.stack = []

    self.action = action_helper

  @property
  def current_state(self):
    return self.states[self.current_state_name] if self.stack else None
  @property
  def current_state_name(self):
    return self.stack[-1] if self.stack else None

  def _register_action(self, state, actions, action_name):
    action = actions.get(action_name)
    if action:
      state[action_name] = state.get(action_name, [])
      state[action_name].append(action)

  def _register_key_action(self, state, actions, key_action_name):
    key_action = actions.get(key_action_name)
    if key_action:
      state[key_action_name] = state.get(key_action_name, {})
      for key in G13Keys.keys:
        if key not in key_action:
          continue
        if key in state[key_action_name]:
          state[key_action_name][key].append(key_action[key])
        else:
          state[key_action_name][key] = [key_action[key]]

  def register_plugin(self, states={}):
    for state_name, actions in states.items():
      if state_name not in self.states:
        self.states[state_name] = {}
      state = self.states[state_name]

      self._register_action(state, actions, 'enter')
      self._register_action(state, actions, 'exit')
      self._register_action(state, actions, 'joystick')

      self._register_key_action(state, actions, 'key_press')
      self._register_key_action(state, actions, 'key_release')

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

