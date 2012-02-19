from __future__ import with_statement
from fabric.api import *

env.hosts = [
	'root@chaosdorf.dyndns.org',
	'root@backend.chaosdorf.de',
	'root@extern.chaosdorf.de',
	'root@frontend.chaosdorf.de',
	'root@shells.chaosdorf.de',
	'root@vm.chaosdorf.de',
]

env.shell = '/bin/sh -c'

def etckeeper_check():
	run('etckeeper pre-install')

def etckeeper_commit(message):
	run('if etckeeper unclean; then etckeeper commit "%s"; fi' % message)

def etckeeper_done():
	run('etckeeper post-install')

def configs():
	etckeeper_check()
	put('dotfiles/zshrc', '/root/.zshrc')
	put('etckeeper/etckeeper.conf', '/etc/etckeeper/')
	put('apt/99checkrestart', '/etc/apt/apt.conf.d/')
	etckeeper_commit('chaosdorf-admin-toolkit configfile updates')

def deploy(version):
	etckeeper_check()
	put("../chaosdorf-admin-toolkit_%s_all.deb" % version, '/root/')
	run("dpkg --install /root/chaosdorf-admin-toolkit_%s_all.deb" % version)
	run("rm /root/chaosdorf-admin-toolkit_%s_all.deb" % version)
	etckeeper_done()
