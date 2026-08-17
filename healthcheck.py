import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("healthcheck_stub")

PID_FILE = os.environ.get("QCLUSTER_PID_FILE", "/tmp/qcluster.pid")
PORT = int(os.environ.get("PORT", 8000))
CHECK_INTERVAL_SECONDS = int(os.environ.get("QCLUSTER_CHECK_INTERVAL", 30))
STARTUP_GRACE_SECONDS = int(os.environ.get("QCLUSTER_STARTUP_GRACE", 20))


def read_qcluster_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def qcluster_is_alive(pid):
    if pid is None:
        return False
    try:
        os.kill(pid, 0)  # signal 0: no-op, just tests whether the pid exists
    except ProcessLookupError:
        return False
    except PermissionError:
        # pid exists but we can't signal it — shouldn't happen in this setup,
        # treat as alive rather than false-triggering a restart
        return True
    return True


def watchdog():
    """If qcluster dies, take this whole service down deliberately so
    Render's crash-restart recovers it. Limping along with a healthy-looking
    stub and no actual worker running is worse than a visible restart."""
    time.sleep(STARTUP_GRACE_SECONDS)  # let qcluster write its pid file on cold start
    while True:
        pid = read_qcluster_pid()
        if not qcluster_is_alive(pid):
            log.error(
                "qcluster (pid=%s) is not running — exiting so Render restarts the service",
                pid,
            )
            os._exit(1)  # hard exit, skip cleanup, force a real container restart
        time.sleep(CHECK_INTERVAL_SECONDS)


class HealthHandler(BaseHTTPRequestHandler):
    def _respond(self, include_body):
        pid = read_qcluster_pid()
        alive = qcluster_is_alive(pid)
        body = b"ok\n" if alive else b"qcluster down\n"
        self.send_response(503 if not alive else 200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def do_GET(self):
        self._respond(include_body=True)

    def do_HEAD(self):
        self._respond(include_body=False)

    def log_message(self, format, *args):
        pass  


if __name__ == "__main__":
    threading.Thread(target=watchdog, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthHandler)
    log.info(
        "healthcheck listening on 0.0.0.0:%s, watching pid file %s",
        PORT,
        PID_FILE,
    )
    server.serve_forever()
