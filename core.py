
"""This is the memory of the MARS."""

__all__ = ['RedcodeSyntaxError', 'Instruction', 'Mars', 'Memory', 'Warrior']

import re

def get_int(operand):
    """Shortcut for extracting the integer from an operand."""
    if len(operand) < 1:
        raise ValueError('%r is not a valid operand' % operand)
    if operand[0] in SYNTAX.addressing:
        if len(operand) < 1:
            raise ValueError('%r is not a valid operand' % operand)
        return int(operand[1:])
    else:
        return int(operand)

class SYNTAX:
    addressing = '#$*@{}<>'

    field = '[ %s]?[0-9-]+' % addressing
    line = re.compile(('\s*(?P<opcode>[A-Z]{3})'
                       '(.(?P<modifier>[A-Z]{1,2}))?'
                       '(\s+(?P<A>%s)(\s*,\s*(?P<B>%s))?)?'
                      ) % ((field,)*2)
                     )
    data_blocks = ('opcode', 'modifier', 'A', 'B')

    opcodes = ('DAT MOV ADD SUB MUL DIV MOD JMP JMZ JMN DJN SPL CMP SEQ SNE '
            'SLT LDP STP NOP').split()

    modifiers = 'A B AB BA F I X'.split()

    @classmethod
    def is_operand(cls, value):
        if len(value) < 2:
            return False
        if value[0] not in SYNTAX.addressing:
            return False
        try:
            get_int(value)
        except ValueError:
            return False
        return True

class RedcodeSyntaxError(Exception):
    pass

class Instruction(object):
    def __init__(self, *data, **kwdata):
        if data != () and kwdata != {}:
            raise ValueError('You cannot give data both as non-keyword '
                    'and keyword argument.')
        if len(data) == 0:
            if 'opcode' not in kwdata:
                raise ValueError('Opcode is not given.')
            self._data = {'modifier': None, 'A': '#0', 'B': '#0'}
            self._data.update(kwdata)
        elif len(data) == 4:
            self._data = dict(zip(SYNTAX.data_blocks, data))
        else:
            raise ValueError('When Instruction() is provided with '
                    'non-keyword arguments, they have to be 4.')
        for block in SYNTAX.data_blocks:
            # Check value of fields:
            setattr(self, block, getattr(self, block))

    def __eq__(self, other):
        if isinstance(other, str):
            other = Instruction.from_string(other)
        elif isinstance(other, tuple) and len(tuple) == 4:
            other = Instruction.from_tuple(other)
        elif not isinstance(other, Instruction):
            return False
        return all([getattr(self, x)==getattr(other, x)
            for x in SYNTAX.data_blocks])
    def __repr__(self):
        return '<%s.%s %r>' % (self.__class__.__module__,
                self.__class__.__name__, str(self))

    def _get_opcode(self):
        return self._data['opcode']
    def _set_opcode(self, value):
        if value not in SYNTAX.opcodes:
            raise ValueError('%r is not a valid opcode.' % value)
        self._data['opcode'] = value
    opcode = property(_get_opcode, _set_opcode)
    def _get_modifier(self):
        if self._data['modifier'] is not None:
            return self._data['modifier']
        elif self.opcode in ('DAT', 'NOP'):
            return 'F'
        elif self.opcode in ('MOV', 'SEQ', 'SNE', 'CMP'):
            if self.A.startswith('#'):
                return 'AB'
            elif self.B.startswith('#'):
                return 'B'
            else:
                return 'I'
        elif self.opcode in ('ADD', 'SUB', 'MUL', 'DIV', 'MOD'):
            if self.A.startswith('#'):
                return 'AB'
            elif self.B.startswith('#'):
                return 'B'
            else:
                return 'F'
        elif self.opcode in ('SLT', 'LDP', 'STP'):
            if 'A'.startswith('#'):
                return 'AB'
            else:
                return 'B'
        elif self.opcode in ('JMP', 'JMZ', 'JMN', 'DJN', 'SPL'):
            return 'B'
    def _set_modifier(self, value):
        if value not in SYNTAX.modifiers:
            raise ValueError('%r is not a valid modifier' % r)
        self._data['modifier'] = value
    modifier = property(_get_modifier, _set_modifier)
    def _get_A(self):
        return self._data['A']
    def _set_A(self, value):
        if value is None:
            value = '$0'
        if value[0] in '0123456789-':
            value = '$' + value
        if not SYNTAX.is_operand(value):
            raise ValueError('%r is not a valid operand' % value)
        self._data['A'] = value
    A = property(_get_A, _set_A)
    def _get_B(self):
        return self._data['B']
    def _set_B(self, value):
        if value is None:
            value = '$0'
        if value[0] in '0123456789-':
            value = '$' + value
        if not SYNTAX.is_operand(value):
            raise ValueError('%r is not a valid operand')
        self._data['B'] = value
    B = property(_get_B, _set_B)

    @classmethod
    def from_string(cls, string):
        assert isinstance(string, str)
        string = string.split(';')[0]
        if string.endswith('\n'):
            string = string[0:-1]
        if all([x in ' \t' for x in string]): # Blank line
            return None
        parsed = SYNTAX.line.match(string)
        if parsed is None:
            raise RedcodeSyntaxError(string)
        opcode = parsed.group('opcode')
        assert opcode is not None
        list_ = [(parsed.group(x).upper() if parsed.group(x) else None)
                    for x in SYNTAX.data_blocks]
        if list_[0] == 'DAT' and list_[3] is None:
            # See: http://vyznev.net/corewar/guide.html#deep_instr
            list_[3] = list_[2]
            list_[2] = None
        return cls(*list_)

    @classmethod
    def from_tuple(cls, tuple_):
        assert isinstance(tuple_, tuple) or isinstance(tuple_, list)
        if len(tuple_) != 4:
            raise ValueError('%s is not a 4-tuple' % repr(tuple_))
        return cls(*tuple_)

    def __str__(self):
        return '%s.%s %s, %s' % (self.opcode, self.modifier, self.A,
                self.B)

    @property
    def as_tuple(self):
        return tuple([self._data[x] for x in SYNTAX.data_blocks])
    
    @property
    def as_dict(self):
        return self._data.copy()


    def _read(self, memory, ptr):
        """Return input data of the instruction, based on modifiers.

        Data with None should _never_ be read."""
        m = self.modifier
        A = memory.read(memory.get_absolute_ptr(ptr, self.A))
        B = memory.read(memory.get_absolute_ptr(ptr, self.B))
        if m == 'A':
            return ((None, None, A.A, None), (None, None, B.A, None))
        elif m == 'B':
            return ((None, None, A.B, None), (None, None, B.B, None))
        elif m == 'AB':
            return ((None, None, A.A, None), (None, None, B.B, None))
        elif m == 'BA':
            return ((None, None, A.B, None), (None, None, B.A, None))
        elif m == 'F':
            return ((None, None, A.A, A.B ), (None, None, B.A, B.B ))
        elif m == 'X':
            return ((None, None, A.A, A.B ), (None, None, B.B, B.A ))
        elif m == 'I':
            return (A.as_tuple, B.as_tuple)
        else:
            assert False
    def _write(self, memory, dest, inst):
        """Writes data to the memory"""
        m = self.modifier
        if isinstance(inst, tuple):
            if m != 'I':
                # Add an opcode if needed, so it passes sanity checks
                inst = (inst[0] or 'DAT', inst[1], inst[2], inst[3])
            inst = Instruction.from_tuple(inst)
        elif not isinstance(inst, Instruction):
            raise ValueError('You can only write tuples and instructions, '
                    'not %r' % inst)
        if not isinstance(dest, int):
            raise ValueError('Destination must be an int, not %r.' % dest)

        if m == 'A':
            memory.write(dest, A=inst.A)
        elif m == 'B':
            memory.write(dest, B=inst.A)
        elif m == 'AB':
            memory.write(dest, B=inst.A)
        elif m == 'BA':
            memory.write(dest, A=inst.A)
        elif m == 'F':
            memory.write(dest, A=inst.A, B=inst.B)
        elif m == 'X':
            memory.write(dest, B=inst.B, A=inst.A)
        elif m == 'I':
            memory.write(dest, instruction=inst)
        else:
            assert False

    def _math(self, A, B, function):
        "Shortcut for running math operations."
        assert None not in (A[2], B[2])
        res1 = B[2][0]+str(function(get_int(A[2]), get_int(B[2])))
        res2 = None
        if A[3] is not None:
            assert B[3] is not None
            res2 = B[3][0]+str(function(get_int(A[3]), get_int(B[3])))
        return (B[0], B[1], res1, res2)
    def _increment(self, memory, ptr, field):
        "Shortcut for incrementing fields."
        inst = memory.read(ptr + get_int(field))
        if field.startswith('}'):
            inst.A = inst.A[0] + str(int(inst.A[1:])+1)
        elif field.startswith('>'):
            inst.B = inst.B[0] + str(int(inst.B[1:])+1)
    def run(self, memory, ptr):
        assert memory.read(ptr) == self

        # Predecrement
        for field in (self.A, self.B):
            inst = memory.read(ptr + get_int(field))
            if field.startswith('{'):
                inst.A = inst.A[0] + str(int(inst.A[1:])-1)
            elif field.startswith('<'):
                inst.B = inst.B[0] + str(int(inst.B[1:])-1)

        oc = self.opcode

        # Postincrement
        # The order matters: http://www.koth.org/info/icws94.html#5.3.5
        self._increment(memory, ptr, self.A)
        dest = memory.get_absolute_ptr(ptr, self.B)
        self._increment(memory, ptr, self.B)
        A = self._read(memory, ptr)[0]
        B = self._read(memory, ptr)[1]

        if oc == 'DAT':
            threads = []
        elif oc == 'NOP':
            threads = [ptr+1]
        elif oc == 'MOV':
            self._write(memory, dest, A)
            threads = [ptr+1]
        elif oc == 'ADD':
            self._write(memory, dest, self._math(A, B, lambda a,b:a+b))
            threads = [ptr+1]
        elif oc == 'SUB':
            self._write(memory, dest, self._math(A, B, lambda a,b:b-a))
            threads = [ptr+1]
        elif oc == 'MUL':
            self._write(memory, dest, self._math(A, B, lambda a,b:a*b))
            threads = [ptr+1]
        elif oc == 'DIV':
            try:
                self._write(memory, dest, self._math(A, B, lambda a,b:int(b/a)))
                threads = [ptr+1]
            except ZeroDivisionError:
                threads = []
        elif oc == 'MOD':
            try:
                self._write(memory, dest, self._math(A, B, lambda a,b:b%a))
                threads = [ptr+1]
            except ZeroDivisionError:
                threads = []
        elif oc == 'JMP':
            # Note that the modifier is ignored
            threads = [memory.get_absolute_ptr(ptr, self.A)]
        elif oc == 'JMZ':
            if get_int(B[2]) == 0 and \
                    (B[3] is None or get_int(B[3]) == 0):
                threads = [memory.get_absolute_ptr(ptr, self.A)]
            else:
                threads = [ptr+1]
        elif oc == 'JMN':
            if get_int(B[2]) == 0 and \
                    (B[3] is None or get_int(B[3]) == 0):
                threads = [ptr+1]
            else:
                threads = [memory.get_absolute_ptr(ptr, self.A)]
        elif oc == 'DJN':
            self.B = self.B[0] + str(get_int(self.B)-1)
            ptrB = memory.get_absolute_ptr(ptr, self.B)
            B = self._read(memory, ptrB)[1] # Load the new pointed data

            # Jump
            if get_int(B[2]) == 0 and \
                    (B[3] is None or get_int(B[3]) == 0):
                threads = [ptr+1]
            else:
                threads = [memory.get_absolute_ptr(ptr, self.A)]
        elif oc == 'CMP' or oc == 'SEQ':
            if A == B:
                threads = [ptr+2]
            else:
                threads = [ptr+1]
        elif oc == 'SLT':
            if get_int(A[2]) < get_int(B[2]) and \
                    (A[3] is None or A[3] < B[3]):
                threads = [ptr+2]
            else:
                threads = [ptr+1]
        elif oc == 'SPL':
            threads = [ptr+1, ptr+get_int(self.A)]
        else:
            raise NotImplementedError()

        return threads

class Memory(object):
    def __init__(self, size=8000):
        if not isinstance(size, int):
            raise ValueError('Memory size must be an integer, not %r' % size)
        self._size = size
        if 'xrange' not in globals(): # Python 3
            xrange = range
        self._memory = [Instruction('DAT', None, '$0', '$0')
                for x in xrange(1, self.size)]
        self._loaded_warriors = {}

    @property
    def size(self):
        return self._size

    def read(self, ptr):
        if not isinstance(ptr, int):
            raise ValueError('Pointer must be an integer, not %r' % ptr)
        ptr %= self.size
        return self._memory[ptr]
    def write(self, ptr, instruction=None, **kwargs):
        if not isinstance(ptr, int):
            raise ValueError('Pointer must be an integer, not %r' % ptr)
        ptr %= self.size
        if instruction is not None:
            if not isinstance(instruction, Instruction):
                raise TypeError('The instruction parameter must be an '
                        'Instruction instance')
            if kwargs != {}:
                raise ValueError('Cannot supply extra attribute if '
                        'instruction is given')
            self._memory[ptr] = instruction
        else:
            for key in kwargs:
                if key not in SYNTAX.data_blocks:
                    raise ValueError('%r is not a valid data block.')
            data = self.read(ptr).as_dict
            data.update(kwargs)
            self.write(ptr, Instruction(**data))

    def get_absolute_ptr(self, base_ptr, value):
        if len(value) < 2:
            raise ValueError('The operand can be only A or B')
        if not isinstance(base_ptr, int):
            raise ValueError('Pointer must be an integer, not %r.' % base_ptr)
        ptr = base_ptr + get_int(value)
        char = value[0]
        if char not in '#$':
            value2 = self.read(ptr)

        if char == '#':
            return base_ptr
        elif char == '$':
            return ptr
        elif char == '*':
            return ptr + get_int(value2.A)
        elif char == '@':
            return ptr + get_int(value2.B)
        elif char in '{}':
            return base_ptr + get_int(value2.A)
        elif char in '<>':
            return base_ptr + get_int(value2.B)

    def load(self, ptr, warrior):
        if not isinstance(warrior, Warrior):
            raise ValueError('warrior must be an instance of Warrior, not %r.'%
                    warrior)
        if not isinstance(ptr, int):
            raise ValueError('Pointer must be an integer, not %r.' % ptr)

        for line in warrior.initial_program(ptr).split('\n'):
            inst = Instruction.from_string(line)
            if inst is not None:
                self.write(ptr, inst)
                ptr += 1
            

class Mars(object):
    def __init__(self, size, warriors):
        self._memory = Memory(size)
        self._warriors = warriors

    def run(self):
        warrior = self._warriors.pop(0)
        alive = warrior.run(self._memory)
        if alive:
            self._warriors.append(warrior)
        else:
            return warrior

class Warrior(object):
    def __init__(self, program=''):
        if not isinstance(program, str):
            raise ValueError('Program must be a string, not %r.' % program)
        self._initial_program = program
        self._threads = None
    
    @property
    def threads(self):
        return [x for x in self._threads] # Shallow copy

    def initial_program(self, ptr=None):
        if (self._threads is None) and (ptr is None):
            raise ValueError('The load pointer must be provided before '
                    'accessing the program.')
        elif self._threads is None:
            self._threads = [ptr]
        return self._initial_program

    def run(self, memory):
        assert self._threads != [], 'Attempted to run a died warrior.'
        ptr = self._threads.pop(0)
        inst = memory.read(ptr)
        new_threads = inst.run(memory, ptr)
        if not isinstance(new_threads, list):
            raise ValueError('Instruction.run must return a list, not %r.' %
                    new_threads)
        self._threads.extend(new_threads)
        return (self._threads != []) # True if warrior is still alive

