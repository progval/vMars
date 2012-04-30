
import unittest

import core
import assembler

class TestAssembler(unittest.TestCase):
    def setUp(self):
        self._assembler = assembler.Assembler(core.MarsProperties())
    def assemble(self, assembly):
        return self._assembler.assemble(assembly)

    def testLabels(self):
        self.assertEqual(self.assemble('imp MOV imp, imp+1')[1], ['MOV 0, 1'])
        self.assertEqual(self.assemble('''
                                          loop:   ADD.AB  #4, bomb
                                                  MOV.I   bomb, @bomb
                                                  JMP     loop
                                          bomb:   DAT     #0, #0
                                       ''')[1],
                         ['ADD.AB #4, 3',
                          'MOV.I 2, @2',
                          'JMP -2',
                          'DAT #0, #0'
                         ]
                        )
    def testParse(self):
        self.assertRaises(assembler.ParseError, self.assemble, 'ABC')
        self.assertRaises(assembler.ParseError, self.assemble, 'ABC 5')


if __name__ == '__main__':
    unittest.main()
