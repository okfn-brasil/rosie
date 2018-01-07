"""Hi, this is Serenata's Rosie!

Usage:
  rosie.py run (chamber_of_deputies | federal_senate) [--path=<path>] [--years=<years>]
  rosie.py test [chamber_of_deputies | federal_senate]

Options:
  --years=<years>  runs Rosie fetching data and finding suspicions for a specific set of years (use a comma to separate years)
  --path=<path>    directory in which Rosie saves fetched data and the suspicions CSV [default: /tmp/serenata-data]

"""

from sys import exit
from docopt import docopt


def main():
    arguments = docopt(__doc__)

    if arguments['run']:
        run(**arguments)

    if arguments['test']:
        return test(**arguments)


def run(**args):
    import rosie
    import rosie.chamber_of_deputies
    import rosie.federal_senate

    commands = ('chamber_of_deputies', 'federal_senate')
    target_module, *_ =  filter(lambda x: args.get(x), commands)

    klass = getattr(rosie, target_module)

    if args['--years']:
        args['--years'] = [int(v) for v in args['--years'].split(',')]

    klass.main(args['--path'], args['--years'])


def test(**args):
    import os

    import unittest

    loader = unittest.TestLoader()

    test_path = 'rosie'

    if args['chamber_of_deputies']:
        tests_path = os.path.join(test_path, 'chamber_of_deputies')
    elif args['federal_senate']:
        tests_path = os.path.join(test_path, 'federal_senate')

    tests = loader.discover(test_path)

    testRunner = unittest.runner.TextTestRunner()
    result = testRunner.run(tests)

    if not result.wasSuccessful():
        exit(1)


if __name__ == '__main__':
    main()
