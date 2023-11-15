#! /usr/bin/env python3

import sys

if __name__ == "__main__":
    raw = sys.argv[1]
    m = eval(raw)
    print("".join([chr(c) for c in m]))
