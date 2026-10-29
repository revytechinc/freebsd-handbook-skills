#!/usr/bin/env python3
"""Reach a vmm guest's serial console over a one-use websocket grant.

The new lab's guests are handed out a console by an https URL such as
"https://<addr>/console/<ticket>", valid 60 s. It is opened as a plain RFC
6455 websocket: binary frames carry the console's bytes both ways and text
frames are control messages (printed to stderr, never to stdout).

This program is the stdlib-only bridge. Given a command that prints the grant
URL and the CA PEM file, it opens the websocket and relays:

  * bytes from its stdin  -> masked binary frames
  * binary frames from the server -> its stdout, unbuffered
  * text frames           -> its stderr
  * ping  -> pong
  * close / EOF on stdin -> send close, exit 0

Only the standard library is used; select() drives stdin and the socket so no
threads are needed. The server certificate is checked against the CA we hold
and against the grant's address, which the masters' certificates carry as an IP
SAN.

Usage:
    vmm_console.py --grant-cmd 'CMD...'
"""
import argparse
import base64
import hashlib
import os
import select
import shlex
import socket
import ssl
import subprocess
import sys
from urllib.parse import urlsplit

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# WebSocket opcodes we care about.
OP_CONT = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
CLOSE_WAIT = 10  # seconds to wait for the server's close after ours
OP_PING = 0x9
OP_PONG = 0xA

HTTP_TIMEOUT = 10.0  # seconds the handshake and grant command are allowed
MAX_HEADERS = 64 * 1024  # bytes of upgrade response headers accepted
MAX_FRAME = 1 << 20  # bytes in one frame from the (untrusted) server


def die(msg):
    """Write a message and exit non-zero; the MCP wrapper reports the error."""
    sys.stderr.write(f"vmm_console: {msg}\n")
    sys.exit(2)


def parse_args():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--grant-cmd", required=True,
                   help="command that prints the grant URL then the CA PEM path")
    return p.parse_args()


def validate_url(url):
    """Refuse anything that is not an https URL with a /console/ path, before
    a connection is attempted (so a bad URL costs no server round-trip).
    Spaces and control characters are refused too: the path goes into the
    request line, where a CR or LF would split the HTTP request."""
    if any(c.isspace() or ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        die("grant URL contains a space or control character")
    u = urlsplit(url)
    if not u.hostname:
        die(f"grant URL has no host: {url!r}")
    if u.scheme != "https":
        die(f"grant URL must be https, got {u.scheme!r}")
    if not u.path.startswith("/console/"):
        die(f"grant URL path must start with /console/, got {u.path!r}")


def two_lines(cmd):
    """Run the grant command and return (url, ca_pem_path). Exactly two lines
    are required: the URL, then the CA path."""
    try:
        out = subprocess.check_output(cmd, timeout=HTTP_TIMEOUT, text=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as e:
        die(f"grant command failed: {e}")
    lines = out.splitlines()
    if len(lines) < 2:
        die(f"grant command must print the URL then the CA path, got {len(lines)} line(s)")
    return lines[0].strip(), lines[1].strip()


# --- RFC 6455 framing -------------------------------------------------------

def build_frame(opcode, payload):
    """Build one (possibly masked) WebSocket frame to send to the server."""
    mask = os.urandom(4)
    length = len(payload)
    if length < 126:
        head = bytes([0x80 | opcode, 0x80 | length])
    elif length < 65536:
        head = bytes([0x80 | opcode, 0x80 | 126]) + length.to_bytes(2, "big")
    else:
        head = bytes([0x80 | opcode, 0x80 | 127]) + length.to_bytes(8, "big")
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return head + mask + masked


def _fill(sock, buf, n):
    """Read from sock until buf holds at least n bytes; None if it closes first."""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _header(sock, buf):
    """Parse a frame header from buf (reading more as needed). Return
    (buf, opcode, mask, payload_start, payload_end), or None if it closed."""
    buf = _fill(sock, buf, 2)
    if buf is None:
        return None
    length, i = buf[1] & 0x7F, 2
    if length in (126, 127):
        width = 2 if length == 126 else 8
        buf = _fill(sock, buf, 2 + width)
        if buf is None:
            return None
        length, i = int.from_bytes(buf[2:2 + width], "big"), 2 + width
    if length > MAX_FRAME:
        raise ValueError(f"a frame of {length} bytes is over the {MAX_FRAME} limit")
    mask = b""
    if buf[1] & 0x80:
        buf = _fill(sock, buf, i + 4)
        if buf is None:
            return None
        mask, i = buf[i:i + 4], i + 4
    return buf, buf[0] & 0x0F, mask, i, i + length


def read_frame(sock, buf=b""):
    """Return (opcode, payload, leftover) for the next complete frame, parsing
    from ``buf`` first and reading more from ``sock`` only when ``buf`` is not
    yet a full frame; ``leftover`` holds any bytes left after that frame.
    Return (None, None, leftover) if the connection closed before a full frame
    arrived. Single (FIN) frames only, which is what this lab's console sends.

    Driving it from a buffer is what keeps the bytes that arrived with the
    upgrade headers: the client parses those first, the server drives from the
    socket with an empty buffer."""
    head = _header(sock, buf)
    if head is None:
        return None, None, buf
    buf, opcode, mask, start, end = head
    buf = _fill(sock, buf, end)
    if buf is None:
        return None, None, b""
    payload = buf[start:end]
    if mask:
        payload = bytes(b ^ mask[k % 4] for k, b in enumerate(payload))
    return opcode, payload, buf[end:]


# --- Handshake --------------------------------------------------------------

def read_http(sock):
    """Read the HTTP response headers for the upgrade. Return
    (status, response_text, leftover): ``leftover`` holds any bytes that
    arrived after the blank line. The first websocket frame often comes in the
    same read as the headers, so those bytes must be kept for the client to
    parse rather than discarded."""
    data = b""
    while b"\r\n\r\n" not in data:
        if len(data) > MAX_HEADERS:
            die(f"the websocket handshake response is over {MAX_HEADERS} bytes")
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    if not data:
        die("empty response to the websocket handshake")
    fields = data.split(b"\r\n", 1)[0].split(b" ")
    if len(fields) < 2 or not fields[1].isdigit():
        die("malformed response to the websocket handshake")
    status = int(fields[1])
    response = data.decode("latin-1", "replace")
    marker = data.find(b"\r\n\r\n")
    leftover = data[marker + 4:] if marker != -1 else b""
    return status, response, leftover


def open_websocket(url, ca_path):
    """Open the TLS websocket. The certificate is verified against the CA we
    hold, but the certificate is checked against the grant's address (an IP SAN).

    The real server is TLS from the first byte, so the socket is wrapped BEFORE
    the upgrade request is sent (not after): the handshake is exchanged over the
    TLS connection. The returned pair is the socket and ``leftover`` -- any bytes
    that arrived with the 101 response, which the relay parses as the first
    frame(s)."""
    u = urlsplit(url)
    host, port = u.hostname, u.port or 443
    raw = socket.create_connection((host, port), timeout=HTTP_TIMEOUT)
    ctx = ssl.create_default_context(cafile=ca_path)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    # Full verification: the masters' certificates carry their address as an
    # IP SAN, so the grant's host (an IP) is checked against the certificate.
    key = base64.b64encode(os.urandom(16)).decode()
    request = ("GET {p} HTTP/1.1\r\n"
               "Host: {h}:{port}\r\n"
               "Upgrade: websocket\r\n"
               "Connection: Upgrade\r\n"
               "Sec-WebSocket-Key: {k}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n").format(p=u.path + ("?" + u.query if u.query else ""), h=host, port=port, k=key)
    sock = ctx.wrap_socket(raw, server_hostname=host)
    sock.sendall(request.encode())
    status, response, leftover = read_http(sock)
    if status != 101:
        die(f"websocket upgrade refused (HTTP {status}); only 101 is accepted")
    # RFC 6455 fixes SHA-1 for Sec-WebSocket-Accept; it is not used for security.
    digest = hashlib.sha1((key + GUID).encode(), usedforsecurity=False).digest()  # nosec B324 -- RFC 6455 accept value, not security # nosemgrep: home.mlapointe..config.scan-tools.rules.semgrep.python.lang.security.insecure-hash-algorithms.insecure-hash-algorithm-sha1 -- RFC 6455 accept value # NOSONAR -- RFC 6455 accept value
    expected = base64.b64encode(digest).decode()
    if not _accept_ok(response, expected):
        die("websocket upgrade: bad Sec-WebSocket-Accept")
    # The connect timeout is for the handshake only. relay() reads only after
    # select() reports data, so a quiet console never times out a recv; this
    # also keeps a large sendall from timing out mid-write.
    sock.settimeout(None)
    return sock, leftover


def _accept_ok(response, expected):
    for line in response.split("\r\n"):
        if line[:21].lower() == "sec-websocket-accept:":
            return line.split(":", 1)[1].strip() == expected
    return False


# --- Main loop --------------------------------------------------------------

def _ready(sock, inputs):
    """What can be read now. Bytes TLS has already decrypted are invisible to
    select(), so do not block while any are waiting. After our close (stdin no
    longer in inputs) wait at most CLOSE_WAIT for the server's own close."""
    if sock.pending():
        return [sock]
    timeout = None if 0 in inputs else CLOSE_WAIT
    readable, _, _ = select.select(inputs, [], [], timeout)
    return readable


def _from_stdin(sock):
    """Send what stdin has as one binary frame; on EOF send our close and
    return False (stop reading stdin), else True."""
    data = os.read(0, 4096)
    if not data:
        sock.sendall(build_frame(OP_CLOSE, b""))
        return False
    sock.sendall(build_frame(OP_BINARY, data))
    return True


def _recv(sock):
    """Bytes from the TLS socket, or b"" when it closed or failed."""
    try:
        return sock.recv(65536)
    except OSError:  # ssl.SSLError is an OSError
        return b""


def _drain(sock, buf):
    """Handle every complete frame in buf. Return (rest, closed)."""
    while buf:
        opcode, payload, buf = read_frame(sock, buf)
        if opcode is None or opcode == OP_CLOSE:
            return buf, True
        if opcode == OP_PING:
            sock.sendall(build_frame(OP_PONG, payload))
        elif opcode == OP_BINARY:
            os.write(1, payload)
        elif opcode == OP_TEXT:
            sys.stderr.write(payload.decode("utf-8", "replace"))
    return buf, False


def relay(sock, leftover=b""):
    """Drive the relay: stdin -> frames, server frames -> stdout. ``leftover``
    holds the bytes the server sent with the upgrade headers and is parsed
    first. On EOF from stdin our close is sent and reading continues until the
    server's close (or CLOSE_WAIT passes), so nothing it already sent is lost."""
    buf, closed = _drain(sock, leftover)
    inputs = [sock, 0]
    while not closed:
        readable = _ready(sock, inputs)
        if not readable:
            return  # we sent close and the server never answered in time
        if 0 in readable and not _from_stdin(sock):
            inputs = [sock]
        if sock in readable:
            chunk = _recv(sock)
            if not chunk:
                return  # the TLS connection closed
            buf, closed = _drain(sock, buf + chunk)


def main():
    cmd = shlex.split(parse_args().grant_cmd)
    url, ca_path = two_lines(cmd)
    validate_url(url)
    sock, leftover = open_websocket(url, ca_path)
    try:
        relay(sock, leftover)
    except ValueError as exc:
        die(str(exc))
    finally:
        sock.close()
    sys.exit(0)


if __name__ == "__main__":
    main()