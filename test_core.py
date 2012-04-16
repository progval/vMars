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

    def testAdd(self):
        inst = core.Instruction.from_string('ADD #5, 2')
        self._memory.write(10, inst)
        inst.run(self._memory, 10)
        self.assertEqual(self._memory.read(12).A, '$0')
        self.assertEqual(self._memory.read(12).B, '$5')

        inst = core.Instruction.from_string('ADD.A #5, 2')
        self._memory.write(20, inst)
        inst.run(self._memory, 20)
        self.assertEqual(self._memory.read(22).A, '$5')
        self.assertEqual(self._memory.read(22).B, '$0')

        inst = core.Instruction.from_string('ADD.A #5, 2')
        self._memory.write(30, inst)
        inst.run(self._memory, 30)
        self.assertEqual(self._memory.read(32).A, '$5')
        self.assertEqual(self._memory.read(32).B, '$0')

        warrior = core.Warrior('ADD #5, 2')
        self._memory.load(40, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(42).A, '$0')
        self.assertEqual(self._memory.read(42).B, '$5')
        self.assertEqual(warrior.threads, [41])

    def testSub(self):
        inst = core.Instruction.from_string('SUB #5, 2')
        self._memory.write(10, inst)
        inst.run(self._memory, 10)
        self.assertEqual(self._memory.read(12).A, '$0')
        self.assertEqual(self._memory.read(12).B, '$-5')

        warrior = core.Warrior('SUB #5, 2')
        self._memory.load(20, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(22).A, '$0')
        self.assertEqual(self._memory.read(22).B, '$-5')
        self.assertEqual(warrior.threads, [21])

    def testMul(self):
        inst = core.Instruction.from_string('MUL #5, 2')
        inst2 = core.Instruction.from_string('DAT $0, $7')
        self._memory.write(10, inst)
        self._memory.write(12, inst2)
        inst.run(self._memory, 10)
        self.assertEqual(self._memory.read(12).A, '$0')
        self.assertEqual(self._memory.read(12).B, '$35')

        self._memory.write(20, inst)
        inst.run(self._memory, 20)
        self.assertEqual(self._memory.read(22).A, '$0')
        self.assertEqual(self._memory.read(22).B, '$0')

    def testDiv(self):
        warrior = core.Warrior('''DIV #5, 2
                                  NOP
                                  DAT $0, $32''')
        self._memory.load(10, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(12).A, '$0')
        self.assertEqual(self._memory.read(12).B, '$6')
        self.assertEqual(warrior.threads, [11])

        warrior = core.Warrior('''DIV #0, 2
                                  NOP
                                  DAT $0, $32''')
        self._memory.load(20, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(22).A, '$0')
        self.assertEqual(self._memory.read(22).B, '$32')
        self.assertEqual(warrior.threads, [])

    def testMod(self):
        warrior = core.Warrior('''MOD #5, 2
                                  NOP
                                  DAT $0, $32''')
        self._memory.load(10, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(12).A, '$0')
        self.assertEqual(self._memory.read(12).B, '$2')
        self.assertEqual(warrior.threads, [11])

        warrior = core.Warrior('''MOD #0, 2
                                  NOP
                                  DAT $0, $32''')
        self._memory.load(20, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(22).A, '$0')
        self.assertEqual(self._memory.read(22).B, '$32')
        self.assertEqual(warrior.threads, [])

    def testJmz(self):
        warrior = core.Warrior('''JMZ 5, #0''')
        self._memory.load(10, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [15])

        warrior = core.Warrior('''JMZ 5, #1''')
        self._memory.load(20, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [21])

        warrior = core.Warrior('''JMZ 5, 1
                                  DAT 0, 0''')
        self._memory.load(30, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [35])

        warrior = core.Warrior('''JMZ 5, 1
                                  DAT 0, 1''')
        self._memory.load(40, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [41])

    def testJmn(self):
        warrior = core.Warrior('''JMN 5, #0''')
        self._memory.load(10, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [11])

        warrior = core.Warrior('''JMN 5, #1''')
        self._memory.load(20, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [25])

    def testDjn(self):
        warrior = core.Warrior('''DJN 5, #1
                                  JMP -1''')
        self._memory.load(10, warrior)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(10).B, '#0')
        self.assertEqual(warrior.threads, [11])
        warrior.run(self._memory)
        warrior.run(self._memory)
        self.assertEqual(self._memory.read(10).B, '#-1')
        self.assertEqual(warrior.threads, [15])

    def testSpl(self):
        warrior = core.Warrior('''SPL 5
                                  SPL -1''')
        self._memory.load(10, warrior)
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [11, 15])
        warrior.run(self._memory)
        self.assertEqual(warrior.threads, [15, 12, 10])



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
        dat4 = core.Instruction('DAT', None, '#0', '#8')
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

        warrior.run(self._memory) # ADD
        warrior.run(self._memory) # MOV
        warrior.run(self._memory) # JMP
        self.assertEqual(warrior.threads, [ptr])
        self.assertEqual(self._memory.read(ptr+3+8), dat4)



if __name__ == '__main__':
    unittest.main()
