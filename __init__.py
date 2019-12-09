#!/usr/bin/env python3
import os
import sys


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
    def __init__(self):
        self.target_filename =  os.path.abspath(sys._getframe().f_back.f_code.co_filename)
        self.target_lineno =  sys._getframe().f_back.f_lineno
        self.noentry = (self.target_filename, self.target_lineno) in COMMENT.visited
        COMMENT.visited.add((self.target_filename, self.target_lineno))
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
            lines[b_lineno-1] = lines[b_lineno-1][:-1] + "# "+self.comment[b_lineno] + "\n"
        with open(self.target_filename, "w") as f:
            f.writelines(lines)
        print("\033[32m%s: %s\033[0m"%(self.target_filename, self.target_lineno))


if __name__ == '__main__':
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    def comment_numpy():
        with COMMENT():
            a = np.array([1,2,3,4,5,6])
            b = np.array([0,1,2,3,4,5])
            ab_h = np.hstack((a,b))
            ab_v = np.vstack((a,b))
            ab = np.dot(a,b)
            AA, BB = np.meshgrid(a,b)

    def comment_pytorch():
        with COMMENT():
            x = torch.tensor([[1,2,],[3,4]])
            x = F.relu(x)

    comment_numpy()
    comment_pytorch()
    comment_numpy()
    comment_pytorch()
