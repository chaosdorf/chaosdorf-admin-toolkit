from __future__ import with_statement
from fabric.api import *
from fabric.contrib.files import exists

import os
from StringIO import StringIO

if not env.hosts:
    env.hosts = [
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

def usrlocal_check():
    with cd('/usr/local'):
        sudo('test -z "`git status --porcelain`"')

def usrlocal_commit(message):
    with cd('/usr/local'):
        sudo('if test -n "`git status --porcelain`"; then git add -A .; git commit -m "%s"; fi' % message)

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


def upgrade():
    sudo("apt-get dist-upgrade --quiet")
    
def checkrestart():
    sudo("checkrestart")

@hosts('backend.chaosdorf.de')
def ldapuser(user_name, first_name, last_name):
    sudo('cpu useradd -f %s -E %s -e %s@chaosdorf.de %s' % (first_name, last_name, user_name, user_name))
    sudo('ldappasswd -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de uid=%s,ou=People,dc=chaosdorf,dc=de' % user_name)

@hosts('backend.chaosdorf.de')
def ldappasswd(user_name):
    sudo('ldappasswd -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de uid=%s,ou=People,dc=chaosdorf,dc=de' % user_name)

@hosts('intern.chaosdorf.de')
def maildir(user_name):
    sudo('mkdir -p /srv/mail/%s' % user_name)
    sudo('chown -R %s:%s /srv/mail/%s' % (user_name, user_name, user_name))

# by default, fabric runs the user target for each host, even though
# ldapuser and maildir only work for one. Limiting it to one host fixes this.
@hosts('backend.chaosdorf.de')
def user(user_name, first_name, last_name):
    execute(ldapuser, user_name, first_name, last_name)
    execute(maildir, user_name)

@hosts('backend.chaosdorf.de')
def mailforward(user_name, mail_forward):
    ldif = '''dn: uid=%s,ou=People,dc=chaosdorf,dc=de
changetype: modify
replace: mailRoutingAddress
mailRoutingAddress: %s
''' % (user_name, mail_forward)
    put(StringIO(ldif), 'fabfile_aliases.ldif')
    sudo('ldapmodify -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de -f fabfile_aliases.ldif')

@hosts('backend.chaosdorf.de')
def sshkey(user_name, key_file):
    key = open(key_file).read().replace("\n", '').replace("\r", '')
    ldif = '''dn: uid=%s,ou=People,dc=chaosdorf,dc=de
changetype: modify
add: sshPublicKey
sshPublicKey: %s
''' % (user_name, key)
    put(StringIO(ldif), 'fabfile_keys.ldif')
    sudo('ldapmodify -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de -f fabfile_keys.ldif')

@hosts('extern.chaosdorf.de')
def upgrade_mediawiki(version):
    with cd('/root'):
        sudo('bash /root/sqldump.sh > /root/mediawiki_before_upgrade_%s.sql' % version)
    with cd('/srv/www'):
        sudo('wget --quiet -O mediawiki.tar.gz http://releases.wikimedia.org/mediawiki/%s/mediawiki-%s.tar.gz' 
             % ('.'.join(version.split('.')[0:2]), version))
        sudo('tar xf mediawiki.tar.gz -C /srv/www/de.chaosdorf.wiki --strip-components=1')
        sudo('rm mediawiki.tar.gz')
        with cd('de.chaosdorf.wiki'):
            with cd('maintenance'):
                sudo('php update.php')
            sudo('git add -A')
            sudo('git commit -m "Upgrade auf MediaWiki %s"' % version)

@hosts('extern.chaosdorf.de')
def deploy_raumstatus():
    etckeeper_check()
    usrlocal_check()
    put('raumstatus/raumstatus_update', '/usr/local/bin', use_sudo=True, mode=0755)
    put('raumstatus/cron', '/etc/cron.d/chaosdorf-raumstatus', use_sudo=True)
    sudo('chown root:root /etc/cron.d/chaosdorf-raumstatus')
    put('raumstatus/bilder/*.png', '/srv/www/de.chaosdorf/raumstatus', use_sudo=True)
    etckeeper_commit('raumstatus update')
    usrlocal_commit('raumstatus update')

@hosts('intern.chaosdorf.de')
def cgit():
    if exists('/opt/cgit/src'):
        with cd('/opt/cgit/src') as d:
            sudo('git pull')
            sudo('git submodule update --init')
    else:
        sudo('apt-get install --assume-yes build-essential libssl-dev zlib1g-dev')
        sudo('mkdir -p /opt/cgit/static')
        sudo('git clone --recursive http://git.zx2c4.com/cgit '
                '/opt/cgit/src')

    with cd('/opt/cgit/src') as d:
        sudo('make')
        sudo('cp cgit /opt/cgit/cgit.cgi')
        sudo('cp cgit.css cgit.png /opt/cgit/static')
