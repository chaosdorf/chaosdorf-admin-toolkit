from __future__ import with_statement
from fabric.api import *

env.hosts = [
	'root@chaosdorf.dyndns.org',
	'backend.chaosdorf.de',
	'extern.chaosdorf.de',
	'intern.chaosdorf.de',
	'shells.chaosdorf.de',
	'vm.chaosdorf.de',
]

env.shell = '/bin/sh -c'

def etckeeper_check():
	sudo('etckeeper pre-install')

def etckeeper_commit(message):
	sudo('if etckeeper unclean; then etckeeper commit "%s"; fi' % message)

def etckeeper_done():
	sudo('etckeeper post-install')

def configs():
	etckeeper_check()
	put('etckeeper/etckeeper.conf', '/etc/etckeeper/', use_sudo=True)
	put('apt/99checkrestart', '/etc/apt/apt.conf.d/', use_sudo=True)
	etckeeper_commit('chaosdorf-admin-toolkit configfile updates')

def deploy(version):
	etckeeper_check()
	put("../chaosdorf-admin-toolkit_%s_all.deb" % version, '/root/', use_sudo=True)
	sudo("dpkg --install /root/chaosdorf-admin-toolkit_%s_all.deb" % version)
	sudo("rm /root/chaosdorf-admin-toolkit_%s_all.deb" % version)
	etckeeper_done()

def test():
    sudo("uptime")

def check_upgrades():
    sudo("apt-get dist-upgrade --simulate --quiet")

def upgrade():
    sudo("apt-get dist-upgrade --yes --quiet")

@hosts('backend.chaosdorf.de')
def user(user_name, first_name, last_name):
    sudo('cpu useradd -f %s -E %s -e %s@chaosdorf.de %s' % (first_name, last_name, user_name, user_name))
    sudo('ldappasswd -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de uid=%s,ou=People,dc=chaosdorf,dc=de' % user_name)

@hosts('backend.chaosdorf.de')
def mailforward(user_name, mail_forward):
    ldif = '''dn: uid=%s,ou=People,dc=chaosdorf,dc=de
changetype: modify
replace: mailRoutingAddress
mailRoutingAddress: %s
''' % (user_name, mail_forward)
    put(StringIO(ldif), 'fabfile_aliases.ldif')
    sudo('ldapmodify -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de -f fabfile_aliases.ldif')


# most munin plugins need to be edited and tested on figurehead
@hosts('root@chaosdorf.dyndns.org')
def get_munin_plugins():
	with cd('/usr/share/munin/plugins/'):
		get('freifunk_nodes', 'munin/')
		get('modem_status', 'munin/')
		get('online_ips', 'munin/')
		get('tc_new', 'munin/')
