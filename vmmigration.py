#!/usr/bin/env python3
from lbm_vdrc.cli import main
from lbm_vdrc.core import logger
import sys

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        logger().exception("Fatal error")
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
