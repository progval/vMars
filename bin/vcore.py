#!/usr/bin/env python

from vmars.core import Mars, MarsProperties, Warrior

import vmars.core as core

if __name__ == '__main__':
    import os
    import sys
    import argparse
    parser = argparse.ArgumentParser(
            description='Runs a bunch of warriors.')
    parser.add_argument('warriors', metavar='warrior.rc', type=open,
            nargs='+', help='warrior source codes.')
    parser.add_argument('--laxist', '-l', action='store_true',
            help='determines whether vMars will perform strict checks')

    for (key, value) in MarsProperties().as_dict.items():
        parser.add_argument('--' + key, default=value, type=int)

    try:
        args = vars(parser.parse_args())
    except IOError as e: # Failed to open files
        sys.stderr.write(str(e) + '\n')
        sys.stderr.flush()
        exit()

    STRICT = not args.pop('laxist')
    warriors = args.pop('warriors')

    print('Booting MARS.')
    properties = MarsProperties(**args)
    mars = Mars(properties)

    print('Loading warriors:')
    warriors = [Warrior(x.read()) for x in warriors]
    for warrior in warriors:
        print('\t' + str(warrior))
        mars.load(warrior)

    print('Running processes.')
    progress_step = int(properties.maxcycles/10)
    progress = progress_step
    try:
        for cycle in xrange(1, properties.maxcycles+1):
            progress += 1
            if progress >= progress_step:
                print('\t%i%%' % (100*cycle/properties.maxcycles))
                progress = 0
            dead_warriors = mars.cycle()
            for warrior in dead_warriors:
                print('\tWarrior %s died at cycle %i.' % (warrior, cycle))
            if len(mars.warriors) <= 1:
                break
    except KeyboardInterrupt:
        print('\tHalt signal got.')

