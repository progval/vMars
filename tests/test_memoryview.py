import sys
import unittest

from vmars.qt.memoryview import MemoryView
from vmars.core import Memory, Instruction
from PyQt4.QtGui import QApplication

app = QApplication(sys.argv)

class TestMemoryView(unittest.TestCase):
    def testInit(self):
        memory = Memory(200)
        memory.write(20, Instruction.from_string('ADD 5, 6'))
        memory.write(30, Instruction.from_string('MOV #5, 2'))
        memory.write(40, Instruction.from_string('SPL 2'))
        widget = MemoryView(memory)
        widget.show()
        app.exec_()

if __name__ == '__main__':
    unittest.main()
