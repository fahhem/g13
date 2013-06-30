import time

class ChromePlugin(object):
  def __init__(self):
    self.reversed = False

  def start_listening(self, state_obj, new_state):
    state_obj.action.register_window_listener(
        self.window_title_filter, self.activate)
  def stop_listening(self, state_obj, new_state):
    state_obj.action.unregister_window_listener(self.window_title_filter)
  def window_title_filter(self, title):
    return title.endswith('Google Chrome')

  def activate(self, state_obj, title):
    print 'activating our state due to title:', title
    state_obj.enter_state('chrome_state')

  def change_tab(self, state_obj, key):
    tab = key[1:]
    # Treat '14' like the last tab, aka 9
    if tab == '14':
      tab = '9'
    state_obj.action.tap_key(tab, state_obj.action.MOD_CONTROL)

  def start_switch_tab(self, state_obj, key):
    state_obj.enter_state('chrome_tab_change')
  def stop_switch_tab(self, state_obj, key):
    state_obj.exit_state('chrome_tab_change')
  def switch_tab(self, state_obj, key):
    print 'switching, stack:', state_obj.stack
    modifiers = state_obj.action.MOD_CONTROL
    if key == 'G20':
       modifiers |= state_obj.action.MOD_SHIFT
    state_obj.action.tap_key('\t', modifiers)
    self.stop_switch_tab(state_obj, key)

  def close_tab(self, state_obj, key):
    if self.reversed:
      state_obj.action.tap_key(
          't', state_obj.action.MOD_CONTROL | state_obj.action.MOD_SHIFT)
    else:
      state_obj.action.tap_key('w', state_obj.action.MOD_CONTROL)

    print 'closing, stack:', state_obj.stack
    self.stop_switch_tab(state_obj, key)
    state_obj.enter_state('chrome_closed_tab')
  def finish_close_tab(self, state_obj, key):
    state_obj.exit_state('chrome_closed_tab')

  def reverse(self, state_obj, key):
    print 'reversing'
    if self.reversed:
      state_obj.exit_state('chrome_reverse')
    else:
      state_obj.enter_state('chrome_reverse')
    self.reversed = not self.reversed

  def page_back(self, state_obj, key):
    state_obj.action.tap_key(
        state_obj.action.KEY_LEFT, state_obj.action.MOD_ALT)
  def page_forward(self, state_obj, key):
    state_obj.action.tap_key(
        state_obj.action.KEY_RIGHT, state_obj.action.MOD_ALT)
  def page_refresh(self, state_obj, key):
    state_obj.action.tap_key(state_obj.action.KEY_F5)

  def __str__(self):
    return self.__class__.__name__
  __repr__ = __str__

def register(state):
  plugin = ChromePlugin()
  nop = lambda s, k: None

  key_press = {
    'G' + str(key+1): plugin.change_tab for key in range(7)+[13]
  }
  key_press['G20'] = plugin.start_switch_tab
  key_press['G22'] = plugin.start_switch_tab
  key_press['LEFT'] = plugin.reverse
  # Back/forward/refresh
  key_press['G15'] = plugin.page_back
  key_press['G16'] = plugin.page_refresh
  key_press['G19'] = plugin.page_forward

  key_release = {
    'G20': plugin.stop_switch_tab,
    'G22': plugin.stop_switch_tab,
    'G21': plugin.finish_close_tab,
    'LEFT': plugin.reverse,
  }

  state.register_plugin(states={
    'default': {
      'enter': plugin.start_listening,
    },

    'chrome_state': {
      'enter': plugin.stop_listening,
      'exit': plugin.start_listening,
      'key_press': key_press,
      'key_release': key_release,
    },
    'chrome_tab_change': {
      'key_press': {
        'G21': plugin.close_tab,
      },
      'key_release': {
        'G20': plugin.switch_tab,
        'G22': plugin.switch_tab,
      }
    },
    'chrome_reverse': {
      'key_press': {
        'G21': plugin.close_tab,
      },
    },
    'chrome_closed_tab': {
      'key_press': {
        'G20': nop,
        'G22': nop,
      }
    }
  })
