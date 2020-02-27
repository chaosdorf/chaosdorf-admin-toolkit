from fabric import task

@task(hosts=['root@backend.chaosdorf.de'])
def deluser(c, user):
    c.run('''cpu userdel '{user}' && cpu groupdel '{user}' '''.format(user=user))

@task(hosts=['root@intern.chaosdorf.de'])
def archive_maildir(c, user):
    c.run('''if test -d '/srv/mail/{user}'; then cd /srv/mail && tar czf '{user}.tgz' '{user}' && chmod 600 '{user}.tgz' && rm -r '{user}'; fi'''.format(user=user))

@task(hosts=['root@extern.chaosdorf.de', 'root@shells.chaosdorf.de'])
def archive_home(c, user):
    c.run('''if test -d '/home/{user}'; then cd /home && tar czf '{user}.tgz' '{user}' && chmod 600 '{user}.tgz' && rm -r '{user}'; fi'''.format(user=user))
