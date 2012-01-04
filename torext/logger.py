#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# custom loggers, for monitoring and output formatting
#

import logging

################
#  formatters  #
################

plainFormatter = logging.Formatter('. %(message)s')

##############
#  handlers  #
##############

streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(plainFormatter)

#############
#  loggers  #
#############

plainLogger = logging.getLogger('plain')
plainLogger.setLevel(logging.DEBUG)
plainLogger.addHandler(streamHandler)
