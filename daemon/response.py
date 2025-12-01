#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#

"""
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings.
"""
import datetime
import os
import mimetypes
import json
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object."""

    __attrs__ = [
        "_content", "_header", "status_code", "method", "headers",
        "url", "history", "encoding", "reason", "cookies", "elapsed",
        "request", "body",
    ]

    def __init__(self, request=None):
        self._content = False
        self._content_consumed = False
        self._next = None
        self.status_code = None
        self.headers = {}
        self.url = None
        self.encoding = None
        self.history = []
        self.reason = None
        self.cookies = CaseInsensitiveDict()
        self.elapsed = datetime.timedelta(0)
        self.request = None

    def get_mime_type(self, path):
        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'

    def prepare_content_type(self, mime_type='text/html'):
        base_dir = ""
        main_type, sub_type = mime_type.split('/', 1)
        
        # Default header set (can be overwritten later)
        self.headers['Content-Type'] = mime_type

        if main_type == 'text':
            if sub_type in ['plain', 'css', 'csv', 'xml']:
                base_dir = BASE_DIR + "static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR + "www/"
            else:
                base_dir = BASE_DIR + "static/"
        elif main_type == 'image':
            base_dir = BASE_DIR + "static/"
        elif main_type == 'application':
            base_dir = BASE_DIR + "apps/"
        elif main_type == 'video':
            base_dir = BASE_DIR + "video/"
        else:
            # Fallback for unknown types
            base_dir = BASE_DIR + "static/"

        return base_dir

    def build_content(self, path, base_dir):
        """Loads the object file from storage."""
        
        # Robust path joining
        filepath = os.path.join(base_dir, path.lstrip('/'))
        print(f"[Response] Serving object at: {filepath}")

        try:
            with open(filepath, "rb") as f:
                content = f.read()
            
            # Legacy support: Clear return.json if used
            if path.endswith("return.json"):
                with open(filepath, "w") as f:
                    f.write("")
            
            return len(content), content
        except FileNotFoundError:
            print(f"[Response] File not found: {filepath}")
            return 0, b""
        except Exception as e:
            print(f"[Response] Error reading file {filepath}: {e}")
            return 0, b""

    def build_response_header(self, request):
        reqhdr = request.headers
        
        # Ensure Content-Type/Length exist to prevent KeyErrors
        c_type = self.headers.get('Content-Type', 'application/octet-stream')
        c_len = self.headers.get('Content-Length', '0')

        headers = {
            "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
            "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
            "Cache-Control": "no-cache",
            "Content-Type": c_type,
            "Content-Length": c_len,
            "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
            "Server": "WeApRous/1.0",
            "Connection": "close"
        }

        # Handle Status Line
        # If reason is still a dict/list here, force it to string to prevent protocol errors
        if isinstance(self.reason, (dict, list)):
            display_reason = "OK" 
        else:
            display_reason = self.reason if self.reason else "OK"

        status_line = f"HTTP/1.1 {self.status_code} {display_reason}\r\n"

        # Handle Cookies
        if self.cookies:
            headers["Set-Cookie"] = [f"{k}={v}" for k, v in self.cookies.items()]

        header_lines = ""
        for k, v in headers.items():
            if isinstance(v, list):
                for item in v:
                    header_lines += f"{k}: {item}\r\n"
            else:
                header_lines += f"{k}: {v}\r\n"

        fmt_header = status_line + header_lines + "\r\n"
        return fmt_header.encode("utf-8")

    def build_notfound(self):
        return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode('utf-8')

    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.
        """
        
        # ---------------------------------------------------------
        # 1. Handle Dynamic Data (JSON from Route Handlers)
        # ---------------------------------------------------------
        # If backend.py put data in self.reason, we turn it into JSON body here.
        if isinstance(self.reason, (dict, list)):
            json_bytes = json.dumps(self.reason).encode('utf-8')
            
            self._content = json_bytes
            self.status_code = 200 if self.status_code is None else self.status_code
            
            # Important: Reset reason so it doesn't break the HTTP Header
            self.reason = "OK" 
            
            # Set headers explicitly
            self.headers['Content-Type'] = 'application/json'
            self.headers['Content-Length'] = len(self._content)
            
            self._header = self.build_response_header(request)
            return self._header + self._content

        # ---------------------------------------------------------
        # 2. Handle File-Based Paths
        # ---------------------------------------------------------
        path = request.path
        mime_type = self.get_mime_type(path)
        base_dir = None

        # -- SMART PATH FINDING --
        # This finds the 'db' folder relative to THIS file (response.py)
        # So it works even if you run python from a different folder.
        current_dir = os.path.dirname(os.path.abspath(__file__)) # .../daemon
        project_root = os.path.dirname(current_dir)              # .../ (Root)

        # Map API paths to DB files
        if path == '/api/get-messages' or path == '/api/get-message':
             path = 'db/message.json'
             mime_type = 'application/json'
             base_dir = project_root
        elif path == '/api/get-users':
             path = 'db/user.json'
             mime_type = 'application/json'
             base_dir = project_root
        
        # ---------------------------------------------------------
        # 3. Handle Static Files (Fallback)
        # ---------------------------------------------------------
        if base_dir is None:
            # If unknown type, treat as JSON or Octet Stream
            if mime_type == 'application/octet-stream':
                 mime_type = 'application/json'
            
            try:
                base_dir = self.prepare_content_type(mime_type)
                # If prepare_content_type returns a relative path (e.g. "static/"),
                # we must prepend project_root to ensure it finds it.
                if not os.path.isabs(base_dir):
                    base_dir = os.path.join(project_root, base_dir)
            except Exception as e:
                print(f"[Response] Error preparing content type: {e}")
                return self.build_notfound()

        print(f"[Response] {request.method} {path} | Type: {mime_type}")

        # ---------------------------------------------------------
        # 4. Read Content and Build Response
        # ---------------------------------------------------------
        c_len, self._content = self.build_content(path, base_dir)

        # Save headers so build_response_header can find them
        self.headers['Content-Type'] = mime_type
        self.headers['Content-Length'] = c_len

        if self.status_code is None:
            self.status_code = 200
            self.reason = "OK"

        self._header = self.build_response_header(request)
        return self._header + self._content

    def build_unauthorized(self):
        body = "401 Unauthorized"
        return (
            "HTTP/1.1 401 Unauthorized\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{body}"
        ).encode("utf-8")