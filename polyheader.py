#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import struct


class Field:
    def __init__(self, format: str, offset: int, name=None):
        self._name = name
        self.format = format
        self.offset = offset

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        val = struct.unpack_from(self.format, instance._buffer, self.offset)
        # instance.__dict__[self._name] = val
        return val


class FieldMeta(type):
    def __new__(mcls, clsname, bases, clsdict, **kwargs):
        fields = clsdict.get("_fields", [])
        newdict = dict(clsdict)
        offset: int = 0
        for name, fmt in fields:
            newdict[name] = Field(fmt, offset, name=name)
            offset += struct.calcsize(fmt)
        newdict["buf_size"] = offset
        return super().__new__(mcls, clsname, bases, newdict, **kwargs)


class FieldBase(metaclass=FieldMeta):
    def __init__(self, bytedata):
        self.buffer = memoryview(bytedata)

    @classmethod
    def as_csv(cls):
        return ", ".join(f"{f, cls.__dict__[f]}" for f in cls._fields)


class PolyHeader(FieldBase):
    _fields = [
        ("code", "<i"),
        ("min_x", "<dd"),
        ("min_y", "<dd"),
        ("max_x", "<dd"),
        ("max_y", "<dd"),
        ("num_polys", "<i"),
    ]


if __name__ == "__main__":
    with open("polys.bin", "rb") as f:
        ph = PolyHeader(f.read(PolyHeader.buf_size))
        print(ph.as_csv())
