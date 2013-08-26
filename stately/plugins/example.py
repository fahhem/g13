import threading
import time

class ExamplePlugin(object):
  def default_entered(self, state_obj, new_state):
    # Activates self in 5 seconds, simulates the OS doing so.
    threading.Thread(target=self.self_activate,
                     args=(state_obj,)).start()

  def self_activate(self, state):
    time.sleep(2)
    print 'activating our state'
    state.enter_state('example_state')

  def state_entered(self, state_obj, new_state):
    print 'entered our state'

  def G1_press(self, state_obj, key):
    print 'key pressed', state_obj, key

  def G1_release(self, state_obj, key):
    print 'key released', state_obj, key

  def __str__(self):
    return self.__class__.__name__
  __repr__ = __str__

def register(state):
  plugin = ExamplePlugin()

  state.register_plugin(states={
    'default': {
      'enter': plugin.default_entered,
    },

    'example_state': {
      'enter': plugin.state_entered,
      'key_press': {
        'G1': plugin.G1_press,
      },
      'key_release': {
        'G1': plugin.G1_release,
      },
    },
  })

