Cross-platform userspace driver for the Logitech G13
===================================================

Based in Python for faster coding. If speed becomes a problem I can switch to
SWIG-wrapping a C driver.

Currently tested with Windows 7 and Ubuntu Linux for compatibility, just install
python-libusb1_ or copy usb1.py and libusb1.py next to g13.py.

ui_example.py just shows how to interact with the G13 and exposes much of the
functionality via the terminal.

Dependencies
------------

* python-libusb1_


.. _python-libusb1: https://github.com/vpelletier/python-libusb1
