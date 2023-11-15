#! /usr/bin/env python3

import sys
import base64
import json


def main(argv):
    infile = open(argv[1]) if len(argv) > 1 else sys.stdin
    jwt = infile.read().strip()
    head, body, sign = jwt.split(".")
    for i in [head, body]:
        d = base64.urlsafe_b64decode(i + "===")
        d = json.loads(d.decode())
        print(json.dumps(d, sort_keys=True, indent=4))
    print(sign)


if __name__ == "__main__":
    main(sys.argv)
