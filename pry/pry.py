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


def GetThreadStacks():
  """Returns Python thread stacks.

  Format is a list of dicts.  Each dict is a record representing a thread.
  """
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
  thread_names = dict((tid, t.getName()) for tid, t in threads)
  thread_dmode = dict((tid, t.daemon) for tid, t in threads)

  content = ['Python threads:\n\n']
  threads = []
  for thread_id, frame in frames.items():
    frame_tuples = []
    thread = {
        'id': _FormatTID(thread_id),
        'name': thread_names.get(thread_id, ''),
        'daemon': thread_dmode.get(thread_id, ''),
        'frames': frame_tuples,
        }
    while frame:
      filename = frame.f_code.co_filename
      lineno = frame.f_lineno
      line = linecache.getline(filename, lineno)
      if 'google3' in filename:
        filename = '.../' + filename[filename.rindex('google3'):]

      frame_tuples.append((filename, lineno, frame.f_code.co_name, line))
      frame = frame.f_back

    threads.append(thread)

  # Sort by name
  threads.sort(key=lambda t: t['name'])

  return {'thread-stacks': threads}


def FormatThreadStacks(d):
  chunks = ['Python threads:\n\n']
  for thread in d['thread-stacks']:
    chunks.append('--- Thread %s (name: %s) (daemon: %s) stack: ---\n' %
                   (thread['id'], thread['name'], thread['daemon']))
    frame_tuples = thread['frames']
    chunks.extend(traceback.format_list(frame_tuples))
  return ''.join(chunks)


def GetHeapStats():
  """Returns Python memory usage statistics as a dict."""

  obj_counts = {}  # type -> number of instances
  mem_used = {}  # type -> # bytes
  total_count = 0
  total_bytes = 0

  for obj in gc.get_objects():
    t = type(obj)
    obj_counts[t] = obj_counts.get(t, 0) + 1

    num_bytes = sys.getsizeof(obj)
    mem_used[t] = mem_used.get(t, 0) + num_bytes

    total_count += 1
    total_bytes += num_bytes

  rows = []
  d = {
      'heap-stats': rows,
      'total_num_objects': total_count,
      'total_num_bytes': total_bytes,
      }
  for total_size, type_ in sorted(((v, k) for k, v in mem_used.iteritems()),
                                  reverse=True):
    # convert the type to a string
    count = obj_counts[type_]
    average_size = float(total_size) / count
    rows.append((total_size, count, average_size, str(type_)))

  if hasattr(gc, 'is_tracked'):
    # This behavior is new in 2.7 and 3.1.
    d['message'] = (
        'Caution: pry only shows objects tracked by the GC, so it\n'
        'does not include objects of atomic type, or built-in containers\n'
        'with all keys and value of atomic type.\n')

  return d


def FormatHeapStats(d):
  chunks = ['Python objects (total bytes, count, average, type):\n\n']
  for row in d['heap-stats']:
    chunks.append('%12s %12s %10.1f   %s\n' % row)

  chunks.append('\n')
  chunks.append('Total bytes: %s\n' % d['total_num_bytes'])
  chunks.append('Total number of objects: %s\n' % d['total_num_objects'])

  message = d.get('message')
  if message:
    chunks.append('\n\n')
    chunks.append(message)
  return ''.join(chunks)
