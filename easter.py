#! /usr/bin/env python3

import datetime


def easter(Y):
    "Meeus/Jones/Butcher algorithm"
    a = Y % 19
    b = Y // 100
    c = Y % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime.date(Y, month, day)


for y in range(1966, 2066):
    print(easter(y))
