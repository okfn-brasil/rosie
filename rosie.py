"""Rosie.

Usage:
  rosie.py run (chamber_of_deputies | federal_senate)
  rosie.py run (chamber_of_deputies | federal_senate) [--years <years>]
  rosie.py run (chamber_of_deputies | federal_senate) [--path <path>]
  rosie.py run (chamber_of_deputies | federal_senate) [--path] [--years <years>]
  rosie.py test [chamber_of_deputies | federal_senate]

Options:
    --years   runs Rosie fetching data and finding suspicions for a specific set of years
    --path    directory in which Rosie saves fetched data and the suspicions CSV [default: /tmp/serenata-data]

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

    target_directory = args['<path>'] if args['--path'] else '/tmp/serenata-data/'

    target_module = 'chamber_of_deputies' if args['chamber_of_deputies'] else 'federal_senate'

    klass = getattr(rosie, target_module)

    if args['--years']:
        years = args['<years>']
        years = [int(num) for num in years.split(',')]
        klass.main(target_directory, years=years)
    else:
        klass.main(target_directory)


def test(**args):
    print(args)
    import os

    import unittest

    loader = unittest.TestLoader()

    if args['chamber_of_deputies']:
        tests_path = os.path.join('rosie', 'chamber_of_deputies')
        tests = loader.discover(tests_path)
    elif args['federal_senate']:
        tests_path = os.path.join('rosie', 'federal_senate')
        tests = loader.discover(tests_path)
    else:
        tests = loader.discover('rosie')

    testRunner = unittest.runner.TextTestRunner()
    result = testRunner.run(tests)

    if not result.wasSuccessful():
        exit(1)


if __name__ == '__main__':
    main()
