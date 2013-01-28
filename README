See jobs.yml for proper configuration syntax

Dependencies: python, python-pyinotify, python-yaml

In Ubuntu (and Debian):

	sudo apt-get install python python-pyinotify python-yaml

make sure watcher.py is marked as executable

	chmod +x watcher.py


start the daemon with:

	./watcher.py start


stop it with:

	./watcher.py stop


restart it with:

	./watcher.py restart


The first time you start it (if you haven't done it yourself) it will
create ~/.watcher and ~/.watcher/jobs.yml and then it will yell at
you. You need to edit ~/.watcher/jobs.yml to setup folders to watch.
You'll find a jobs.yml in the same directory as this README. Use that
as an example. It should be pretty simple.

If you edit ~/.watcher/jobs.yml you must restart the daemon for it to
reload the configuration file. It'd make sense for me to set up
watcher to watch the config file. That'll be coming soon.

Problems? greggory.hz@gmail.com

Have fun.
