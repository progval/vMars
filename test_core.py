import unittest

import core

imp = 'MOV 0, 1'
dwarf = '''
        ADD.AB #4, 3
        MOV.I  2, @2
        JMP    -2
        DAT    #0, #0
        '''

class TestInstruction(unittest.TestCase):
    def setUp(self):
        self._memory = core.Memory()

    def testMagic(self):
        """Test magic methods"""
        inst = core.Instruction('DAT', None, '$0', '$0')
        self.assertEqual(str(inst), 'DAT.F $0, $0')

        inst = core.Instruction('MOV', 'X', '52', '@621')
        self.assertEqual(str(inst), 'MOV.X $52, @621')

        self.assertEqual(repr(inst), '<core.Instruction \'MOV.X $52, @621\'>')

        inst2 = core.Instruction.from_string('MOV.X $52, @621')
        self.assertEqual(inst, inst2)

        self.assertEqual(inst2.opcode, 'MOV')
        self.assertEqual(inst2.modifier, 'X')
        self.assertEqual(inst2.A, '$52')
        self.assertEqual(inst2.B, '@621')

        self.assertIsNot(core.Instruction('DAT', None, '0', '0'),
                core.Instruction('DAT', None, '0', '0'))

    def testMov(self):
        # Basic test
        inst = core.Instruction.from_string('MOV 0, 1')
        self._memory.write(5, inst)
        inst.run(self._memory, 5)
        self.assertEqual(self._memory.read(5), inst)
        self.assertEqual(self._memory.read(6), inst)
        self.assertEqual(self._memory.read(7), core.Instruction('DAT', None, '0', '0'))

        # Test modulo
        inst = core.Instruction.from_string('MOV 0, 10')
        self._memory.write(7998, inst)
        inst.run(self._memory, 7998)
        self.assertEqual(self._memory.read(8), inst)
        self.assertNotEqual(self._memory.read(7), inst)

        # Test modifier
        inst = core.Instruction.from_string('MOV.B 0, 1')
        self._memory.write(100, inst)
        inst.run(self._memory, 100)
        self.assertEqual(self._memory.read(101), 'DAT 0, 1')

class TestMemory(unittest.TestCase):
    def setUp(self):
        self._memory = core.Memory()

    def testSize(self):
        self.assertEqual(self._memory.size, 8000)
        self.assertIs(self._memory.read(1), self._memory.read(8001))

    def testRead(self):
        for i in range(0, 10):
            self.assertEqual(self._memory.read(i),
                    core.Instruction('DAT', None, '$0', '$0'))
        self.assertIsNot(self._memory.read(0), self._memory.read(1))
        self.assertIs(self._memory.read(0), self._memory.read(0))

    def testWrite(self):
        inst = core.Instruction('MOV', None, '658', '{47')
        self._memory.write(5, inst)

    def testLoad(self):
        warrior = core.Warrior(imp)
        self._memory.load(10, warrior)
        self.assertEqual(self._memory.read(10), warrior.initial_program())

        ptr = 200
        warrior2 = core.Warrior(dwarf)
        self._memory.load(ptr, warrior2)
        for line in warrior2.initial_program().split('\n'):
            if not all([x in ' \n\t' for x in line]):
                self.assertEqual(self._memory.read(ptr),
                        core.Instruction.from_string(line))
                ptr += 1

class TestWarrior(unittest.TestCase):
    def setUp(self):
        self._memory = core.Memory()

    def testImp(self):
        ptr = 10
        warrior = core.Warrior(imp)
        self.assertRaises(ValueError, warrior.initial_program)
        self.assertEqual(warrior.initial_program(ptr), imp)
        self.assertEqual(warrior.threads, [ptr])
        self._memory.load(ptr, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [ptr+1])
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [ptr+2])

    def testDwarf(self):
        dat1 = core.Instruction('DAT', None, '$0', '$0')
        dat2 = core.Instruction('DAT', None, '#0', '#0')
        dat3 = core.Instruction('DAT', None, '#0', '#4')
        ptr = 100
        warrior = core.Warrior(dwarf)
        self.assertRaises(ValueError, warrior.initial_program)
        self.assertEqual(warrior.initial_program(ptr), dwarf)
        self.assertEqual(warrior.threads, [ptr])
        self._memory.load(ptr, warrior)
        self.assertEqual(self._memory.read(ptr+3), dat2)
        self.assertEqual(self._memory.read(ptr+3+4), dat1)
        warrior.run(self._memory) # ADD
        self.assertEqual(warrior.threads, [ptr+1])
        self.assertEqual(self._memory.read(ptr+3), dat3)
        self.assertEqual(self._memory.read(ptr+3+4), dat1)
        warrior.run(self._memory) # MOV
        self.assertEqual(warrior.threads, [ptr+2])
        self.assertEqual(self._memory.read(ptr+3+4), dat3)
        warrior.run(self._memory) # JMP
        self.assertEqual(warrior.threads, [ptr])
        self.assertEqual(self._memory.read(ptr+3+4), dat3)



if __name__ == '__main__':
    unittest.main()
