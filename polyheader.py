#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Iterator, BinaryIO, ClassVar, Any, Union, cast
import struct
import pprint
import writepolys
from typing import Protocol


class SizedField(Protocol):
    """Has buf_size attr"""

    buf_size: int


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
        o = self.offset
        val = self.sub_type(instance.buffer[o:])
        instance.__dict__[self._name] = val
        return val


class FieldMeta(type):
    def __new__(mcls, clsname, bases, clsdict, **kwargs):
        fields = clsdict.get("_fields", [])
        newdict = dict(clsdict)
        offset: int = 0
        for name, fmt_or_class in fields:
            if isinstance(fmt_or_class, str):
                fmt: str = fmt_or_class
                newdict[name] = Field(fmt, offset, name=name)
                offset += struct.calcsize(fmt)
            elif isinstance(fmt_or_class, FieldMeta):
                newtype: SizedField = cast(SizedField, fmt_or_class)
                newdict[name] = NestedType(newtype, offset, name=name)
                offset += newtype.buf_size
            else:
                raise TypeError(f"{fmt_or_class}: expected str or FieldBase")
        newdict["buf_size"] = offset
        return super().__new__(mcls, clsname, bases, newdict, **kwargs)


class FieldBase(metaclass=FieldMeta):
    _fields: ClassVar[list[tuple[str, Any]]] = []
    buf_size: ClassVar[int]

    def __init__(self, bytedata):
        self.buffer = memoryview(bytedata)

    def as_csv(self):
        return ", ".join(f"{name}={getattr(self, name)}" for name, _ in self._fields)

    __str__ = as_csv


class Point(FieldBase):
    _fields = [
        ("x", "<d"),
        ("y", "<d"),
    ]
    x: float
    y: float

    def __str__(self):
        return f"<class {self.__class__.__name__!r}>({self.x}, {self.y})"


class PolyHeader(FieldBase):
    _fields = [
        ("code", "<i"),
        ("upper_left", Point),
        ("bottom_right", Point),
        ("num_polys", "<i"),
    ]
    num_polys: int


class SizedRecord:
    def __init__(self, f: BinaryIO):
        self.f = f
        s = struct.Struct("<i")
        self.num_items = s.unpack(f.read(s.size))[0]

    def iter_as(self, fmt: str | type[FieldBase] = "<dd") -> Iterator[Any]:
        for _ in range(self.num_items):
            if isinstance(fmt, str):
                s = struct.Struct(fmt)
                buf = self.f.read(s.size)
                yield s.unpack(buf)
            elif isinstance(fmt, FieldBase):
                field_type: type[FieldBase] = fmt
                buf = self.f.read(field_type.buf_size)
                yield field_type(buf)
            else:
                raise TypeError(f"{fmt}: expected str or FieldBase-based class")


if __name__ == "__main__":
    with open("polys.bin", "rb") as f:
        ph = PolyHeader(f.read(PolyHeader.buf_size))
        print(ph.as_csv())
        # poly = [[p for p in SizedRecord(f).iter_as("<dd")] for _ in range(ph.num_polys)]
        # assert poly == writepolys.polys
        # pprint.pprint(poly)
        poly = [
            [str(p) for p in SizedRecord(f).iter_as(Point)] for _ in range(ph.num_polys)
        ]
        print(poly)
