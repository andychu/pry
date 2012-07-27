#!/usr/bin/python
#
# Copyright 2012 Google Inc.  All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found
# in the COPYING file.

import unittest

import pry


class PryTest(unittest.TestCase):

  def assertIn(self, needle, haystack):
    self.assert_(needle in haystack, haystack)

  def testShowThreads(self):
    msg = pry.ShowThreads()
    print msg
    self.assertIn('Python threads:', msg)
    self.assertIn('ShowThreads()', msg)

  def testShowHeap(self):
    d = pry.HeapTop()
    print d
    msg = pry.ShowHeap(d)
    print msg
    self.assertIn('Python objects', msg)
    self.assertIn("<type 'dict'>", msg)


if __name__ == '__main__':
  unittest.main()
