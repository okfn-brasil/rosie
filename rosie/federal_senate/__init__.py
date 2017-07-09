from rosie.federal_senate import settings
from rosie.federal_senate.adapter import Adapter
from rosie.core import Core


def main(target_directory='/tmp/serenata-data', years=None):
    adapter = Adapter(target_directory, years=years)
    core = Core(settings, adapter)
    core()
