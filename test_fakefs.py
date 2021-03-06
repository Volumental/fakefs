import unittest
import fakefs
from nose.tools import assert_equal, assert_true, assert_false, raises

import os
import shutil
import tempfile


class FakeTestCase(unittest.TestCase):
    def run(self, result=None):
        self.fs = fakefs.FakeFilesystem()
        with self.fs.monkey.patch():
            super(FakeTestCase, self).run(result)
    
    def test_open_write_missing(self):
        with open('/a.txt', 'w') as f:
            f.write('abc')
        assert_equal(b'abc', self.fs.content_for('/a.txt'))
    
    def test_open_write_existing(self):
        self.fs.add_file('/a.txt', 'original')
        with open('/a.txt', 'w') as f:
            f.write('abc')
        assert_equal(b'abc', self.fs.content_for('/a.txt'))
    
    def test_open_read(self):
        self.fs.add_file('/x.txt', "xyz")
        with open('/x.txt') as f:
            data = f.read()
        assert_equal("xyz", data)

    @raises(FileNotFoundError)
    def test_open_read_missing(self):
        with open('/x.txt') as f:
            pass

    def test_open_append_missing(self):
        with open('/a.txt', 'a') as f:
            f.write('abc')
        assert_equal(b'abc', self.fs.content_for('/a.txt'))

    def test_open_append_existing(self):
        self.fs.add_file('/a.txt', 'abc')
        with open('/a.txt', 'a') as f:
            f.write('123')
        assert_equal(b'abc123', self.fs.content_for('/a.txt'))
        
    @raises(ValueError)
    def test_open_bad_mode(self):
        with open('whatever', 'does not start with r, w, nor a'):
            pass

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

    def test_isdir_missing(self):
        assert_false(os.path.isdir('/dir'))

    def test_isdir_file(self):
        self.fs.add_file('/file', '')
        assert_false(os.path.isdir('/file'))

    def test_isdir(self):
        self.fs.add_file('/dir/file', '')
        assert_true(os.path.isdir('/dir'))

    @raises(FileNotFoundError)
    def test_rename_missing(self):
        os.rename('/nope', 'whatever')

    def test_rename(self):
        self.fs.add_file('/before', '')
        os.rename('/before', '/after')
        assert_true(os.path.isfile('/after'))

    @raises(FileNotFoundError)
    def test_listdir_missing(self):
        os.listdir('/nope')

    def test_listdir_empty(self):
        os.mkdir('/empty')
        assert_equal(os.listdir('/empty'), [])

    def test_listdir_single(self):
        self.fs.add_file('/single/file', '')
        assert_equal(os.listdir('/single'), ['file'])

    @raises(FileNotFoundError)
    def test_stat_missing(self):
        os.stat('/nope')
    
    def test_stat(self):
        self.fs.add_file('/file', '123')
        stat = os.stat('/file')
        assert_equal(stat.st_mtime, 0)

    @raises(FileNotFoundError)
    def test_remove_missing(self):
        os.remove('/nope')
    
    def test_remove(self):
        self.fs.add_file('/file', '123')
        os.remove('/file')
        assert_false(os.path.isfile('/file'))

    # shutil
    @raises(OSError)
    def test_copy_missing(self):
        shutil.copy('/nope', 'whatever')

    def test_copy_old_still_there(self):
        self.fs.add_file('/a', 'a')
        shutil.copy('/a', '/b')
        assert_true(os.path.isfile('/a'))

    def test_copy_new_content(self):
        self.fs.add_file('/a', 'a')
        shutil.copy('/a', '/b')
        assert_equal(self.fs.content_for('/b'), b'a')

    @raises(FileNotFoundError)
    def test_chown_missing(self):
        shutil.chown('/nope', 'whatever')

    def test_chown(self):
        self.fs.add_file('/file', '')
        shutil.chown('/file', 'whatever')
        # chown just dummy, nothing to assert.

    def test_rmtree(self):
        self.fs.add_file('/dir/dir/file', '')
        shutil.rmtree('/dir')
        assert_false(os.path.isfile('/dir/dir/file'))
        assert_false(os.path.isdir('/dir/dir'))
        assert_false(os.path.isdir('/dir'))

    # tempfile
    def test_temporary_directory(self):
        with tempfile.TemporaryDirectory() as name:
            assert_true(os.path.isdir(name))
