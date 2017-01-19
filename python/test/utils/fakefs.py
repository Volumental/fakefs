#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2017 Volumental AB. CONFIDENTIAL. DO NOT REDISTRIBUTE.
"""Fake filesystem for easy mocking. Usage

# Setup
fs = FakeFilesystem()
fs.add_file('file.txt', data='contents goes here')
fs.monkey.patch()

# Production code
with open('file.txt') as f:
    print(f.read())
"""
import builtins
import io
import os

import shutil
from typing import Union, Callable


class Monkey(object):
    def __init__(self, fs) -> None:
        self.fs = fs
        self.original = {}  # type: Dict[str, Callable]

    def patch(self):
        """Patches relevant functions in builtins, os, and shutil"""
        # `patch`ing does not seem to work for whatever reason
        self.original['open'] = builtins.open
        builtins.open = self.fs.open

        self.original['os.path.exists'] = os.path.exists
        os.path.exists = self.fs.exists

        self.original['shutil.copy'] = shutil.copy
        shutil.copy = self.fs.copy

        self.original['os.rename'] = os.rename
        os.rename = self.fs.rename

        return self

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        builtins.open = self.original['open']
        os.path.exists = self.original['os.path.exists']
        shutil.copy = self.original['shutil.copy']
        os.rename = self.original['os.rename']


class InspectableBytesIO(io.BytesIO):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.the_value = None  # type: bytes

    def close(self) -> None:
        self.the_value = self.getvalue()
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
            f = InspectableBytesIO()
            # TODO(samuel): Make it possible to read back data written during test.
            self.files[p] = FakeFile(b'dummy')
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

    def rename(self, source: str, target: str) -> None:
        s = os.path.normpath(source)
        t = os.path.normpath(target)
        self.files[t] = self.files.pop(s)
