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
        self._painting = threading.Lock()
        self._paint_queue = collections.deque()
        self._image = QtGui.QPixmap(400, 400)
        self._image.fill(QtCore.Qt.yellow)
        self.setPixmap(self._image)
        self._painter = QtGui.QPainter()
        self.resize(400, 400)
        self.drawInstruction.connect(self.onDrawInstruction)

    def show(self):
        super(MemoryView, self).show()
        self.resizeEvent()
        self.redraw()

    def resizeEvent(self, resizeEvent=None):
        self.cols = math.floor((self.width())/CELL_SIZE) - 1
        self.lines = math.ceil(self._memory.size/float(self.cols))

    def redraw(self):
        self._thread = InitializationThread(self)
        self._thread.run() # FIXME: use .start() instead

    drawInstruction = QtCore.pyqtSignal(int, object, bool)

    @exitOnKeyboardInterrupt
    def onDrawInstruction(self, ptr, instruction, update):
        rectangle = QtCore.QRect(
                 (ptr % self.cols)*CELL_SIZE,
                 math.floor(ptr/float(self.cols))*CELL_SIZE,
                 CELL_SIZE,
                 CELL_SIZE)
        color = opcode2color[instruction.opcode]
        self._painting.acquire()
        self._painter.begin(self._image)
        self._painter.fillRect(rectangle, color)
        self._painter.end()
        self._painting.release()
        self.repaint()
        if update:
            self.setPixmap(self._image)

    def onMemoryUpdate(self, ptr, old_inst, new_inst):
        self.drawInstruction.emit(ptr, new_inst, True)

    def __del__(self):
        if hasattr(self, '_painter'):
            self._painter.end()


class InitializationThread(QtCore.QThread):
    def __init__(self, widget):
        super(InitializationThread, self).__init__()
        self._widget = widget

    def run(self):
        with self._widget._memory.lock:
            for ptr, instruction in enumerate(self._widget._memory.as_list):
                self._widget.drawInstruction.emit(ptr, instruction, False)
            self._widget.drawInstruction.emit(ptr, instruction, True)

