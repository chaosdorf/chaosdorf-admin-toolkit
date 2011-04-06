from fabric.api import *

env.hosts = [
	'root@chaosdorf.dyndns.org', 
	'root@backend.chaosdorf.de',
	'root@frontend.chaosdorf.de',
	'root@shells.chaosdorf.de',
	'root@vm.chaosdorf.de',
]

def deploy(file):
	put("../%s" % file, '/tmp/')
	run('etckeeper pre-install')
	run("dpkg --install /tmp/%s" % file)
	run('etckeeper post-install')
	run("rm /tmp/%s" % file)
