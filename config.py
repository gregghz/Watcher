import ConfigParser
import pyinotify

def parserFactory(args):
    if args.config_type == 'ini':
        return IniParser(args)
    else:
        return YmlParser(args)
        
class Parser(object):
    options = {
        'logfile': '/tmp/watcher.log',
        'pidfile': '/tmp/watcher.pid'
    }
    
    def __init__(self, config_file):
        pass

    def get(self, option):
        return self.options[option]
        
    def jobs(self):
        raise Exception('must define this method')
        
    def _parseMask(self, masks):
        ret = False;

        for mask in masks:
            mask = mask.strip()

            if 'access' == mask:
                ret = self._addMask(pyinotify.IN_ACCESS, ret)
            elif 'atrribute_change' == mask:
                ret = self._addMask(pyinotify.IN_ATTRIB, ret)
            elif 'write_close' == mask:
                ret = self._addMask(pyinotify.IN_CLOSE_WRITE, ret)
            elif 'nowrite_close' == mask:
                ret = self._addMask(pyinotify.IN_CLOSE_NOWRITE, ret)
            elif 'create' == mask:
                ret = self._addMask(pyinotify.IN_CREATE, ret)
            elif 'delete' == mask:
                ret = self._addMask(pyinotify.IN_DELETE, ret)
            elif 'self_delete' == mask:
                ret = self._addMask(pyinotify.IN_DELETE_SELF, ret)
            elif 'modify' == mask:
                ret = self._addMask(pyinotify.IN_MODIFY, ret)
            elif 'self_move' == mask:
                ret = self._addMask(pyinotify.IN_MOVE_SELF, ret)
            elif 'move_from' == mask:
                ret = self._addMask(pyinotify.IN_MOVED_FROM, ret)
            elif 'move_to' == mask:
                ret = self._addMask(pyinotify.IN_MOVED_TO, ret)
            elif 'open' == mask:
                ret = self._addMask(pyinotify.IN_OPEN, ret)
            elif 'all' == mask:
                m = pyinotify.IN_ACCESS | pyinotify.IN_ATTRIB | pyinotify.IN_CLOSE_WRITE | \
                    pyinotify.IN_CLOSE_NOWRITE | pyinotify.IN_CREATE | pyinotify.IN_DELETE | \
                    pyinotify.IN_DELETE_SELF | pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF | \
                    pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO | pyinotify.IN_OPEN
                ret = self._addMask(m, ret)
            elif 'move' == mask:
                ret = self._addMask(pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO, ret)
            elif 'close' == mask:
                ret = self._addMask(pyinotify.IN_CLOSE_WRITE | IN_CLOSE_NOWRITE, ret)

        return ret
        
    def _addMask(self, new_option, current_options):
        if not current_options:
            return new_option
        else:
            return current_options | new_option
            
class IniParser(Parser):
    config_parser = ConfigParser.ConfigParser()
    
    def __init__(self, args):
        config_file = args.config
        if not config_file:
            config_file = ['watcher.ini', '~/.watcher/watcher.ini', '/etc/watcher.ini']
        self.config = self.config_parser.read(config_file)

    def jobs(self):
        jobs = []
        for section in self.config_parser.sections():
            mask = self._parseMask(self.config_parser.get(section, 'events').split(','))
            folder = self.config_parser.get(section, 'watch')
            recursive = self.config_parser.getboolean(section, 'recursive')
            command = self.config_parser.get(section, 'command')
            
            jobs.append(Job(mask, folder, recursive, command))
        
        return jobs
        
    
class YmlParser(Parser):
    def jobs(self):
        jobs = []
        return jobs
    
class Job(object):
    def __init__(self, mask, folder, recursive, command):
        self.mask = mask
        self.folder = folder
        self.recursive = recursive
        self.command = command
        
    def __str__(self):
        return self.command
