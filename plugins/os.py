import threading
import time

class OSPlugin(object):
  def __init__(self):
    self.relative = 0, 0
  def start_mouse_thread(self, state_obj, new_state):
    self.stopped = False
    threading.Thread(target=self.move_mouse,
                     args=(state_obj,)).start()
  def stop_mouse_thread(self, state_obj, new_state):
    self.stopped = True
  def move_mouse(self, state_obj):
    while not self.stopped:
      time.sleep(0.01)
      if self.relative:
        state_obj.action.mouse_relative(*self.relative)
  def joystick_relative(self, state_obj, stick_x, stick_y):
    x = -((127 - stick_x) / 20)
    y = -((127 - stick_y) / 20)
    self.relative = x, y
    # print x, y, stick_x, stick_y
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
