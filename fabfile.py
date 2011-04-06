from fabric.api import *

env.hosts = [
	'root@chaosdorf.dyndns.org', 
	'root@backend.chaosdorf.de',
	'root@frontend.chaosdorf.de',
	'root@shells.chaosdorf.de',
	'root@vm.chaosdorf.de',
]

def deploy(version):
	put("../chaosdorf-admin-toolkit_%s_all.deb" % version, '/tmp/')
	run('etckeeper pre-install')
	run("dpkg --install /tmp/chaosdorf-admin-toolkit_%s_all.deb" % version)
	run('etckeeper post-install')
	run("rm /tmp/chaosdorf-admin-toolkit_%s_all.deb" % version)

def configs():
	put('etckeeper/etckeeper.conf', '/etc/etckeeper/')
