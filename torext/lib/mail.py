#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib


class EmailSender(object):
    def __init__(self, hostport, username, password, **kwgs):
        self.info = {
            'hostport': hostport,
            'username': username,
            'password': password,
        }
        self.toaddrs = []
        self._connect()
        if 'fromaddr' in kwgs and 'body' in kwgs:
            self.set_fromaddr(kwgs['fromaddr'])
            self.set_body(kwgs['body'])
            if 'toaddr' in kwgs:
                self.set_toaddr(kwgs['toaddr'])
            elif 'toaddrs'in kwgs:
                for i in kwgs['toaddrs']:
                    self.set_toaddr(i)
            else:
                raise Exception('lost kwarg `toaddr` or `toaddrs`')

    def _connect(self):
        info = self.info
        client = smtplib.SMTP(info['hostport'])
        client.ehlo()
        client.starttls()
        client.login(info['username'], info['password'])
        self.client = client

    def set_fromaddr(self, fromaddr):
        self.fromaddr = fromaddr

    def set_toaddr(self, toaddr):
        if not toaddr in self.toaddrs:
            self.toaddrs.append(toaddr)

    def set_body(self, body, html_body=None):
        # TODO html_body apply
        self.body = body

    def set_attachment(self, fname):
        raise NotImplementedError

    def send(self):
        print self.__dict__
        if not hasattr(self, 'fromaddr'):
            raise NotImplementedError
        self.client.sendmail(self.fromaddr, self.toaddrs, self.body)

    def close(self):
        self.client.quit()


def send_once_from_gmail(u, p, fr, to, body):
    HOST_PORT = 'smtp.gmail.com:587'
    sender = EmailSender(HOST_PORT, u, p)
    sender.set_fromaddr(fr)
    sender.set_toaddr(to)
    sender.set_body(body)
    sender.send()
    sender.close()


if __name__ == '__main__':
    import sys

    HOST_PORT = 'smtp.gmail.com:587'
    sender = EmailSender(HOST_PORT, 'reorx.xiao@gmail.com', 'mx320lf2')
    sender.set_fromaddr('reorx.xiao@gmail.com')
    sender.set_toaddr('595895020@qq.com')
    sender.set_toaddr('novoreorx@gmail.com')
    sender.set_body('wo cao')
    sender.send()
    sender.close()
