#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "path", #:ban dau la body, sua lai thanh path
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None

        return method, path, version # Example: "GET / HTTP/1.1" become return(GET, /index.html, HTTP/1.1)
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request) # get method, path and version from first line: GET /test1/ HTTP/1.1
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #

        if not routes == {}:
            self.routes = routes
            self.hook = routes.get((self.method, self.path)) # this will give the destination function ("GET", "/index.html") → home_handler => req.hook = home_handler
            #
            # self.hook manipulation goes here
            # ...
            #

        self.headers = self.prepare_headers(request)
        cookies = self.headers.get('cookie', '')
            #
            #  TODO: implement the cookie function here
            #        by parsing the header            #
        
        #self.prepare_cookies(self.cookies) #format from {"auth=true",...} to {"auth":"true",...}
        self.cookies = {}
        if cookies:
            for pair in cookies.split(';'):
                if '=' in pair:
                    key, value = pair.strip().split('=', 1)
                    self.cookies[key.strip()] = value.strip() #get the value of auth
            self.prepare_cookies(cookies)
        

        
        parts = request.split("\r\n\r\n", 1) #seperate header with body
        if len(parts) > 1:
            body = parts[1]
        self.prepare_body(body,None,None) #now we still not handle multipara?

        return

    def prepare_body(self, data, files, json=None):
        
        """
        Prepares the request body and sets the appropriate Content-Type and Content-Length headers.
        Handles three cases: JSON, form data, and files (multipart).
        """
        if json is not None:
            # Case 1: JSON body (assume already a string or use str())
            self.body = str(json)
            self.headers["Content-Type"] = "application/json"
        elif files is not None:
            # Case 3: Files (multipart/form-data) - placeholder
            boundary = "----WeApRousBoundary"
            self.headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
            self.body = data if data else ""
        elif data is not None:
            # Case 2: Form data or raw
            if isinstance(data, dict):
                # Manual urlencoding: key1=val1&key2=val2
                self.body = "&".join(f"{k}={v}" for k, v in data.items())
                self.headers["Content-Type"] = "application/x-www-form-urlencoded"
            elif isinstance(data, bytes):
                self.body = data
            else:
                self.body = str(data)
                self.headers.setdefault("Content-Type", "text/plain")
        else:
            # No body provided, keep as is (could be set from earlier parsing)
            pass
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        self.prepare_content_length(self.body)
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        if body is not None:
            if isinstance(body, str):
                self.headers["Content-Length"] = str(len(body.encode('utf-8')))
            else:
                self.headers["Content-Length"] = str(len(body))
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
        self.auth = auth
        if auth:
            self.cookies["auth"] = "true"
            self.prepare_cookies("auth=true")
        return

    def prepare_cookies(self, cookies):
            self.headers["Cookie"] = cookies
