import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from bones_bullets import server


@pytest.fixture(scope="module")
def base_url():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def call(base, path, body=None, token=""):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json", "X-Game": token})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_serves_index(base_url):
    with urllib.request.urlopen(base_url + "/") as r:
        assert r.status == 200 and b"Bones" in r.read()


def test_new_game_with_seed_is_reproducible(base_url):
    _, a = call(base_url, "/api/new", {"seed": 7})
    _, b = call(base_url, "/api/new", {"seed": 7})
    assert a["state"]["dice"] == b["state"]["dice"]
    assert a["token"] != b["token"]


def test_lock_fire_play_flow(base_url):
    _, r = call(base_url, "/api/new", {"seed": 1})
    tok = r["token"]
    st, r = call(base_url, "/api/lock", {"index": 0}, tok)
    assert st == 200 and r["state"]["dice"][0]["locked"] is True
    st, r = call(base_url, "/api/fire", {}, tok)
    assert st == 200 and r["event"]["chamber"] in ("EMPTY", "LIVE")
    st, r = call(base_url, "/api/play", {}, tok)
    assert st == 200 and "played" in r["event"]
    assert r["state"]["hands_left"] <= 2


def test_unknown_token_and_bad_upgrade(base_url):
    st, r = call(base_url, "/api/fire", {}, "nope")
    assert st == 404
    _, r = call(base_url, "/api/new", {"seed": 1})
    st, r = call(base_url, "/api/upgrade", {"id": "SHIELD"}, r["token"])
    assert st == 400 and "error" in r["event"]
