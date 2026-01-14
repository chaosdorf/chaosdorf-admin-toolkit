#!/usr/bin/env python3

from email.message import EmailMessage
import subprocess
import sys

assert len(sys.argv) >= 2

nickname = sys.argv[1]

if len(sys.argv) >= 3:
    datum = f" seit {sys.argv[2]} "
else:
    datum = " "

body = f"""{nickname} ist{datum}nicht mehr Mitglied im Chaosdorf e.V. und daher nicht mehr auf dieser Mailingliste subscribed."""

msg = EmailMessage()
msg.set_content(body)

msg["Subject"] = "Mitgliederstatus (Abgang)"
msg["From"] = "Admins <admin@chaosdorf.de>"
msg["To"] = "Chaosdorf Intern <intern@chaosdorf.de>"

p = subprocess.Popen(
    [
        "ssh",
        "shells.chaosdorf.de",
        "/usr/sbin/sendmail",
        "-f",
        "kasse@chaosdorf.de",
        "-t",
        "-oi",
    ],
    stdin=subprocess.PIPE,
)
p.communicate(msg.as_bytes())
