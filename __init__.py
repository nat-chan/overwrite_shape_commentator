#!/usr/bin/env python3
# %%
import os
import sys
import linecache
import threading

# %%
class COMMENT:
    """
    Automatically tracks the return value of the function at the point enclosed by the with statement.
    If the return value has dtype and shape attributes, those details are added as comments to the corresponding lines.
    e.g.
    >>> import shapyr
    >>> with shapyr.COMMENT():
    >>>     a = np.array([1,2,3,4,5,6])
    >>>     b = np.array([0,1,2,3,4,5])
    >>>     ab_h = np.hstack((a,b))# int64(12,)
    >>>     ab_v = np.vstack((a,b))# int64(2, 6)
    >>>     ab = np.dot(a,b)
    >>>     AA, BB = np.meshgrid(a,b)
    >>>     x = torch.tensor([[1,2,],[3,4]])
    >>>     x = F.relu(x)# int64(2, 2)
    """
    visited = set()

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.target_filename = os.path.abspath(sys._getframe().f_back.f_code.co_filename)
        self.target_lineno = sys._getframe().f_back.f_lineno
        self.position = (self.target_filename, self.target_lineno)
        self.noentry = self.position in COMMENT.visited
        COMMENT.visited.add(self.position)
        self.comment = dict()

    def __enter__(self):
        if self.noentry: return

        def tracer(frame, event, arg):
            if event != 'return': return tracer
            if not frame.f_back: return tracer
            b_filename = os.path.abspath(frame.f_back.f_code.co_filename)
            b_lineno = frame.f_back.f_lineno
            funcname = frame.f_code.co_name
            if b_filename != self.target_filename: return tracer
            if hasattr(arg, 'shape') and hasattr(arg, 'dtype'):
                self.comment[b_lineno] = str(arg.dtype).split('.')[-1] + str(tuple(arg.shape))

        self._tracer = sys.gettrace()
        sys.settrace(tracer)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.noentry: return
        sys.settrace(self._tracer)
        with open(self.target_filename, "r") as f:
            lines = f.readlines()
        for b_lineno in self.comment:
            lines[b_lineno-1] = lines[b_lineno-1][:-1] + "# " + self.comment[b_lineno] + "\n"
        with open(self.target_filename, "w") as f:
            f.writelines(lines)
        if self.verbose:
            print("\033[32m%s: %s\033[0m" % self.position)

# %%
def dissect(f):
    data = threading.local()
    data.filename = None
    data.captured = None
    data.depth = float('inf')
    def tracer(frame, event, arg):
        _frame = frame
        _depth = 0
        while _frame:
            _frame = _frame.f_back
            _depth += 1
        funcname = frame.f_code.co_name
        filename = frame.f_back.f_code.co_filename
        lineno = frame.f_back.f_lineno
        if event == 'call' and funcname == 'forward' and data.depth > _depth:
            data.depth = _depth
        if event != 'return': return tracer
        if not frame.f_back: return tracer
        if hasattr(arg, 'shape') and _depth == data.depth + 1:
            if data.filename != filename:
                print(f'\033[35m{filename}\033[0m')
                data.filename = filename
            code = linecache.getline(filename, lineno).rstrip()
            shape = str(tuple(arg.shape)).rjust(25)
            print(f'\033[32m{lineno:5}\033[36m{shape}\033[0m{code}')
        if _depth == data.depth:
            data.captured = frame.f_locals.copy()
        return tracer
    def wrapper(*args, **kw):
        _tracer = sys.gettrace()
        sys.settrace(tracer)
        try:
            ret = f(*args, **kw)
        finally:
            sys.settrace(_tracer)
        return data.captured
    return wrapper

# %%
if __name__ == '__main__':
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    def comment_numpy():
        with COMMENT():
            a = np.array([1, 2, 3, 4, 5, 6])
            b = np.array([0, 1, 2, 3, 4, 5])
            ab_h = np.hstack((a, b))# int64(12,)
            ab_v = np.vstack((a, b))# int64(2, 6)
            ab = np.dot(a, b)
            AA, BB = np.meshgrid(a, b)

    def comment_pytorch():
        with COMMENT():
            x = torch.tensor([[1, 2], [3, 4]])
            x = F.relu(x)# int64(2, 2)

    comment_numpy()
    comment_pytorch()
    comment_numpy()
    comment_pytorch()
# %%
