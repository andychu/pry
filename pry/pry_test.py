#!/usr/bin/python
#
# Copyright 2012 Google Inc.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the COPYING file.

import unittest
import pprint

import pry


class PryTest(unittest.TestCase):

  def assertIn(self, needle, haystack):
    self.assert_(needle in haystack, haystack)

  def testThreads(self):
    d = pry.GetThreadStacks()
    pprint.pprint(d)
    msg = pry.FormatThreadStacks(d)
    print msg
    self.assertIn('Python threads:', msg)
    self.assertIn('GetThreadStacks()', msg)

  def testHeap(self):
    d = pry.GetHeapStats()
    pprint.pprint(d)
    msg = pry.FormatHeapStats(d)
    print msg
    self.assertIn('Python objects', msg)
    self.assertIn("<type 'dict'>", msg)


if __name__ == '__main__':
  unittest.main()
