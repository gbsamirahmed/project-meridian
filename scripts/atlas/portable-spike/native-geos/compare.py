"""Unchanged frozen replay and expected envelopes; no answer data in native binding."""
import sys
from adapter import NativeSession
import replay

if __name__=='__main__':
    replay.SharedProjection=NativeSession
    sys.exit(replay.run())
