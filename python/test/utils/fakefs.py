#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 Volumental AB. CONFIDENTIAL. DO NOT REDISTRIBUTE.
"""Fake filesystem for easy mocking. Usage

# Setup
fs = FakeFilesystem()
fs.add_file('file.txt', data='contents goes here')
with fs.monkey.patch():

    # Production code
    with open('file.txt') as f:
        print(f.read())
"""
import io
import os

from typing import Callable, Dict, List, Union

from mock import patch


class Monkey(object):
    def __init__(self, fs) -> None:
        self.fs = fs
        self.original = {}  # type: Dict[str, Callable]
        self.patches = []  # type: List[patch]

    def patch(self):
        """Patches relevant functions in builtins, os, and shutil"""
        self.patches.append(patch('builtins.open', self.fs.open))

        self.patches.append(patch('os.path.exists', self.fs.exists))
        self.patches.append(patch('os.path.isfile', self.fs.isfile))
        self.patches.append(patch('os.path.getsize', self.fs.getsize))
        self.patches.append(patch('os.path.isdir', self.fs.isdir))

        self.patches.append(patch('shutil.copy', self.fs.copy))
        self.patches.append(patch('shutil.chown', self.fs.chown))
        self.patches.append(patch('shutil.rmtree', self.fs.rmtree))

        self.patches.append(patch('os.rename', self.fs.rename))
        self.patches.append(patch('os.makedirs', self.fs.makedirs))
        self.patches.append(patch('os.remove', self.fs.remove))
        self.patches.append(patch('os.listdir', self.fs.listdir))

        return self

    def __enter__(self):
        for p in self.patches:
            p.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for p in self.patches:
            p.stop()


class InspectableBytesIO(io.BytesIO):
    def __init__(self, onclose=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.onclose = onclose

    def close(self) -> None:
        if self.onclose:
            self.onclose(self.getvalue())
        super(InspectableBytesIO, self).close()


class FakeFile(object):
    def __init__(self, data: bytes) -> None:
        self.data = data


class FakeFilesystem(object):
    def __init__(self) -> None:
        self.files = {}  # type: Dict[str, FakeFile]
        self.monkey = Monkey(self)

    # Setup functions
    def add_file(self, path: str, data: str) -> None:
        p = os.path.normpath(path)
        self.files[p] = FakeFile(data.encode('utf-8'))

    # Fake functions
    def open(self, path: str, mode: str='r') -> Union[io.BytesIO, io.TextIOWrapper]:
        p = os.path.normpath(path)
        if mode.startswith('r'):
            if p in self.files:
                data = io.BytesIO(self.files[p].data)
                if 'b' in mode:
                    return data
                return io.TextIOWrapper(data)

            raise FileNotFoundError("[Errno 2] No such file or directory: '{}'".format(path))

        if mode.startswith('w'):
            # Add file
            def store_file(content):
                self.files[p] = FakeFile(content)
            f = InspectableBytesIO(store_file)
            if 'b' in mode:
                return f
            return io.TextIOWrapper(f)

        raise ValueError("invalid mode: '{}'".format(mode))

    def exists(self, path: str) -> bool:
        p = os.path.normpath(path)
        return p in self.files

    def copy(self, source: str, target: str) -> None:
        s = os.path.normpath(source)
        t = os.path.normpath(target)
        if s not in self.files:
            raise IOError("Could not copy '{}' to '{}'".format(s, t))
        self.files[t] = self.files[s]

    def chown(self, path: str, user: str, group: str=None):
        p = os.path.normpath(path)
        if p not in self.files:
            raise FileNotFoundError("[Errno 2] No such file or directory: '{}'".format(path))

    def rmtree(self, path):
        p = os.path.normpath(path)
        self.files = {key: value for key, value in self.files.items() if not key.startswith(p)}

    def rename(self, source: str, target: str) -> None:
        s = os.path.normpath(source)
        t = os.path.normpath(target)
        self.files[t] = self.files.pop(s)

    def makedirs(self, path: str, mode: int=0o777, exists_ok: bool=False) -> None:
        # TODO(niko or samuel): Proper directory support
        # Only files exists in the fake fs
        pass

    def isfile(self, path):
        p = os.path.normpath(path)
        return p in self.files

    def getsize(self, path):
        p = os.path.normpath(path)
        if p not in self.files:
            raise FileNotFoundError("[Errno 2] No such file or directory: '{}'".format(path))
        return len(self.files[p].data)

    def isdir(self, path):
        # TODO(niko or samuel): Proper directory support
        p = os.path.normpath(path)
        if p in self.files:
            return False
        return any(file.startswith(p) for file in self.files.keys())

    def remove(self, path):
        p = os.path.normpath(path)
        if p not in self.files:
            raise FileNotFoundError("[Errno 2] No such file or directory: '{}'".format(path))
        del self.files[p]

    def listdir(self, path):
        def first_segment(subpath):
            dirname, basename = os.path.split(subpath)
            if not dirname or dirname == '/':
                return basename
            return first_segment(dirname)

        # list dir also supports passing a file descriptor to directory
        if isinstance(path, int):
            return []

        p = os.path.normpath(path)

        # Handle files
        suffixes = [f[len(p):] for f in self.files.keys() if f.startswith(p)]
        return [first_segment(suff) for suff in suffixes]
