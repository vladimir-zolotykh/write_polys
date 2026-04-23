#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK


import io
import struct
import pytest

from polyheader import Point, PolyHeader, SizedRecord


def test_point_parsing():
    # Prepare binary data for Point(x=1.5, y=2.5)
    data = struct.pack("<dd", 1.5, 2.5)

    p = Point(data)

    assert p.x == 1.5
    assert p.y == 2.5


def test_point_str():
    data = struct.pack("<dd", 3.0, 4.0)
    p = Point(data)

    assert str(p) == "<class 'Point'>(3.0, 4.0)"


def test_polyheader_parsing():
    # Build a PolyHeader:
    # code=7
    # upper_left=(1.0, 2.0)
    # bottom_right=(3.0, 4.0)
    # num_polys=2
    data = struct.pack("<i dd dd i", 7, 1.0, 2.0, 3.0, 4.0, 2)

    ph = PolyHeader(data)

    assert ph.code == 7
    assert ph.upper_left.x == 1.0
    assert ph.upper_left.y == 2.0
    assert ph.bottom_right.x == 3.0
    assert ph.bottom_right.y == 4.0
    assert ph.num_polys == 2


def test_buf_size_calculation():
    # Point: 2 doubles = 16 bytes
    assert Point.buf_size == struct.calcsize("<dd")

    # PolyHeader: int + Point + Point + int
    expected = (
        struct.calcsize("<i") + Point.buf_size + Point.buf_size + struct.calcsize("<i")
    )
    assert PolyHeader.buf_size == expected


def test_sized_record_with_struct():
    # num_items = 2, then two points as "<dd"
    data = struct.pack("<i dd dd", 2, 1.0, 2.0, 3.0, 4.0)

    f = io.BytesIO(data)
    sr = SizedRecord(f)

    result = list(sr.iter_as("<dd"))

    assert result == [(1.0, 2.0), (3.0, 4.0)]


def test_sized_record_with_fieldbase():
    # num_items = 2, then two Points
    data = struct.pack("<i dd dd", 2, 5.0, 6.0, 7.0, 8.0)

    f = io.BytesIO(data)
    sr = SizedRecord(f)

    result = list(sr.iter_as(Point))

    assert len(result) == 2
    assert result[0].x == 5.0
    assert result[0].y == 6.0
    assert result[1].x == 7.0
    assert result[1].y == 8.0


def test_invalid_format_raises():
    data = struct.pack("<i", 1)
    f = io.BytesIO(data)
    sr = SizedRecord(f)

    with pytest.raises(TypeError):
        list(sr.iter_as(123))  # invalid fmt
