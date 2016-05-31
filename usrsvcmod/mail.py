'''
    Copyright (c) 2016 Tim Savannah All Rights Reserved.
    This software is licensed under the terms of the GPLv3.
    This may change at my discretion, retroactively, and without notice.

    You should have received a copy of this with the source distribution as a file titled, LICENSE.

    The most current license can be found at:
    https://github.com/kata198/usrsvc/LICENSE

    This location may need to be changed at some point in the future, in which case
    you are may email Tim Savannah <kata198 at gmail dot com>, or find them on the
    current website intended for distribution of usrsvc.


    usrsvc mail function
'''

# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :

import subprocess2 as subprocess

from .util import getUsername, getHostname

__all__ =  ('SendmailFailedException', 'sendmail' )

SENDMAIL_TIMEOUT = 2

class SendmailFailedException(Exception):
    pass

def sendmail(sendmailPath, to, subject, body):
    mailHeaders = ["To: " + to, "Subject: " + subject]

    username = getUsername()
    hostname = getHostname()

    mailHeaders.append('From: %s@%s' %(username, hostname))

    pipe = subprocess.Popen([sendmailPath, to], shell=False, stdin=subprocess.PIPE)

    pipe.stdin.write( ('\r\n'.join(mailHeaders)).encode('utf-8'))
    pipe.stdin.write(b'\r\n\r\n')
    if bytes != str and type(body) == str:
        body = body.encode('utf-8')

    pipe.stdin.write(body)
    pipe.stdin.close()

    ret = pipe.waitOrTerminate(SENDMAIL_TIMEOUT, .05, 1)
    if ret['actionTaken'] == subprocess.SUBPROCESS2_PROCESS_COMPLETED:
        if ret['returnCode'] == 0:
            return True
        else:
            raise SendmailFailedException('Failed to send email using %s to=%s subject=%s. Return Code: %s' %(sendmailPath, to, subject, str(ret['returnCode'])))
    else:
        raise SendmailFailedException('Sendmail at %s failed to send email in %d seconds and had to be terminated. to=%s subject=%s' %(sendmailPath, SENDMAIL_TIMEOUT, to, subject))


# vim:set ts=4 shiftwidth=4 softtabstop=4 expandtab :
