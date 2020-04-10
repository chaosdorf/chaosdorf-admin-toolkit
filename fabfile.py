from fabric import task
from fabric.connection import Connection
import io

all_hosts=list(map(lambda x: 'root@{}.chaosdorf.de'.format(x), 'backend dashbaord extern intern shells vm'.split()))

# Git helpers

def etckeeper_check(c):
    c.run('etckeeper pre-install')

def etckeeper_commit(c, message):
    c.run('''if etckeeper unclean; then etckeeper commit '{}'; fi'''.format(message))

def etckeeper_done(c):
    c.run('etckeeper post-install')

def usrlocal_check(c):
    c.run('cd /usr/local && test -z "`git status --porcelain`"')

def usrlocal_commit(c, message):
    c.run('''if test -n "`git status --porcelain`"; then git add -A .; git commit -m '{}'; fi'''.format(message))

# Checks

@task(hosts=all_hosts)
def test(c):
    c.run('uptime')

@task(hosts=all_hosts)
def checkrestart(c):
    c.run('checkrestart')

# Upgrade cgit

@task(hosts=['root@intern.chaosdorf.de'])
def cgit(c):
    c.run('if ! test -e /opt/cgit/src; then apt --quiet --assume-yes install build-essential libssl-dev zlib1g-dev; mkdir -p /opt/cgit/static; git clone --recursive https://git.zx2c4.com/cgit /opt/cgit/src; fi')
    with c.cd('/opt/cgit/src'):
        c.run('git pull')
        c.run('git submodule update --init')
        c.run('make')
        c.run('cp cgit /opt/cgit/cgit.cgi')
        c.run('cp cgit.css cgit.png /opt/cgit/static')

# Add user

@task(hosts=['root@backend.chaosdorf.de'])
def ldapuser(c, user_name, first_name, last_name):
    c.run('''cpu useradd -f '{first_name}' -E '{last_name}' -e '{user_name}@chaosdorf.de' '{user_name}' '''.format(user_name=user_name, first_name=first_name, last_name=last_name))
    ldappasswd(c, user_name)

@task(hosts=['root@backend.chaosdorf.de'])
def ldappasswd(c, user_name):
    c.run('''ldappasswd -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de uid='{user_name}',ou=People,dc=chaosdorf,dc=de'''.format(user_name=user_name))

@task(hosts=['root@intern.chaosdorf.de'])
def maildir(c, user_name):
    c.run('''mkdir -p '/srv/mail/{user_name}' '''.format(user_name=user_name))
    c.run('''chown -R '{user_name}:{user_name}' '/srv/mail/{user_name}' '''.format(user_name=user_name))

@task
def user(c, user_name, first_name, last_name):
    with Connection('root@backend.chaosdorf.de') as c_backend:
        ldapuser(c_backend, user_name, first_name, last_name)

    with Connection('root@intern.chaosdorf.de') as c_intern:
        maildir(c_intern, user_name)

# Set external Mail Forwarding address

@task(hosts=['root@backend.chaosdorf.de'])
def mailforward(c, user_name, mail_forward):
    ldif = '''dn: uid={user_name},ou=People,dc=chaosdorf,dc=de
changetype: modify
replace: mailRoutingAddress
mailRoutingAddress: {mail_forward}
'''.format(user_name=user_name, mail_forward=mail_forward)
    c.put(io.StringIO(ldif), 'fabfile_aliases.ldif')
    c.run('ldapmodify -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de -f fabfile_aliases.ldif')
    c.run('rm fabfile_aliases.ldif')

# Add Jabber account

@task(hosts=['root@extern.chaosdorf.de'])
def jabber_adduser(c, user_name):
    print('Temporaeres Passwort: ', end='')
    c.run('pwgen -s 23 1')
    c.run('''sudo -u prosody prosodyctl adduser '{user_name}@chaosdorf.de' '''.format(user_name=user_name))

# Delete user

@task(hosts=['root@backend.chaosdorf.de'])
def ldapdeluser(c, user):
    c.run('''cpu userdel '{user}' && cpu groupdel '{user}' '''.format(user=user))

@task(hosts=['root@intern.chaosdorf.de'])
def archive_maildir(c, user):
    c.run('''if test -d '/srv/mail/{user}'; then cd /srv/mail && tar czf '{user}.tgz' '{user}' && chmod 600 '{user}.tgz' && rm -r '{user}'; fi'''.format(user=user))

@task(hosts=['root@extern.chaosdorf.de', 'root@shells.chaosdorf.de'])
def archive_home(c, user):
    c.run('''if test -d '/home/{user}'; then cd /home && tar czf '{user}.tgz' '{user}' && chmod 600 '{user}.tgz' && rm -r '{user}'; fi'''.format(user=user))

@task(hosts=['root@shells.chaosdorf.de'])
def remove_crontab(c, user):
    c.run(f'rm -f /var/spool/cron/crontabs/{user}')

@task
def deluser(c, user_name):
    with Connection('root@backend.chaosdorf.de') as c_backend:
        ldapdeluser(c_backend, user_name)
    with Connection('root@intern.chaosdorf.de') as c_intern:
        archive_maildir(c_intern, user_name)
    with Connection('root@extern.chaosdorf.de') as c_extern:
        archive_home(c_extern, user_name)
    with Connection('root@shells.chaosdorf.de') as c_shells:
        archive_home(c_shells, user_name)
        remove_crontab(c_shells, user_name)
