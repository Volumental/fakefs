import unittest
import fakefs
from nose.tools import assert_equal, assert_true, assert_false, raises

import os

class FakeTestCase(unittest.TestCase):
    def run(self, result=None):
        self.fs = fakefs.FakeFilesystem()
        with self.fs.monkey.patch():
            super(FakeTestCase, self).run(result)

    def test_open_write(self):
        with open('/a.txt', 'w') as f:
            f.write('abc')
        assert_equal(b'abc', self.fs.content_for('/a.txt'))
    
    def test_open_read(self):
        self.fs.add_file('/x.txt', "xyz")
        with open('/x.txt') as f:
            data = f.read()
        assert_equal("xyz", data)

    def test_exists_missing(self):
        assert_false(os.path.exists('/nope'))
    
    def test_exists(self):
        self.fs.add_file('/yup', '')
        assert_true(os.path.exists('/yup'))

    @raises(FileNotFoundError)
    def test_getsize_missing(self):
        os.path.getsize('/a')

    def test_getsiz(self):
        self.fs.add_file('/a', '123')
        assert_equal(os.path.getsize('/a'), 3)
