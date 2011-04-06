from fabric.api import *

env.hosts = [
	'root@chaosdorf.dyndns.org', 
	'root@backend.chaosdorf.de',
	'root@frontend.chaosdorf.de',
	'root@shells.chaosdorf.de',
	'root@vm.chaosdorf.de',
]

env.shell = '/bin/sh -c'

def check_etc():
	run('etckeeper pre-install')

def deploy(version):
	check_etc()
	put("../chaosdorf-admin-toolkit_%s_all.deb" % version, '/tmp/')
	run("dpkg --install /tmp/chaosdorf-admin-toolkit_%s_all.deb" % version)
	run('etckeeper post-install')
	run("rm /tmp/chaosdorf-admin-toolkit_%s_all.deb" % version)

def configs():
	check_etc()
	put('dotfiles/zshrc', '/root/.zshrc')
	put('etckeeper/etckeeper.conf', '/etc/etckeeper/')
	run('etckeeper commit "chaosdorf-admin-toolkit configfile updates"')
