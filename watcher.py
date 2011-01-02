#!/usr/bin/env python
# Copyright (c) 2010 Greggory Hernandez

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import sys, os, time, atexit
from signal import SIGTERM
import pyinotify
import sys, os
import datetime
import subprocess
from types import *
from string import Template
import ConfigParser
import argparse

class Daemon:
    """
    A generic daemon class

    Usage: subclass the Daemon class and override the run method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced Programming in the
        UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                #exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        #redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        #write pid file
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exists. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the Daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """

class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, command):
        pyinotify.ProcessEvent.__init__(self)
        self.command = command

    def runCommand(self, event):
        t = Template(self.command)
        command = t.substitute(watched=event.path, filename=event.pathname, tflags=event.maskname, nflags=event.mask)
        try:
            subprocess.call(command.split())
        except OSError, err:
            print "Failed to run command '%s' %s" % (command, str(err))

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

class WatcherDaemon(Daemon):

    def __init__(self, config):
        self.stdin   = '/dev/null'
        self.stdout  = config.get('DEFAULT','logfile')
        self.stderr  = config.get('DEFAULT','logfile')
        self.pidfile = config.get('DEFAULT','pidfile')
        self.config  = config

    def run(self):
        print datetime.datetime.today()
        wdds      = []
        notifiers = []

        # read jobs from config file
        for section in self.config.sections():
            sys.stdout.write(section + "\n")
            # get the basic config info
            mask      = self._parseMask(self.config.get(section,'events').split(','))
            folder    = self.config.get(section,'watch')
            recursive = self.config.getboolean(section,'recursive')
            command   = self.config.get(section,'command')

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

if __name__ == "__main__":
    # Parse commandline arguments
    parser = argparse.ArgumentParser(
                description='A daemon to monitor changes within specified directories and run commands on these changes.',
             )
    parser.add_argument('-c','--config',
                        action='store',
                        help='Path to the config file (default: %(default)s)')
    parser.add_argument('command',
                        action='store',
                        choices=['start','stop','restart','debug'],
                        help='What to do. Use debug to start in the foreground')
    args = parser.parse_args()

    # Parse the config file
    config = ConfigParser.ConfigParser()
    if(args.config):
        confok = config.read(args.config)
    else:
        confok = config.read(['/etc/watcher.ini', os.path.expanduser('~/.watcher.ini')]);

    if(confok):
        print "Read config from %s" % str(confok);
    else:
        print "Failed to read config file."
        sys.exit(4);

    # Initialize the daemon
    daemon = WatcherDaemon(config)

    # Execute the command
    if 'start' == args.command:
        daemon.start()
    elif 'stop' == args.command:
        os.remove(log)
        daemon.stop()
    elif 'restart' == args.command:
        daemon.restart()
    elif 'debug' == args.command:
        daemon.run()
    else:
        print "Unkown Command"
        sys.exit(2)
    sys.exit(0)
