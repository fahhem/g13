"""Benchmark for various g13 code.

Benchmarks the difference between A1 and RGB24 memory layouts and also between
python and C++ (via weave) implementations of the conversion layer.
"""
import math
import struct
import time

import cairo
from scipy import weave

def python_a1(source, dest, width):
  row, col = 0, 0
  for pixels in source:
    pixels = pixels
    for i in xrange(8):
      pixel = pixels & 1
      pixels >>= 1
      idx = 32 + col + (row/8)*width
      if pixel:
        dest[idx] |= 1 << (row % 8)
      else:
        dest[idx] &= ~(1 << (row % 8))

      col += 1
      if col >= width:
        row += 1
        col = 0

def weave_a1(source, dest, width):
  c_code = """
  char* dest_buf = PyByteArray_AsString(dest);

  int row = 0, col = 0;
  for (int pi=0; pi < source.len(); pi++) {
    int pixels = source[pi];
    for (int di=0; di < 8; di++) {

      int pixel = pixels & 1;
      pixels >>= 1;
      int idx = 32 + col + (row >> 3) * %(width)s;
      if (pixel)
        dest_buf[idx] |= 1 << (row & 0x07);
      else
        dest_buf[idx] &= ~(1 << (row & 0x07));

      col++;
      if (col >= %(width)s) {
        col = 0;
        row++;
      }
    }
  }
  """ % {'width': width}
  weave.inline(c_code, ['source', 'dest'])


def python_rgb(source, dest, width):
  threshold = 128
  row, col = 0, 0
  for pi in xrange(len(source)/4):
    data = source[pi*4:pi*4+4]
    pixel = data[1] > threshold and data[2] > threshold and data[3] > threshold
    idx = 32 + col + (row / 8) * width
    if pixel:
      dest[idx] |= 1 << (row % 8)
    else:
      dest[idx] &= ~(1 << (row % 8))

    col += 1
    if col >= width:
      row += 1
      col = 0


def weave_rgb(source, dest, width):
  threshold = 128
  support_code = """
  #define RGB_R(x) ((x&0x00FF0000) >> 16)
  #define RGB_G(x) ((x&0x0000FF00) >> 8)
  #define RGB_B(x) ((x&0x000000FF) >> 0)
  """
  c_code = """
  Py_buffer source_buffer;
  PyObject_GetBuffer(source, &source_buffer, PyBUF_WRITABLE);

  unsigned int* source_buf = (unsigned int*)source_buffer.buf;
  int source_len = source_buffer.len;

  char* dest_buf = PyByteArray_AsString(dest);

  int row = 0, col = 0;
  for (int pi=0; pi < source_len / 4; pi++) {
    int pix = source_buf[pi];
    bool pixel = RGB_R(pix) > %(threshold)s ||
                 RGB_G(pix) > %(threshold)s ||
                 RGB_B(pix) > %(threshold)s;
    int idx = 32 + col + (row >> 3) * %(width)s;
    if (pixel)
      dest_buf[idx] |= 1 << (row & 0x07);
    else
      dest_buf[idx] &= ~(1 << (row & 0x07));

    col++;
    if (col >= %(width)s) {
      col = 0;
      row++;
    }
  }
  """ % {'width': width, 'threshold': threshold}
  weave.inline(c_code, ['source', 'dest'], support_code=support_code)

def benchmark_rgb(func, n=10):
  width = 160
  height = 44
  surface = cairo.ImageSurface(
      cairo.FORMAT_RGB24, width, height)
  source = surface.get_data()
  dest = bytearray(32 + 960+30)

  start = time.time()
  for i in xrange(n):
    func(source, dest, width)
  return time.time() - start

def benchmark_a1(func, n=10):
  width = 160
  height = 44
  surface = cairo.ImageSurface(
      cairo.FORMAT_A1, width, height)
  context = cairo.Context(surface)
  text = 'Benchmark Text'

  context.set_source_rgb(1, 1, 1)
  context.select_font_face('Verdana')
  context.set_font_size(20)
  height = context.text_extents(text)[3]
  context.move_to(0, height)
  context.show_text(text)

  source = bytearray(surface.get_data())
  dest = bytearray(32 + 960)

  start = time.time()
  for i in xrange(n):
    func(source, dest, width)
  return time.time() - start

def benchmark_generic(benchmark_func, func_list):
  for func in func_list:
    print 'Running %s on %s' % (
        benchmark_func.__name__, func.__name__)
    n = 1
    while True:
      dur = benchmark_func(func, n)
      print '%s took %.3fs or %s each' % (n, dur, dur/n)
      if dur > 1:
        break
      if dur < 0.1:
        prevn = n
        n = int(2**math.ceil(math.log(n/dur)))
        if n <= prevn:
          n = prevn * 2
      else:
        n *= 2

if __name__ == '__main__':
  benchmark_generic(benchmark_a1, [python_a1, weave_a1])
  benchmark_generic(benchmark_rgb, [python_rgb, weave_rgb])
