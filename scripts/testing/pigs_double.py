#!/usr/bin/env python3

import sys
from datetime import datetime


if __name__ == "__main__":
    with open("/tmp/esphome_test_pigs.out", "a") as f:
        timestamp = str(datetime.now())
        f.write(f"{timestamp} ")
        f.write(" ".join(sys.argv))
        f.write("\n")
