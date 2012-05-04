#!/usr/bin/env python

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

CELL_SIZE = 10.0 # Used for float division

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


class MemoryView(QtGui.QWidget):
    def __init__(self, memory, parent=None):
        super(MemoryView, self).__init__(parent)
        self._memory = memory
        self._painting = threading.RLock()

        self.resizeEvent()

    def resizeEvent(self, resizeEvent=None):
        self.cols = math.floor((self.width())/CELL_SIZE) - 1
        self.lines = math.ceil(self._memory.size/float(self.cols))

    def redraw(self):
        self._thread = InitializationThread(self)
        self._thread.run() # FIXME: use .start() instead

    def paintEvent(self, paintEvent):
        self._painter = QtGui.QPainter()
        self.redraw()
        self._memory.add_callback(self.onMemoryUpdate)

    def drawInstruction(self, ptr, instruction, pop=True):
        rectangle = QtCore.QRectF((ptr % self.cols)*CELL_SIZE,
                 math.floor(ptr/float(self.cols))*CELL_SIZE,
                 CELL_SIZE,
                 CELL_SIZE)
        try:
            self._painting.acquire()
            self._painter.begin(self)
            self._painter.fillRect(rectangle,
                    opcode2color[instruction.opcode])
        finally:
            self._painting.release()
            self._painter.end()

    def onMemoryUpdate(self, ptr, old_inst, new_inst):
        self.drawInstruction(ptr, new_inst)

    def __del__(self):
        self._painter.end()
        super(MemoryView, self).__del__()


class InitializationThread(QtCore.QThread):
    def __init__(self, widget):
        super(InitializationThread, self).__init__()
        self._widget = widget
        self.drawInstruction.connect(self._widget.drawInstruction)

    def run(self):
        self._widget._memory.lock.acquire()
        for ptr, instruction in enumerate(self._widget._memory.as_list):
            self.drawInstruction.emit(ptr, instruction, False)
        self._widget._memory.lock.release()

    drawInstruction = QtCore.pyqtSignal(int, object, bool)
