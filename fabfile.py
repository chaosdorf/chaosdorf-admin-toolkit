from __future__ import with_statement
from fabric.api import *

env.hosts = [
	'root@chaosdorf.dyndns.org', 
	'root@backend.chaosdorf.de',
	'root@frontend.chaosdorf.de',
	'root@shells.chaosdorf.de',
	'root@vm.chaosdorf.de',
]

env.shell = '/bin/sh -c'

def run_or_sudo(command, use_sudo):
	if use_sudo:
		sudo(command)
	else:
		run(command)

def etckeeper_check(use_sudo=False):
	run_or_sudo('etckeeper pre-install', use_sudo)

def etckeeper_commit(message, use_sudo=False):
	run_or_sudo('if etckeeper unclean; then etckeeper commit "%s"; fi' % message,
		use_sudo)

def etckeeper_done(use_sudo=False):
	run_or_sudo('etckeeper post-install', use_sudo)

# Fabric >= 1.0 can use sudo in put. However, thanks to
# <http://code.fabfile.org/issues/show/320>, this does not help me at all.
# So, I'll stick with 0.9.3 and use this instead. --derf
def put_sudo(local, remote):
	tmp = "/home/derf/fabtmp"
	put(local, tmp)
	sudo("mv %s %s" % (tmp, remote))
	sudo("chmod a+rX %s" % remote)

def put_icinga_check(name):
	put_sudo(
		"nagios-checks/remote/check_%s" % name,
		"/usr/local/lib/nagios/plugins/check_%s" % name,
	)


def configs():
	etckeeper_check()
	put('dotfiles/zshrc', '/root/.zshrc')
	put('etckeeper/etckeeper.conf', '/etc/etckeeper/')
	etckeeper_commit('chaosdorf-admin-toolkit configfile updates')

def deploy(version):
	etckeeper_check()
	put("../chaosdorf-admin-toolkit_%s_all.deb" % version, '/tmp/')
	run("dpkg --install /tmp/chaosdorf-admin-toolkit_%s_all.deb" % version)
	etckeeper_done()
	run("rm /tmp/chaosdorf-admin-toolkit_%s_all.deb" % version)

# Only for derf ;-)
@hosts('aneurysm')
def icinga():
	etckeeper_check(use_sudo=True)
	put_icinga_check('http_authed')
	put_icinga_check('mail_no_relay')
	put_icinga_check('rbl')
	put_icinga_check('ssh_no_password_login')
	put_icinga_check('websites')
	put_sudo('icinga/chaosdorf_websites.ini',
		'/etc/nagios/chaosdorf_websites.ini')
	put_sudo('icinga/chaosdorf.cfg', '/etc/icinga/objects/chaosdorf.cfg')
	put_sudo('icinga/checks.cfg', '/etc/nagios-plugins/config/chaosdorf.cfg')

	sudo('if ! /etc/init.d/icinga check; then etckeeper vcs checkout '
		+ 'icinga/objects/chaosdorf.cfg '
		+ 'nagios/chaosdorf_websites.ini '
		+ 'nagios-plugins/config/chaosdorf.cfg '
		+ '; exit 1; fi')

	sudo('/etc/init.d/icinga reload')
	etckeeper_commit('Icinga config updates from chaosdorf-admin-toolkit',
		use_sudo=True)
