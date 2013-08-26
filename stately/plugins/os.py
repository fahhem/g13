import threading
import time

class MouseThread(threading.Thread):
  daemon = True
  def __init__(self, state_obj):
    self.state = state_obj
    self.relative = tuple()
    self.stopped = False
    super(MouseThread, self).__init__()

  def run(self):
    while not self.stopped:
      time.sleep(0.01)
      if self.relative:
        self.state.action.mouse_relative(*self.relative)
  def stop(self):
    self.stopped = True

  def set_relative(self, x, y):
    self.relative = x, y

class OSPlugin(object):
  def start_mouse_thread(self, state_obj, new_state):
    self.mouse_thread = MouseThread(state_obj)
    self.mouse_thread.start()
  def stop_mouse_thread(self, state_obj, new_state):
    self.mouse_thread.stop()
  def joystick_relative(self, state_obj, stick_x, stick_y):
    x = -((127 - stick_x) / 15)
    y = -((127 - stick_y) / 15)
    if x == -1 and stick_x >= 107:
      # It sometimes gets stuck here.
      x = 0
    self.mouse_thread.set_relative(x, y)
  def click(self, state_obj, key):
    if key == 'G17':
      button = state_obj.action.MOUSE_LEFT
    elif key == 'G18':
      button = state_obj.action.MOUSE_RIGHT
    state_obj.action.mouse_toggle(True, button=button)
  def unclick(self, state_obj, key):
    if key == 'G17':
      button = state_obj.action.MOUSE_LEFT
    elif key == 'G18':
      button = state_obj.action.MOUSE_RIGHT
    state_obj.action.mouse_toggle(False, button=button)

def register(state):
  plugin = OSPlugin()
  state.register_plugin(states={
    'default': {
      'enter': plugin.start_mouse_thread,
      'exit': plugin.stop_mouse_thread,
      'joystick': plugin.joystick_relative,
      'key_press': {
        'G17': plugin.click,
        'G18': plugin.click,
      },
      'key_release': {
        'G17': plugin.unclick,
        'G18': plugin.unclick,
      }
    }
  })
