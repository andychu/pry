# Copyright 2012 Google Inc.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the COPYING file.

"""Library for introspection of a Python process."""

import ctypes
import gc
import linecache
import struct
import sys
import threading
import traceback


ptr_size = struct.calcsize('P')


def _FormatTID(tid):
  """Deal with python sys._current_frames treating thread IDs as signed ints."""
  if ptr_size == 4:
    tid = ctypes.c_ulong(tid).value
  else:
    tid = ctypes.c_ulonglong(tid).value
  return '%x' % tid


def ShowThreads():
  """Formats and returns Python thread stacks."""

  frames = sys._current_frames()  # pylint: disable-msg=W0212
  # A list of (id, thread) tuples.
  threads = []
  if sys.version_info[:2] < (2, 6):
    # 2.4 does not have an 'ident' attribute on Thread objects.  We use
    # threading._active as a hack. Note that we make a copy of _active to
    # iterate over it. We also intentionally ignore threading._limbo.
    threads = threading._active.items()  # pylint: disable-msg=W0212
  else:
    threads = [(t.ident, t) for t in threading.enumerate()]
  thread_names = dict((tid, '(name: %s) ' % t.getName())
                      for tid, t in threads)
  thread_dmode = dict((tid, '(daemon: %s) ' % t.daemon)
                      for tid, t in threads)

  content = ['Python threads:\n\n']
  for thread_id, frame in frames.items():
    content.append('--- Thread %s %s%sstack: ---\n' %
                   (_FormatTID(thread_id), thread_names.get(thread_id, ''),
                    thread_dmode.get(thread_id, '')))
    frame_tuples = []
    while frame:
      filename = frame.f_code.co_filename
      lineno = frame.f_lineno
      line = linecache.getline(filename, lineno)
      if 'google3' in filename:
        filename = '.../' + filename[filename.rindex('google3'):]
      frame_tuples.append((filename, lineno, frame.f_code.co_name, line))
      frame = frame.f_back
    content.extend(traceback.format_list(frame_tuples))
  return ''.join(content)


def HeapTop():
  """Returns Python memory usage statistics as a dict."""

  count = {}
  mem_used = {}
  for obj in gc.get_objects():
    t = type(obj)
    count[t] = count.get(t, 0) + 1
    mem_used[t] = mem_used.get(t, 0) + sys.getsizeof(obj)

  rows = []
  d = {'rows': rows}
  for total_size, type_ in sorted(((v, k) for k, v in mem_used.iteritems()),
                                  reverse=True):
    # convert the type to a string
    rows.append((total_size, count[type_], str(type_)))

  if hasattr(gc, 'is_tracked'):
    # This behavior is new in 2.7 and 3.1.
    d['message'] = (
        'Caution: pry only shows objects tracked by the GC, so it\n'
        'does not include objects of atomic type, or built-in containers\n'
        'with all keys and value of atomic type.\n')

  return d


def ShowHeap(d):
  chunks = ['Python objects (total bytes, count, type):\n\n']
  for row in d['rows']:
    chunks.append('%12s %12s  %s\n' % row)

  message = d.get('message')
  if message:
    chunks.append('\n\n')
    chunks.append(message)
  return ''.join(chunks)


