#!/usr/bin/env python

from vmars import core
from vmars.assembler import Assembler

if __name__ == '__main__':
    import os
    import sys
    import argparse
    parser = argparse.ArgumentParser(
            description='Assembles a RedCode assembly file into a load file.')
    parser.add_argument('--force', '-f', action='store_true',
            help='determines whether existing files will be overwritten')
    parser.add_argument('warriors', metavar='warrior.red', type=open,
            nargs='+', help='file to be assembled')

    for (key, value) in core.MarsProperties().as_dict.items():
        parser.add_argument('--' + key, default=value, type=int)

    try:
        args = vars(parser.parse_args())
    except IOError as e: # Failed to open files
        sys.stderr.write(str(e) + '\n')
        sys.stderr.flush()
        exit()

    assemblies = args.pop('warriors')
    force = args.pop('force')
    properties = core.MarsProperties(**args)
    assembler = Assembler(properties)
    for assembly in assemblies:
        if not assembly.name.endswith('.red'):
            sys.stderr.write('%s does not end with .red.\n' % assembly.name)
            sys.stderr.flush()
            exit()
        dest = assembly.name.replace('.red', '.rc')
        name = os.path.split(dest)[1][0:-len('.rc')]
        print('Assembling %s...' % name)
        try:
            load_file = assembler.assemble(assembly.read(), raw=True)
        except ParseError as e:
            print('\tError: %s' % e.args[0])
            print('\tWarrior %s not assembled.' % name)
            continue
        print('\tWarrior %s successfully assembled.' % name)
        print('\tWriting to %s' % dest)
        if os.path.exists(dest):
            if force:
                print('\tFile %s exists, dropping it.' % dest)
                try:
                    os.unlink(dest)
                except:
                    print('\tError: Could not remove file. Warrior not '
                        'written.')
            else:
                print('\tError: File %s exists, not writing warrior %s.' %
                        (dest, name))
                continue
        try:
            open(dest, 'w').write(load_file[1])
        except Exception as e:
            print('\tError: write failed, file may be corrupted.')
            continue
        print('\tWarrior %s successfully written.' % name)

