import watcher
import config
import time

class Args(object):
    config_type = 'ini'
    config = 'watcher.ini'

    def __init__(self, command, config_type):
        self.command = command
        self.config_type = config_type

print 'Testing:'

######################
### Config Parsing ###

## INI Parsing
print 'INI Parsing . . .'

args = Args('debug', 'ini')

conf = config.parserFactory(args)

daemon = watcher.WatcherDaemon(conf)

daemon.run()

### Config Parsing ###
######################

print 'All Tests passed successfully!'
