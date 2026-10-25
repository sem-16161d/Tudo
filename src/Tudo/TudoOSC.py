# TudoOSC.py
"""
OSC front end for Tudo, built on GreasyPidgin's OSCBridge.

Run it next to Ableton Live / Max (tests/tudoServer.py) and query the
database from a Max for Live device with [udpsend] / [udpreceive].

Messages Max is likely to send are plain key/value lists (no JSON, because
commas split messages in Max):

    /tudo/search   tags violin pizzicato  durationSec__gt 2  limit 20
    /tudo/count    tagContains radar
    /tudo/similar  id 1234  k 10  tags violin
    /tudo/similar  path "/Users/.../op 6 4.wav"  k 5
    /tudo/similar  @roughness 1  @mainPitchHz 100  k 10  tagContains violin
    /tudo/render   /private/tmp/similar.wav  spread 1  align onset
    /tudo/columns
    /tudo/ping

Key/value rules
    - a key is a known search key: a column name (optionally with __gt,
      __between, ...), tags / anyTags / noTags / tagContains / anyTagContains /
      noTagContains / pathContains / orderBy / limit / offset / random, or for
      /tudo/similar: id, path, k, features, metric, normalise, pca, @<column>
    - everything up to the next key are its values; several values -> list
      (tags violin pizzicato -> ["violin", "pizzicato"])
    - "@column value" sets a target feature for /tudo/similar
    - features / columns / orderBy take column names as values; a plain
      column filter (dynProfile descending) must not follow them directly
    - instead of key/values, a single JSON string also works (SuperCollider,
      Python): /tudo/search '{"tags": ["violin"], "limit": 20}'

Replies (sent to the out port):
    /tudo/clear   <command>                         before the results
    /tudo/result  <index> <id> <path> <distance> <durationSec>
    /tudo/done    <command> <numResults>
    /tudo/count   <n>
    /tudo/columns <name> <name> ...
    /tudo/rendered <path>
    /tudo/error   <command> <message>
    /tudo/pong

Results are sent one message each, so the UDP packet limit is never hit
and Max can fill a [coll] / [polybuffer~] message by message.
"""

import json
import threading
import traceback

from GreasyPidgin.OSCBridge import OSCBridge

LIST_KEYS = {"tags", "anytags", "notags", "tagcontains", "anytagcontains",
             "notagcontains", "columns", "orderby", "features"}
SEARCH_SPECIAL = {"tags", "anytags", "notags", "tagcontains", "anytagcontains",
                  "notagcontains", "pathcontains", "orderby", "limit", "offset",
                  "random", "columns"}
SIMILAR_OPTIONS = {"id", "path", "k", "features", "metric", "normalise", "pca",
                   "balancevectors", "includetarget"}
COLUMN_VALUE_KEYS = {"features", "columns", "orderby"}
RENDER_OPTIONS = {"align", "spread", "normaliseeach", "peakdb", "maxdurationsec",
                  "sr", "channels", "play"}
OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "between", "in", "isnull"}

# canonical spelling of the special keys (OSC is case-insensitive here)
_CANON = {k.lower(): k for k in [
    "tags", "anyTags", "noTags", "tagContains", "anyTagContains", "noTagContains",
    "pathContains", "orderBy", "limit", "offset", "random", "columns",
    "id", "path", "k", "features", "metric", "normalise", "pca",
    "balanceVectors", "includeTarget", "align", "spread", "normaliseEach",
    "peakDb", "maxDurationSec", "sr", "channels", "play"]}


def _value(v):
    """OSC/Max atoms -> Python values ("true"/"false" -> bool)."""
    if isinstance(v, str):
        low = v.lower()
        if low in ("true", "false"):
            return low == "true"
        if low in ("none", "null"):
            return None
    return v


def parseArgs(args, columns, extraKeys=()):
    """
    Key/value OSC arguments (or one JSON string) -> dict.
    columns   : known column names (lowercase)
    extraKeys : additional option keys for this command (lowercase)
    Returns (conditions, options, target) where target holds "@column" values.
    """
    if len(args) == 1 and isinstance(args[0], str) and args[0].strip().startswith("{"):
        data = json.loads(args[0])
        target = {k[1:]: v for k, v in data.items() if k.startswith("@")}
        if isinstance(data.get("target"), dict):
            target.update(data.pop("target"))
        options = {k: v for k, v in data.items() if k.lower() in extraKeys}
        conditions = {k: v for k, v in data.items()
                      if not k.startswith("@") and k.lower() not in extraKeys and k != "target"}
        return conditions, options, target

    columns = {c.lower() for c in columns}

    def isKey(tok):
        if not isinstance(tok, str):
            return False
        low = tok.lower()
        if low.startswith("@") and len(low) > 1:
            return True
        if low in SEARCH_SPECIAL or low in extraKeys:
            return True
        base, _, op = low.partition("__")
        return base in columns and (not op or op in OPERATORS)

    def isBareColumn(tok):
        return isinstance(tok, str) and tok.lower().lstrip("-") in columns

    pairs, key, vals = [], None, []
    for tok in args:
        # features / columns / orderBy take column names as values
        if key is not None and key.lower() in COLUMN_VALUE_KEYS and isBareColumn(tok):
            vals.append(tok)
        elif isKey(tok):
            if key is not None:
                pairs.append((key, vals))
            key, vals = tok, []
        elif isinstance(tok, str) and "__" in tok and tok.lower().partition("__")[2] in OPERATORS:
            raise ValueError(f"unknown column '{tok.partition('__')[0]}' in '{tok}'")
        elif key is None:
            raise ValueError(f"unexpected value '{tok}' before any key")
        else:
            vals.append(_value(tok))
    if key is not None:
        pairs.append((key, vals))

    conditions, options, target = {}, {}, {}
    for key, vals in pairs:
        low = key.lower()
        if low.startswith("@"):
            target[key[1:]] = vals[0] if len(vals) == 1 else vals
            continue
        if not vals:
            value = True                                  # e.g. "random"
        elif len(vals) == 1 and low not in LIST_KEYS and not low.endswith(("__in",)):
            value = vals[0]
        else:
            value = list(vals)
        if low in ("tags", "anytags", "notags", "tagcontains", "anytagcontains",
                   "notagcontains", "pathcontains") and value is not True:
            value = [str(v) for v in value] if isinstance(value, list) else str(value)
        name = _CANON.get(low, key)
        if low in extraKeys:
            options[name] = value
        else:
            conditions[name] = value
    return conditions, options, target


class TudoOSC:
    """
    tudo   : a connected Tudo instance
    inPort : port Tudo listens on (Max: [udpsend localhost <inPort>])
    outPort: port Tudo answers to   (Max: [udpreceive <outPort>])
    """

    def __init__(self, tudo, inIp="127.0.0.1", inPort=7400,
                 outIp="127.0.0.1", outPort=7401, threaded=False,
                 tableName="soundfile_analysis", verbose=True):
        self.tudo = tudo
        self.tableName = tableName
        self.verbose = verbose
        self.lastResults = []
        # one query at a time: the database connection is not thread-safe
        # and OSCBridge's server handles each message in its own thread
        self._lock = threading.Lock()
        self.bridge = OSCBridge(in_ip=inIp, in_port=inPort,
                                out_ip=outIp, out_port=outPort, threaded=threaded)
        for address, fn in [
            ("/tudo/search", self._search),
            ("/tudo/count", self._count),
            ("/tudo/similar", self._similar),
            ("/tudo/render", self._render),
            ("/tudo/columns", self._columns),
            ("/tudo/ping", lambda *a: self.bridge.send("/tudo/pong")),
        ]:
            self.bridge.handlers.add(address, self._guarded(address, fn), run=True)

    # ------------------------------------------------------------------
    def start(self):
        self.bridge.start()

    def stop(self):
        self.bridge.stop()

    def _log(self, *msg):
        if self.verbose:
            print("TudoOSC:", *msg)

    def _guarded(self, command, fn):
        def handler(address, *args):
            self._log(address, *args)
            with self._lock:
                try:
                    fn(address, *args)
                except Exception as e:
                    self._log("error:", e)
                    if self.verbose:
                        traceback.print_exc()
                    try:
                        self.tudo.conn.rollback()
                    except Exception:
                        pass
                    self.bridge.send("/tudo/error", command, str(e))
        return handler

    def _columnsLower(self):
        return [c.lower() for c in self.tudo.searchColumns(self.tableName)]

    def _sendResults(self, command, rows):
        self.lastResults = rows
        self.bridge.send("/tudo/clear", command)
        for i, r in enumerate(rows):
            self.bridge.send("/tudo/result", i, int(r.get("id", -1)), str(r.get("path", "")),
                             float(r.get("distance", 0.0)),
                             float(r.get("durationsec") or r.get("durationSec") or 0.0))
        self.bridge.send("/tudo/done", command, len(rows))
        self._log(f"{command}: {len(rows)} results")

    # ------------------------------------------------------------------
    def _search(self, address, *args):
        conditions, _, _ = parseArgs(args, self._columnsLower())
        conditions.setdefault("columns", ["id", "path", "durationSec"])
        rows = self.tudo.search(self.tableName, **conditions)
        self._sendResults("search", rows)

    def _count(self, address, *args):
        conditions, _, _ = parseArgs(args, self._columnsLower())
        self.bridge.send("/tudo/count", int(self.tudo.count(self.tableName, **conditions)))

    def _similar(self, address, *args):
        conditions, options, target = parseArgs(args, self._columnsLower(), SIMILAR_OPTIONS)
        if "id" in options:
            tgt = int(options.pop("id"))
        elif "path" in options:
            tgt = str(options.pop("path"))
        elif target:
            tgt = target
        else:
            raise ValueError("similar needs a target: id <n>, path <file> or @column <value>")
        k = int(options.pop("k", 10))
        rows = self.tudo.findSimilar(tgt, k, tableName=self.tableName,
                                     returnColumns=("path", "durationSec"),
                                     **options, **conditions)
        self._sendResults("similar", rows)

    def _render(self, address, *args):
        if not self.lastResults:
            raise ValueError("nothing to render: run /tudo/search or /tudo/similar first")
        outPath, rest = (args[0], args[1:]) if args and isinstance(args[0], str) \
            and not args[0].lower() in RENDER_OPTIONS else ("/private/tmp/tudo_mix.wav", args)
        _, options, _ = parseArgs(rest, [], RENDER_OPTIONS)
        play = bool(options.pop("play", False))
        path = self.tudo.renderMix(self.lastResults, outPath, play=play, **options)
        self.bridge.send("/tudo/rendered", path)

    def _columns(self, address, *args):
        self.bridge.send("/tudo/columns", *self.tudo.searchColumns(self.tableName))
