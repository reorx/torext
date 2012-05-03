#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


# zh_CN
def sharp(s):
    if not isinstance(s, unicode):
        s = unicode(s, 'utf8')
    rep = re.compile(ur'#[\w\u2E80-\u9FFF]+')
    fits = []
    for i in rep.findall(s):
        fits.append(
            re.search(ur'[\w\u2E80-\u9FFF]+', i).group())
    return fits


# zh_CN
def frank(s):
    if not isinstance(s, unicode):
        s = unicode(s, 'utf8')
    rep = re.compile(ur'[\w\u2E80-\u9FFF]+')
    return rep.findall(s)


def src2name(src):
    rep = re.compile(ur'[\w]+')
    src_red = rep.findall(src)
    if not src_red:
        return None
    return '_'.join(src_red)


def plainstr(s):
    rep = re.compile(ur'[\w][^\n]+')
    s_red = rep.findall(s)
    if not s_red:
        return None
    return s_red[0]


class TextFilter(object):
    def __init__(self, mode=str):
        self.mode = mode

    def _search(self, p, s):
        res = re.search(p, s)
        if not res:
            return None
        else:
            return self.mode(res.group())

    def clean(self, s):
        mode = self.mode
        if str == mode:
            return self._search('.+', s)
        if int == mode:
            return self._search('\d+', s)
