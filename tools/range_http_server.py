#!/usr/bin/env python
"""
Static HTTP server with byte-range support for media seeking.
"""
from __future__ import annotations

import argparse
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeRequestHandler(SimpleHTTPRequestHandler):
    _range: tuple[int, int] | None = None

    def send_head(self):
        self._range = None
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        ctype = self.guess_type(path)
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        size = fs.st_size
        start = 0
        end = size - 1

        range_header = self.headers.get("Range")
        if range_header:
            match = re.match(r"bytes=(\d*)-(\d*)$", range_header.strip())
            if match:
                start_text, end_text = match.groups()
                if start_text:
                    start = int(start_text)
                    end = int(end_text) if end_text else end
                elif end_text:
                    # suffix bytes request: bytes=-500
                    suffix_len = int(end_text)
                    start = max(size - suffix_len, 0)
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    f.close()
                    return None
                end = min(end, size - 1)
                self._range = (start, end)
                self.send_response(206)
            else:
                self.send_response(200)
        else:
            self.send_response(200)

        content_length = (end - start + 1) if self._range else size
        self.send_header("Content-type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(content_length))
        if self._range:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()

        if self._range:
            f.seek(start)
        return f

    def copyfile(self, source, outputfile):
        if not self._range:
            return super().copyfile(source, outputfile)

        start, end = self._range
        remaining = end - start + 1
        block_size = 64 * 1024
        while remaining > 0:
            chunk = source.read(min(block_size, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main() -> int:
    parser = argparse.ArgumentParser(description="Static HTTP server with Range support")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--directory", default="web")
    args = parser.parse_args()

    if args.directory:
        os.chdir(args.directory)

    httpd = ThreadingHTTPServer((args.host, args.port), RangeRequestHandler)
    print(f"Serving {os.getcwd()} at http://{args.host}:{args.port}")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
