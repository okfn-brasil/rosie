"""Rosie.

Usage:
    python rosie.py run (chamber_of_deputies | federal_senate)
    python rosie.py run (chamber_of_deputies | federal_senate) [--years 2017,2016]
    python rosie.py run (chamber_of_deputies | federal_senate) [--path <path to output directory>]
    python rosie.py run (chamber_of_deputies | federal_senate) [--path <path to output directory>] [--years 2017,2016]
    python rosie.py test [chamber_of_deputies | federal_senate]

Options:
    --years   runs Rosie fetching data and finding suspicions for a specific set of years
    --path    directory in which Rosie saves fetched data and the suspicions CSV [default: /tmp/serenata-data]

"""

from sys import argv, exit
from docopt import docopt


def entered_command(argv):
    if len(argv) >= 2:
        return argv[1]
    return None


def run():
    import rosie
    import rosie.chamber_of_deputies
    import rosie.federal_senate

    if len(argv) >= 3:
        target_module = argv[2]
    else:
        arguments = docopt(__doc__, help=True)
        print(arguments)
        exit(1)

    target_directory = argv[argv.index('--path') + 1] if '--path' in argv else '/tmp/serenata-data/'

    klass = getattr(rosie, target_module)
    if '--years' in argv:
        years = argv[argv.index('--years') + 1]
        years = [int(num) for num in years.split(',')]
        klass.main(target_directory, years=years)
    else:
        klass.main(target_directory)


def test():
    import os

    import unittest

    loader = unittest.TestLoader()

    if len(argv) >= 3:
        target_module = argv[2]
        tests_path = os.path.join('rosie', target_module)
        tests = loader.discover(tests_path)
    else:
        tests = loader.discover('rosie')

    testRunner = unittest.runner.TextTestRunner()
    result = testRunner.run(tests)

    if not result.wasSuccessful():
        exit(1)


commands = {'run': run, 'test': test}
command = commands.get(entered_command(argv), help)
command()
