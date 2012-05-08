# Copyright (C) 2012, Valentin Lorentz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

__all__ = ['MemoryView']

import math
import threading
import collections

from PyQt4 import QtCore, QtGui

CELL_SIZE = 5.0 # Used for float division

def exitOnKeyboardInterrupt(f):
    def newf(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except KeyboardInterrupt:
            exit()
    return newf

opcode2color = {
    # Math
    'ADD': QtCore.Qt.blue,
    'SUB': QtCore.Qt.blue,
    'MUL': QtCore.Qt.blue,
    # Dangerous math
    'DIV': QtCore.Qt.darkBlue,
    'MOD': QtCore.Qt.darkBlue,
    # Dangerous
    'DAT': QtCore.Qt.red,
    # Common
    'MOV': QtCore.Qt.green,
    # Jumps
    'JMP': QtCore.Qt.darkMagenta,
    'JMZ': QtCore.Qt.darkMagenta,
    'JMN': QtCore.Qt.darkMagenta,
    'DJN': QtCore.Qt.darkMagenta,
    # Skips
    'SEQ': QtCore.Qt.magenta,
    'SNE': QtCore.Qt.magenta,
    'SLI': QtCore.Qt.magenta,
    # P-space
    'LDP': QtCore.Qt.lightGray,
    'SDP': QtCore.Qt.lightGray,
    # Split
    'SPL': QtCore.Qt.black,
    # Nop
    'NOP': QtCore.Qt.transparent
}

class MemoryView(QtGui.QLabel):
    def __init__(self, memory, parent=None):
        super(MemoryView, self).__init__(parent)
        self._memory = memory
        self._memory.add_callback(self.onMemoryUpdate)
        self.painting = threading.Lock()
        self._paint_queue = collections.deque()
        if parent is None:
            self.resize(700, 500)
        self._image = QtGui.QPixmap(self.width(), self.height())
        self._image.fill(QtCore.Qt.transparent)
        self._painter = QtGui.QPainter()
        self._cache = collections.deque(maxlen=10)

    def show(self):
        super(MemoryView, self).show()
        self.resizeEvent()
        self.redraw()

    def resizeEvent(self, resizeEvent=None):
        self.cols = math.floor((self.width())/CELL_SIZE) - 1
        self.lines = math.ceil(self._memory.size/float(self.cols))

    def redraw(self):
        with self.painting:
            for ptr, instruction in enumerate(self._memory.as_list):
                self.drawInstruction(ptr, instruction, True)
            self.setPixmap(self._image)

    @exitOnKeyboardInterrupt
    def paintEvent(self, event):
        super(MemoryView, self).paintEvent(event)
        self._draw(self)

    @exitOnKeyboardInterrupt
    def drawInstruction(self, ptr, instruction, init):
        rectangle = QtCore.QRect(
                 (ptr % self.cols)*CELL_SIZE,
                 math.floor(ptr/float(self.cols))*CELL_SIZE,
                 CELL_SIZE,
                 CELL_SIZE)
        color = opcode2color[instruction.opcode]
        self._cache.append((rectangle, color))
        if len(self._cache) == self._cache.maxlen:
            self._draw(self._image)
            self._cache.clear()
            if not init:
                self.setPixmap(self._image)
        if not init:
            self.repaint()

    @exitOnKeyboardInterrupt
    def _draw(self, target):
        try:
            self._painter.begin(target)
            self._painter.beginNativePainting()
            for rectangle, color in self._cache:
                self._painter.fillRect(rectangle, color)
        finally:
            self._painter.endNativePainting()
            self._painter.end()

    def onMemoryUpdate(self, ptr, old_inst, new_inst):
        if old_inst.opcode == new_inst.opcode:
            return
        with self.painting:
            self.drawInstruction(ptr, new_inst, False)

    def __del__(self):
        if hasattr(self, '_painter'):
            self._painter.end()
