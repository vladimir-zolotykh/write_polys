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
        val = struct.unpack_from(self.format, instance.buffer, self.offset)
        # instance.__dict__[self._name] = val
        return val[0] if len(val) == 1 else val


class NestedType(Field):
    def __init__(self, sub_type, offset, name=None):
        self.sub_type = sub_type
        self.offset = offset
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        val = self.sub_type(self.offset)
        instance.__dict__[self._name] = val
        return val


class FieldMeta(type):
    def __new__(mcls, clsname, bases, clsdict, **kwargs):
        fields = clsdict.get("_fields", [])
        newdict = dict(clsdict)
        offset: int = 0
        for name, fmt_or_class in fields:
            print(fmt_or_class)
            if isinstance(fmt_or_class, str):
                fmt: str = fmt_or_class
                newdict[name] = Field(fmt, offset, name=name)
                offset += struct.calcsize(fmt)
            elif isinstance(fmt_or_class, FieldMeta):
                newtype: type = fmt_or_class
                newdict[name] = NestedType(newtype, offset, name=name)
                offset += newtype.buf_size
            else:
                raise TypeError(f"{fmt_or_class}: expected str or FieldBase")
        newdict["buf_size"] = offset
        return super().__new__(mcls, clsname, bases, newdict, **kwargs)


class FieldBase(metaclass=FieldMeta):
    def __init__(self, bytedata):
        self.buffer = memoryview(bytedata)

    def as_csv(self):
        return ", ".join(f"{name}={getattr(self, name)}" for name, _ in self._fields)


class Point(FieldBase):
    _fields = [
        ("x", "<d"),
        ("y", "<d"),
    ]


class PolyHeader(FieldBase):
    _fields = [
        ("code", "<i"),
        ("upper_left", Point),
        ("bottom_right", Point),
        ("num_polys", "<i"),
    ]


if __name__ == "__main__":
    with open("polys.bin", "rb") as f:
        ph = PolyHeader(f.read(PolyHeader.buf_size))
        print(ph.as_csv())
