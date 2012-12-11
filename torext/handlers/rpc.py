#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2009 Josh Marshall
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Ecosystem:

BaseRPCHandler              BaseRPCParser
    |                           |
JSONRPCHandler              JSONRPCParser
    _RPC_   <-------------------+
    |
PracticingRPCHandler
"""

try:
    import jsonrpclib
except ImportError:
    raise ImportError('You should install `jsonrpclib` before using rpc feature of torext')
from jsonrpclib.jsonrpc import isbatch, isnotification, Fault
from jsonrpclib.jsonrpc import dumps, loads

import inspect
import logging
import traceback

import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.web import RequestHandler


_string_types = (str, unicode)


# Configuration element
class Config(object):
    verbose = True
    short_errors = True

config = Config()


def getcallargs(func, *positional, **named):
    """
    Simple implementation of inspect.getcallargs function in
    the Python 2.7 standard library.

    Takes a function and the position and keyword arguments and
    returns a dictionary with the appropriate named arguments.
    Raises an exception if invalid arguments are passed.
    """
    args, varargs, varkw, defaults = inspect.getargspec(func)
    fname = func.__name__

    final_kwargs = {}
    extra_args = []
    has_self = inspect.ismethod(func) and func.im_self is not None
    if has_self:
        self_key = args.pop(0)

    # (Since our RPC supports only positional OR named.)
    if named:
        for key, value in named.iteritems():
            arg_key = None
            try:
                arg_key = args[args.index(key)]
            except ValueError:
                if not varkw:
                    raise TypeError("Keyword argument '%s' not valid" % key)
            if key in final_kwargs.keys():
                message = "Keyword argument '%s' used more than once" % key
                raise TypeError(message)
            final_kwargs[key] = value
    else:
        for i in range(len(positional)):
            value = positional[i]
            arg_key = None
            try:
                arg_key = args[i]
            except IndexError:
                if not varargs:
                    raise TypeError("Too many positional arguments")
            if arg_key:
                final_kwargs[arg_key] = value
            else:
                extra_args.append(value)
    if defaults:
        reverse_args = args[:]
        reverse_args.reverse()
        for i in range(len(defaults)):
            arg_key = reverse_args[i]
            final_kwargs.setdefault(arg_key, defaults[i])
    for arg in args:
        if arg not in final_kwargs:
            raise TypeError("Not all arguments supplied. (%s)", arg)
    return final_kwargs, extra_args


class BaseRPCParser(object):
    """
    This class is responsible for managing the request, dispatch,
    and response formatting of the system. It is tied into the
    _RPC_ attribute of the BaseRPCHandler (or subclasses) and
    populated as necessary throughout the request. Use the
    .faults attribute to take advantage of the built-in error
    codes.
    """
    content_type = 'text/plain'

    def __init__(self, library, encode=None, decode=None):
        # Attaches the RPC library and encode / decode functions.
        self.library = library
        if not encode:
            encode = getattr(library, 'dumps')
        if not decode:
            decode = getattr(library, 'loads')
        self.encode = encode
        self.decode = decode
        self.requests_in_progress = 0
        self.responses = []

    @property
    def faults(self):
        # Grabs the fault tree on request
        return Faults(self)

    def run(self, handler, request_body):
        """
        This is the main loop -- it passes the request body to
        the parse_request method, and then takes the resulting
        method(s) and parameters and passes them to the appropriate
        method on the parent Handler class, then parses the response
        into text and returns it to the parent Handler to send back
        to the client.
        """
        self.handler = handler
        try:
            requests = self.parse_request(request_body)
        except:
            self.traceback()
            return self.handler.result(self.faults.parse_error())
        #if type(requests) is not types.TupleType:
        if isinstance(requests, tuple):
            # SHOULD be the result of a fault call,
            # according tothe parse_request spec below.
            #if type(requests) in types.StringTypes:
            if isinstance(requests, _string_types):
                # Should be the response text of a fault
                return requests
            elif hasattr(requests, 'response'):
                # Fault types should have a 'response' method
                return requests.response()
            elif hasattr(requests, 'faultCode'):
                # XML-RPC fault types need to be properly dispatched. This
                # should only happen if there was an error parsing the
                # request above.
                return self.handler.result(requests)
            else:
                # No idea, hopefully the handler knows what it
                # is doing.
                return requests
        self.handler._requests = len(requests)
        for request in requests:
            self.dispatch(request[0], request[1])

    def dispatch(self, method_name, params):
        """
        This method walks the attribute tree in the method
        and passes the parameters, either in positional or
        keyword form, into the appropriate method on the
        Handler class. Currently supports only positional
        or keyword arguments, not mixed.
        """
        if method_name in dir(RequestHandler):
            # Pre-existing, not an implemented attribute
            return self.handler.result(self.faults.method_not_found())
        method = self.handler
        method_list = dir(method)
        method_list.sort()
        attr_tree = method_name.split('.')
        try:
            for attr_name in attr_tree:
                method = self.check_method(attr_name, method)
        except AttributeError:
            return self.handler.result(self.faults.method_not_found())
        if not callable(method):
            # Not callable, so not a method
            return self.handler.result(self.faults.method_not_found())
        if method_name.startswith('_') or \
                ('private' in dir(method) and method.private is True):
            # No, no. That's private.
            return self.handler.result(self.faults.method_not_found())
        args = []
        kwargs = {}
        #if type(params) is types.DictType:
        if isinstance(params, dict):
            # The parameters are keyword-based
            kwargs = params
        elif type(params) in (list, tuple):
            # The parameters are positional
            args = params
        else:
            # Bad argument formatting?
            return self.handler.result(self.faults.invalid_params())
        # Validating call arguments
        try:
            final_kwargs, extra_args = getcallargs(method, *args, **kwargs)
        except TypeError:
            return self.handler.result(self.faults.invalid_params())
        try:
            response = method(*extra_args, **final_kwargs)
        except Exception:
            self.traceback(method_name, params)
            return self.handler.result(self.faults.internal_error())

        if 'async' in dir(method) and method.async:
            # Asynchronous response -- the method should have called
            # self.result(RESULT_VALUE)
            if response is not None:
                # This should be deprecated to use self.result
                message = "Async results should use 'self.result()'"
                message += " Return result will be ignored."
                logging.warning(message)
        else:
            # Synchronous result -- we call result manually.
            return self.handler.result(response)

    def response(self, handler):
        """
        This is the callback for a single finished dispatch.
        Once all the dispatches have been run, it calls the
        parser library to parse responses and then calls the
        handler's asynch method.
        """
        handler._requests -= 1
        if handler._requests > 0:
            return
        # We are finished with requests, send response
        if handler._RPC_finished:
            # We've already sent the response
            raise Exception("Error trying to send response twice.")
        handler._RPC_finished = True
        responses = tuple(handler._results)
        response_text = self.parse_responses(responses)
        #if type(response_text) not in types.StringTypes:
        if isinstance(response_text, _string_types):
            # Likely a fault, or something messed up
            response_text = self.encode(response_text)
        # Calling the asynch callback
        handler.on_result(response_text)

    def traceback(self, method_name='REQUEST', params=[]):
        err_lines = traceback.format_exc().splitlines()
        err_title = "ERROR IN %s" % method_name
        if len(params) > 0:
            err_title = '%s - (PARAMS: %s)' % (err_title, repr(params))
        err_sep = ('-' * len(err_title))[:79]
        err_lines = [err_sep, err_title, err_sep] + err_lines
        if config.verbose is True:
            if len(err_lines) >= 7 and config.short_errors:
                # Minimum number of lines to see what happened
                # Plus title and separators
                print '\n'.join(err_lines[0:4] + err_lines[-3:])
            else:
                print '\n'.join(err_lines)
        # Log here
        return

    def parse_request(self, request_body):
        """
        Extend this on the implementing protocol. If it
        should error out, return the output of the
        'self.faults.fault_name' response. Otherwise,
        it MUST return a TUPLE of TUPLE. Each entry
        tuple must have the following structure:
        ('method_name', params)
        ...where params is a list or dictionary of
        arguments (positional or keyword, respectively.)
        So, the result should look something like
        the following:
        ( ('add', [5,4]), ('add', {'x':5, 'y':4}) )
        """
        return ([], [])

    def parse_responses(self, responses):
        """
        Extend this on the implementing protocol. It must
        return a response that can be returned as output to
        the client.
        """
        return self.encode(responses, methodresponse=True)

    def check_method(self, attr_name, obj):
        """
        Just checks to see whether an attribute is private
        (by the decorator or by a leading underscore) and
        returns boolean result.
        """
        if attr_name.startswith('_'):
            raise AttributeError('Private object or method.')
        attr = getattr(obj, attr_name)
        if 'private' in dir(attr) and attr.private is True:
            raise AttributeError('Private object or method.')
        return attr


class BaseRPCHandler(RequestHandler):
    """
    This is the base handler to be subclassed by the actual
    implementations and by the end user.
    """
    _RPC_ = None
    _results = None
    _requests = 0
    _RPC_finished = False

    @tornado.web.asynchronous
    def post(self):
        # Very simple -- dispatches request body to the parser
        # and returns the output
        self._results = []
        request_body = self.request.body
        self._RPC_.run(self, request_body)

    def result(self, result, *results):
        """ Use this to return a result. """
        if results:
            results = [result, ] + results
        else:
            results = result
        self._results.append(results)
        self._RPC_.response(self)

    def on_result(self, response_text):
        """ Asynchronous callback. """
        self.set_header('Content-Type', self._RPC_.content_type)
        self.finish(response_text)


class FaultMethod(object):
    """
    This is the 'dynamic' fault method so that the message can
    be changed on request from the parser.faults call.
    """
    def __init__(self, fault, code, message):
        self.fault = fault
        self.code = code
        self.message = message

    def __call__(self, message=None):
        if message:
            self.message = message
        return self.fault(self.code, self.message)


class Faults(object):
    """
    This holds the codes and messages for the RPC implementation.
    It is attached (dynamically) to the Parser when called via the
    parser.faults query, and returns a FaultMethod to be called so
    that the message can be changed. If the 'dynamic' attribute is
    not a key in the codes list, then it will error.

    USAGE:
        parser.fault.parse_error('Error parsing content.')

    If no message is passed in, it will check the messages dictionary
    for the same key as the codes dict. Otherwise, it just prettifies
    the code 'key' from the codes dict.

    """
    codes = {
        'parse_error': -32700,
        'method_not_found': -32601,
        'invalid_request': -32600,
        'invalid_params': -32602,
        'internal_error': -32603
    }

    messages = {}

    def __init__(self, parser, fault=None):
        self.library = parser.library
        self.fault = fault
        if not self.fault:
            self.fault = getattr(self.library, 'Fault')

    def __getattr__(self, attr):
        message = 'Error'
        if attr in self.messages.keys():
            message = self.messages[attr]
        else:
            message = ' '.join(map(str.capitalize, attr.split('_')))
        fault = FaultMethod(self.fault, self.codes[attr], message)
        return fault


class JSONRPCParser(BaseRPCParser):

    content_type = 'application/json-rpc'

    def parse_request(self, request_body):
        try:
            request = loads(request_body)
        except:
            # Bad request formatting. Bad.
            self.traceback()
            return self.faults.parse_error()
        self._requests = request
        self._batch = False
        request_list = []
        if isbatch(request):
            self._batch = True
            for req in request:
                req_tuple = (req['method'], req.get('params', []))
                request_list.append(req_tuple)
        else:
            self._requests = [request, ]
            request_list.append(
                (request['method'], request.get('params', []))
            )
        return tuple(request_list)

    def parse_responses(self, responses):
        if isinstance(responses, Fault):
            return dumps(responses)
        if len(responses) != len(self._requests):
            return dumps(self.faults.internal_error())
        response_list = []
        for i in range(0, len(responses)):
            request = self._requests[i]
            response = responses[i]
            if isnotification(request):
                # Even in batches, notifications have no
                # response entry
                continue
            rpcid = request['id']
            version = jsonrpclib.config.version
            if 'jsonrpc' not in request.keys():
                version = 1.0
            try:
                response_json = dumps(
                    response, version=version,
                    rpcid=rpcid, methodresponse=True
                )
            except TypeError:
                return dumps(
                    self.faults.server_error(),
                    rpcid=rpcid, version=version
                )
            response_list.append(response_json)
        if not self._batch:
            # Ensure it wasn't a batch to begin with, then
            # return 1 or 0 responses depending on if it was
            # a notification.
            if len(response_list) < 1:
                return ''
            return response_list[0]
        # Batch, return list
        return '[ %s ]' % ', '.join(response_list)


class JSONRPCLibraryWrapper(object):

    dumps = dumps
    loads = loads
    Fault = Fault


class JSONRPCHandler(BaseRPCHandler):
    """
    Subclass this to add methods -- you can treat them
    just like normal methods, this handles the JSON formatting.
    """
    _RPC_ = JSONRPCParser(JSONRPCLibraryWrapper)
