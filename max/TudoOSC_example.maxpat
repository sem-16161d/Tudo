{
 "patcher": {
  "fileversion": 1,
  "appversion": {
   "major": 8,
   "minor": 6,
   "revision": 0,
   "architecture": "x64",
   "modernui": 1
  },
  "classnamespace": "box",
  "rect": [
   59.0,
   125.0,
   980.0,
   620.0
  ],
  "bglocked": 0,
  "openinpresentation": 0,
  "default_fontsize": 12.0,
  "default_fontface": 0,
  "default_fontname": "Arial",
  "gridonopen": 1,
  "gridsize": [
   15.0,
   15.0
  ],
  "gridsnaponopen": 1,
  "objectsnaponopen": 1,
  "statusbarvisible": 2,
  "toolbarvisible": 1,
  "lefttoolbarpinned": 0,
  "toptoolbarpinned": 0,
  "righttoolbarpinned": 0,
  "bottomtoolbarpinned": 0,
  "toolbars_unpinned_last_save": 0,
  "tallnewobj": 0,
  "boxanimatetime": 200,
  "enablehscroll": 1,
  "enablevscroll": 1,
  "devicewidth": 0.0,
  "description": "",
  "digest": "",
  "tags": "",
  "style": "",
  "subpatcher_template": "",
  "assistshowspatchername": 0,
  "boxes": [
   {
    "box": {
     "id": "c1",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20,
      10,
      520,
      20.0
     ],
     "text": "Tudo OSC example  -  start tests/tudoServer.py first (ports 7400 / 7401)"
    }
   },
   {
    "box": {
     "id": "c2",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20,
      40,
      420,
      20.0
     ],
     "text": "queries (edit the messages, any t.search / findSimilar condition works):"
    }
   },
   {
    "box": {
     "id": "m0",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      65,
      430,
      22.0
     ],
     "text": "/tudo/ping",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m1",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      93,
      430,
      22.0
     ],
     "text": "/tudo/count tags violin",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m2",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      121,
      430,
      22.0
     ],
     "text": "/tudo/search tags violin durationSec__gt 2 limit 20",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m3",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      149,
      430,
      22.0
     ],
     "text": "/tudo/search tagContains radar random limit 8",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m4",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      177,
      430,
      22.0
     ],
     "text": "/tudo/similar @roughness 1 @mainPitchHz 100 k 10 tags violin",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m5",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      205,
      430,
      22.0
     ],
     "text": "/tudo/similar id 1234 k 10 features timbre",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m6",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      233,
      430,
      22.0
     ],
     "text": "/tudo/render /private/tmp/similar.wav spread 1 align onset play true",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "m7",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      261,
      430,
      22.0
     ],
     "text": "/tudo/columns",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "send",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20,
      299,
      150,
      22.0
     ],
     "text": "udpsend localhost 7400"
    }
   },
   {
    "box": {
     "id": "c3",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      20,
      349,
      420,
      20.0
     ],
     "text": "replies:"
    }
   },
   {
    "box": {
     "id": "recv",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "patching_rect": [
      20,
      374,
      110,
      22.0
     ],
     "text": "udpreceive 7401",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "route",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 9,
     "patching_rect": [
      20,
      414,
      640,
      22.0
     ],
     "text": "route /tudo/clear /tudo/result /tudo/done /tudo/error /tudo/rendered /tudo/count /tudo/pong /tudo/columns",
     "outlettype": [
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      "",
      ""
     ]
    }
   },
   {
    "box": {
     "id": "tclear",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 2,
     "patching_rect": [
      20,
      464,
      50,
      22.0
     ],
     "text": "t b b",
     "outlettype": [
      "bang",
      "bang"
     ]
    }
   },
   {
    "box": {
     "id": "clrmsg",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      20,
      504,
      40,
      22.0
     ],
     "text": "clear",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "clrcoll",
     "maxclass": "message",
     "numinlets": 2,
     "numoutlets": 1,
     "patching_rect": [
      80,
      504,
      40,
      22.0
     ],
     "text": "clear",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "unp",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 5,
     "patching_rect": [
      180,
      464,
      120,
      22.0
     ],
     "text": "unpack 0 0 s 0. 0.",
     "outlettype": [
      "int",
      "int",
      "",
      "float",
      "float"
     ]
    }
   },
   {
    "box": {
     "id": "app",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 1,
     "patching_rect": [
      180,
      504,
      100,
      22.0
     ],
     "text": "prepend append",
     "outlettype": [
      ""
     ]
    }
   },
   {
    "box": {
     "id": "poly",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 2,
     "patching_rect": [
      20,
      554,
      110,
      22.0
     ],
     "text": "polybuffer~ tudo",
     "outlettype": [
      "",
      ""
     ]
    }
   },
   {
    "box": {
     "id": "coll",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 4,
     "patching_rect": [
      180,
      554,
      110,
      22.0
     ],
     "text": "coll tudo_results",
     "outlettype": [
      "",
      "",
      "",
      ""
     ]
    }
   },
   {
    "box": {
     "id": "c4",
     "maxclass": "comment",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      300,
      554,
      380,
      20.0
     ],
     "text": "coll: index -> id path distance durationSec   |   polybuffer~ tudo: the result files"
    }
   },
   {
    "box": {
     "id": "p0",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      320,
      464,
      95,
      22.0
     ],
     "text": "print tudo-done"
    }
   },
   {
    "box": {
     "id": "p1",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      420,
      464,
      95,
      22.0
     ],
     "text": "print tudo-ERROR"
    }
   },
   {
    "box": {
     "id": "p2",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      520,
      464,
      95,
      22.0
     ],
     "text": "print tudo-rendered"
    }
   },
   {
    "box": {
     "id": "p3",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      640,
      464,
      95,
      22.0
     ],
     "text": "print tudo-count"
    }
   },
   {
    "box": {
     "id": "p4",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      740,
      464,
      95,
      22.0
     ],
     "text": "print tudo-pong"
    }
   },
   {
    "box": {
     "id": "p5",
     "maxclass": "newobj",
     "numinlets": 1,
     "numoutlets": 0,
     "patching_rect": [
      840,
      464,
      95,
      22.0
     ],
     "text": "print tudo-columns"
    }
   }
  ],
  "lines": [
   {
    "patchline": {
     "source": [
      "m0",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m1",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m2",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m3",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m4",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m5",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m6",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "m7",
      0
     ],
     "destination": [
      "send",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "recv",
      0
     ],
     "destination": [
      "route",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      0
     ],
     "destination": [
      "tclear",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "tclear",
      0
     ],
     "destination": [
      "clrmsg",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "tclear",
      1
     ],
     "destination": [
      "clrcoll",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      1
     ],
     "destination": [
      "unp",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "unp",
      2
     ],
     "destination": [
      "app",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "clrmsg",
      0
     ],
     "destination": [
      "poly",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "app",
      0
     ],
     "destination": [
      "poly",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      1
     ],
     "destination": [
      "coll",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "clrcoll",
      0
     ],
     "destination": [
      "coll",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      2
     ],
     "destination": [
      "p0",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      3
     ],
     "destination": [
      "p1",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      4
     ],
     "destination": [
      "p2",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      5
     ],
     "destination": [
      "p3",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      6
     ],
     "destination": [
      "p4",
      0
     ]
    }
   },
   {
    "patchline": {
     "source": [
      "route",
      7
     ],
     "destination": [
      "p5",
      0
     ]
    }
   }
  ],
  "dependency_cache": [],
  "autosave": 0
 }
}