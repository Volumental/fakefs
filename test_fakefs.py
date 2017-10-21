import unittest
import fakefs
from nose.tools import assert_equal

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
