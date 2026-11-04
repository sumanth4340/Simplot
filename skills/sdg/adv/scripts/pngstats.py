"""PNG stats helper (runs under C:/isaacsim/python.bat, which
has PIL; system + pixi pythons do not). Prints one line per file:
path shape mean nunique. Args: files...
"""
import sys

from PIL import Image
import numpy as np

for f in sys.argv[1:]:
    a = np.asarray(Image.open(f))
    flat = a.reshape(-1, a.shape[-1]) if a.ndim == 3 else a.reshape(-1)
    print("%s shape=%s mean=%.1f nunique=%d"
          % (f, a.shape, float(a.mean()),
             len(np.unique(flat, axis=0))))
