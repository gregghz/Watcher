#!/usr/bin/env python

import pyinotify
import daemon
import sys, os
import datetime
import subprocess
from types import *
from string import Template
from yaml import load, dump # load is for read yaml, dump is for writing
try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, command):
        pyinotify.ProcessEvent.__init__(self)
        self.command = command

    def runCommand(self, event):
        t = Template(self.command)
        command = t.substitute(watched=event.path, filename=event.pathname, tflags=event.maskname, nflags=event.mask)
        subprocess.call(command.split())

    def process_IN_ACCESS(self, event):
        print "Access: ", event.pathname
        self.runCommand(event)

    def process_IN_ATTRIB(self, event):
        print "Attrib: ", event.pathname
        self.runCommand(event)

    def process_IN_CLOSE_WRITE(self, event):
        print "Close write: ", event.pathname
        self.runCommand(event)

    def process_IN_CLOSE_NOWRITE(self, event):
        print "Close nowrite: ", event.pathname
        self.runCommand(event)

    def process_IN_CREATE(self, event):
        print "Creating: ", event.pathname
        self.runCommand(event)

    def process_IN_DELETE(self, event):
        print "Deleteing: ", event.pathname
        self.runCommand(event)

    def process_IN_MODIFY(self, event):
        print "Modify: ", event.pathname
        self.runCommand(event)

    def process_IN_MOVE_SELF(self, event):
        print "Move self: ", event.pathname
        self.runCommand(event)

    def process_IN_MOVED_FROM(self, event):
        print "Moved from: ", event.pathname
        self.runCommand(event)

    def process_IN_MOVED_TO(self, event):
        print "Moved to: ", event.pathname
        self.runCommand(event)

    def process_IN_OPEN(self, event):
        print "Opened: ", event.pathname
        self.runCommand(event)

class WatcherDaemon(daemon.Daemon):
    def run(self):
        print datetime.datetime.today()

        dir = self._loadWatcherDirectory()
        jobs_file = file(dir + '/jobs.yml', 'r')
        wdds = []
        notifiers = []

        # parse jobs.yml and add_watch/notifier for each entry
        jobs = load(jobs_file, Loader=Loader)
        for job in jobs.iteritems():
            sys.stdout.write(job[0] + "\n")
            # get the basic config info
            mask = self._parseMask(job[1]['events'])
            folder = job[1]['watch']
            recursive = job[1]['recursive']
            command = job[1]['command']

            wm = pyinotify.WatchManager()
            handler = EventHandler(command)

            wdds.append(wm.add_watch(folder, mask, rec=recursive))
            # BUT we need a new ThreadNotifier so I can specify a different
            # EventHandler instance for each job
            # this means that each job has its own thread as well (I think)
            notifiers.append(pyinotify.ThreadedNotifier(wm, handler))

        # now we need to start ALL the notifiers.
        # TODO: load test this ... is having a thread for each a problem?
        for notifier in notifiers:
            notifier.start()

    def _loadWatcherDirectory(self):
        home = os.path.expanduser('~')
        watcher_dir = home + '/.watcher'
        jobs_file = watcher_dir + '/jobs.yml'

        if not os.path.isdir(watcher_dir):
            # create directory
            os.path.mkdir(watcher_dir)

        if not os.path.isfile(jobs_file):
            # create jobs.yml
            f = open(jobs_file, 'w')
            f.close()

        return watcher_dir

    def _parseMask(self, masks):
        ret = False;

        for mask in masks:
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

if __name__ == "__main__":
    log = '/tmp/watcher_out'
    try:
        # TODO: make stdout and stderr neutral location
        daemon = WatcherDaemon('/tmp/watcher.pid', stdout=log, stderr=log)
        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                f = open(log, 'w')
                f.close()
                daemon.start()
            elif 'stop' == sys.argv[1]:
                os.remove(log)
                daemon.stop()
            elif 'restart' == sys.argv[1]:
                daemon.restart()
            elif '--non-daemon' == sys.argv[1]:
                daemon.run()
            else:
                print "Unkown Command"
                sys.exit(2)
            sys.exit(0)
        else:
            print "Usage: %s start|stop|restart" % sys.argv[0]
            sys.exit(2)
    except Exception, e:
        print e
        os.remove(log)
        raise