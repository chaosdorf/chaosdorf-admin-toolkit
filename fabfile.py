from fabric import task
from fabric.connection import Connection
import io
import json

# Usage: fab --prompt-for-sudo-password -H user@host some-task
# Or: fab -H root@host some-task

all_hosts = list(
    map(
        lambda x: "root@{}.chaosdorf.de".format(x),
        "backend dashbaord extern intern shells vm".split(),
    )
)

# Git helpers


def etckeeper_check(c):
    c.sudo("etckeeper pre-install")


def etckeeper_commit(c, message):
    if c.sudo("etckeeper unclean", warn=True).ok:
        c.sudo(f"etckeeper commit '{message}'")


def etckeeper_done(c):
    c.sudo("etckeeper post-install")


def usrlocal_check(c):
    c.sudo('cd /usr/local && test -z "`git status --porcelain`"')


def usrlocal_commit(c, message):
    c.sudo(
        """if test -n "`git status --porcelain`"; then git add -A .; git commit -m '{}'; fi""".format(
            message
        )
    )


def install(c, source, destination, mode="0644", owner=None, group=None):
    install_cmd = f"install -m {mode}"
    if owner is not None and group is not None:
        install_cmd += f" -o {owner} -g {group}"
    install_cmd += f" /tmp/.chaosdorf-admin-tmp {destination}"

    c.put(source, "/tmp/.chaosdorf-admin-tmp")
    c.sudo(install_cmd)
    c.run("rm /tmp/.chaosdorf-admin-tmp")


# Checks


@task(hosts=all_hosts)
def test(c):
    c.run("uptime")


@task(hosts=all_hosts)
def checkrestart(c):
    c.run("checkrestart")


# Add user


@task(hosts=["root@backend.chaosdorf.de"])
def ldapuser(c, user_name, first_name, last_name):
    c.run(
        """cpu useradd -f '{first_name}' -E '{last_name}' -e '{user_name}@chaosdorf.de' '{user_name}' """.format(
            user_name=user_name, first_name=first_name, last_name=last_name
        )
    )
    ldappasswd(c, user_name)


@task(hosts=["root@backend.chaosdorf.de"])
def ldappasswd(c, user_name):
    c.run(
        """ldappasswd -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de uid='{user_name}',ou=People,dc=chaosdorf,dc=de""".format(
            user_name=user_name
        )
    )


@task(hosts=["root@intern.chaosdorf.de"])
def maildir(c, user_name):
    c.run("""mkdir -p '/srv/mail/{user_name}' """.format(user_name=user_name))
    c.run(
        """chown -R '{user_name}:{user_name}' '/srv/mail/{user_name}' """.format(
            user_name=user_name
        )
    )


@task
def user(c, user_name, first_name, last_name):
    with Connection("root@backend.chaosdorf.de") as c_backend:
        ldapuser(c_backend, user_name, first_name, last_name)

    with Connection("root@intern.chaosdorf.de") as c_intern:
        maildir(c_intern, user_name)


# Set external Mail Forwarding address


@task(hosts=["root@backend.chaosdorf.de"])
def mailforward(c, user_name, mail_forward):
    ldif = """dn: uid={user_name},ou=People,dc=chaosdorf,dc=de
changetype: modify
replace: mailRoutingAddress
mailRoutingAddress: {mail_forward}
""".format(
        user_name=user_name, mail_forward=mail_forward
    )
    c.put(io.StringIO(ldif), "fabfile_aliases.ldif")
    c.run(
        "ldapmodify -y /root/ldap_password -x -W -D cn=admin,dc=chaosdorf,dc=de -f fabfile_aliases.ldif"
    )
    c.run("rm fabfile_aliases.ldif")


# Add Jabber account


@task(hosts=["root@extern.chaosdorf.de"])
def jabber_adduser(c, user_name):
    print("Temporaeres Passwort: ", end="")
    c.run("pwgen -s 23 1")
    c.run(
        """sudo -u prosody prosodyctl adduser '{user_name}@chaosdorf.de' """.format(
            user_name=user_name
        )
    )


# Delete user


@task(hosts=["root@backend.chaosdorf.de"])
def ldapdeluser(c, user):
    c.run("""cpu userdel '{user}' && cpu groupdel '{user}' """.format(user=user))


@task(hosts=["root@intern.chaosdorf.de"])
def archive_maildir(c, user):
    c.run(
        """if test -d '/srv/mail/{user}'; then cd /srv/mail && tar czf '{user}.tgz' '{user}' && chmod 600 '{user}.tgz' && rm -r '{user}'; fi""".format(
            user=user
        )
    )


@task(hosts=["root@extern.chaosdorf.de", "root@shells.chaosdorf.de"])
def archive_home(c, user):
    c.run(
        """if test -d '/home/{user}'; then cd /home && tar czf '{user}.tgz' '{user}' && chmod 600 '{user}.tgz' && rm -r '{user}'; fi""".format(
            user=user
        )
    )


@task(hosts=["root@shells.chaosdorf.de"])
def remove_crontab(c, user):
    c.run(f"rm -f /var/spool/cron/crontabs/{user}")


@task
def deluser(c, user_name):
    with Connection("root@backend.chaosdorf.de") as c_backend:
        ldapdeluser(c_backend, user_name)
    with Connection("root@intern.chaosdorf.de") as c_intern:
        archive_maildir(c_intern, user_name)
    with Connection("root@extern.chaosdorf.de") as c_extern:
        archive_home(c_extern, user_name)
    with Connection("root@shells.chaosdorf.de") as c_shells:
        archive_home(c_shells, user_name)
        remove_crontab(c_shells, user_name)


# monitoring/config/auth.json must contain {"user":"...","password":"..."}
# (with the Icinga2 API credentials filled in).
# It is not part of this repository.
@task
def deploy_icinga_client(c, hostname):
    with open(f"monitoring/config/{hostname}.json", "r") as f:
        client_config = json.load(f)
    with open("monitoring/config/auth.json", "r") as f:
        auth_config = json.load(f)

    client_config["auth"] = [auth_config["user"], auth_config["password"]]

    etckeeper_check(c)

    if c.run("getent passwd nagios", warn=True).failed:
        c.sudo(
            "adduser --quiet --system --no-create-home --disabled-login --shell /bin/sh --home /var/lib/nagios nagios"
        )
        c.sudo("apt-get update")
        c.sudo("apt-get install monitoring-plugins-basic python3-requests")
        c.sudo("mkdir -p /etc/nagios")
        c.sudo("chmod 755 /etc/nagios")

    install(
        c,
        io.StringIO(json.dumps(client_config, indent=4)),
        "/etc/nagios/api.json",
        "0660",
        "nagios",
        "root",
    )
    for check in "git_status kernel libs_ng sympa systemd wordpress".split():
        install(
            c,
            f"monitoring/checks/check_{check}",
            f"/usr/lib/nagios/plugins/check_{check}",
            "0755",
        )
    install(c, "sudoers.d/nagios", "/etc/sudoers.d/nagios", "0440")
    install(
        c, "monitoring/icinga-run-checks", "/usr/local/lib/icinga-run-checks", "0755"
    )
    install(c, "monitoring/cron", "/etc/cron.d/chaosdorf-admin-toolkit")

    etckeeper_commit(c, "deploy icinga2 checks")


@task
def deploy_weekly_backup(c):
    etckeeper_check(c)

    c.sudo("apt-get -y update")
    c.sudo("apt-get -y install gpg")

    c.put("backup/pubkey", "/tmp")
    c.sudo("gpg --import /tmp/pubkey")
    c.run("rm /tmp/pubkey")

    install(c, "backup/backup_external", "/usr/sbin/backup_external", "0755")
    install(c, "backup/cron", "/etc/cron.d/chaosdorf-backup", "0644")

    etckeeper_commit(c, "deploy weekly backup")
