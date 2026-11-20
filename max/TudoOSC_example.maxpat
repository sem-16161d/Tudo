{
	"patcher" : 	{
		"fileversion" : 1,
		"appversion" : 		{
			"major" : 8,
			"minor" : 6,
			"revision" : 0,
			"architecture" : "x64",
			"modernui" : 1
		}
,
		"classnamespace" : "box",
		"rect" : [ 59.0, 125.0, 1294.0, 1010.0 ],
		"bglocked" : 0,
		"openinpresentation" : 0,
		"default_fontsize" : 12.0,
		"default_fontface" : 0,
		"default_fontname" : "Arial",
		"gridonopen" : 1,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 1,
		"objectsnaponopen" : 1,
		"statusbarvisible" : 2,
		"toolbarvisible" : 1,
		"lefttoolbarpinned" : 0,
		"toptoolbarpinned" : 0,
		"righttoolbarpinned" : 0,
		"bottomtoolbarpinned" : 0,
		"toolbars_unpinned_last_save" : 0,
		"tallnewobj" : 0,
		"boxanimatetime" : 200,
		"enablehscroll" : 1,
		"enablevscroll" : 1,
		"devicewidth" : 0.0,
		"description" : "",
		"digest" : "",
		"tags" : "",
		"style" : "",
		"subpatcher_template" : "",
		"assistshowspatchername" : 0,
		"boxes" : [ 			{
				"box" : 				{
					"id" : "obj-17",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 0,
					"patching_rect" : [ 89.0, 884.0, 100.0, 22.0 ],
					"text" : "dac~"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-16",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "int" ],
					"patching_rect" : [ 90.654204905033112, 661.682237863540649, 100.0, 22.0 ],
					"text" : "t b i"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-15",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 24.299065232276917, 715.845788896083832, 50.0, 22.0 ],
					"text" : "start"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-9",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 89.0, 753.271022200584412, 100.0, 22.0 ],
					"text" : "prepend set"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-8",
					"linecount" : 2,
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 89.0, 709.345788896083832, 100.0, 35.0 ],
					"text" : "sprintf symout tudo.%ld"
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-7",
					"maxclass" : "number",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 89.0, 612.0, 50.0, 22.0 ]
				}

			}
, 			{
				"box" : 				{
					"id" : "obj-1",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "signal", "bang" ],
					"patching_rect" : [ 89.0, 828.037376761436462, 100.0, 22.0 ],
					"text" : "play~"
				}

			}
, 			{
				"box" : 				{
					"id" : "c1",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 10.0, 520.0, 20.0 ],
					"text" : "Tudo OSC example  -  start tests/tudoServer.py first (ports 7400 / 7401)"
				}

			}
, 			{
				"box" : 				{
					"id" : "c2",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 40.0, 420.0, 20.0 ],
					"text" : "queries (edit the messages, any t.search / findSimilar condition works):"
				}

			}
, 			{
				"box" : 				{
					"id" : "m0",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 65.0, 430.0, 22.0 ],
					"text" : "/tudo/ping"
				}

			}
, 			{
				"box" : 				{
					"id" : "m1",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 93.0, 430.0, 22.0 ],
					"text" : "/tudo/count tags violin"
				}

			}
, 			{
				"box" : 				{
					"id" : "m2",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 121.0, 430.0, 22.0 ],
					"text" : "/tudo/search tags violin durationSec__gt 2 limit 20"
				}

			}
, 			{
				"box" : 				{
					"id" : "m3",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 149.0, 430.0, 22.0 ],
					"text" : "/tudo/search tagContains radar random limit 8"
				}

			}
, 			{
				"box" : 				{
					"id" : "m4",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 177.0, 430.0, 22.0 ],
					"text" : "/tudo/similar @roughness 0 @mainPitchHz 1000 k 100 tags ordinario"
				}

			}
, 			{
				"box" : 				{
					"id" : "m5",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 205.0, 430.0, 22.0 ],
					"text" : "/tudo/similar id 1234 k 10 features timbre"
				}

			}
, 			{
				"box" : 				{
					"id" : "m6",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 233.0, 430.0, 22.0 ],
					"text" : "/tudo/render /private/tmp/similar.wav spread 1 align onset play false"
				}

			}
, 			{
				"box" : 				{
					"id" : "m7",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 261.0, 430.0, 22.0 ],
					"text" : "/tudo/columns"
				}

			}
, 			{
				"box" : 				{
					"id" : "send",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 299.0, 150.0, 22.0 ],
					"text" : "udpsend localhost 7400"
				}

			}
, 			{
				"box" : 				{
					"id" : "c3",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 20.0, 349.0, 420.0, 20.0 ],
					"text" : "replies:"
				}

			}
, 			{
				"box" : 				{
					"id" : "recv",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 374.0, 110.0, 22.0 ],
					"text" : "udpreceive 7401"
				}

			}
, 			{
				"box" : 				{
					"id" : "route",
					"maxclass" : "newobj",
					"numinlets" : 9,
					"numoutlets" : 9,
					"outlettype" : [ "", "", "", "", "", "", "", "", "" ],
					"patching_rect" : [ 20.0, 414.0, 640.0, 22.0 ],
					"text" : "route /tudo/clear /tudo/result /tudo/done /tudo/error /tudo/rendered /tudo/count /tudo/pong /tudo/columns"
				}

			}
, 			{
				"box" : 				{
					"id" : "tclear",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "bang" ],
					"patching_rect" : [ 20.0, 464.0, 50.0, 22.0 ],
					"text" : "t b b"
				}

			}
, 			{
				"box" : 				{
					"id" : "clrmsg",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 20.0, 504.0, 40.0, 22.0 ],
					"text" : "clear"
				}

			}
, 			{
				"box" : 				{
					"id" : "clrcoll",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 80.0, 504.0, 40.0, 22.0 ],
					"text" : "clear"
				}

			}
, 			{
				"box" : 				{
					"id" : "unp",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 5,
					"outlettype" : [ "int", "int", "", "float", "float" ],
					"patching_rect" : [ 180.0, 464.0, 120.0, 22.0 ],
					"text" : "unpack 0 0 s 0. 0."
				}

			}
, 			{
				"box" : 				{
					"id" : "app",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 180.0, 504.0, 100.0, 22.0 ],
					"text" : "prepend append"
				}

			}
, 			{
				"box" : 				{
					"id" : "poly",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 2,
					"outlettype" : [ "", "bang" ],
					"patching_rect" : [ 20.0, 554.0, 110.0, 22.0 ],
					"saved_object_attributes" : 					{
						"embed" : 0
					}
,
					"text" : "polybuffer~ tudo"
				}

			}
, 			{
				"box" : 				{
					"id" : "coll",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 4,
					"outlettype" : [ "", "", "", "" ],
					"patching_rect" : [ 180.0, 554.0, 110.0, 22.0 ],
					"saved_object_attributes" : 					{
						"embed" : 0,
						"precision" : 6
					}
,
					"text" : "coll tudo_results"
				}

			}
, 			{
				"box" : 				{
					"id" : "c4",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 300.0, 554.0, 421.0, 20.0 ],
					"text" : "coll: index -> id path distance durationSec   |   polybuffer~ tudo: the result files"
				}

			}
, 			{
				"box" : 				{
					"id" : "p0",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 320.0, 464.0, 95.0, 22.0 ],
					"text" : "print tudo-done"
				}

			}
, 			{
				"box" : 				{
					"id" : "p1",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 420.0, 464.0, 106.0, 22.0 ],
					"text" : "print tudo-ERROR"
				}

			}
, 			{
				"box" : 				{
					"id" : "p2",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 520.0, 464.0, 111.0, 22.0 ],
					"text" : "print tudo-rendered"
				}

			}
, 			{
				"box" : 				{
					"id" : "p3",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 640.0, 464.0, 95.0, 22.0 ],
					"text" : "print tudo-count"
				}

			}
, 			{
				"box" : 				{
					"id" : "p4",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 740.0, 464.0, 95.0, 22.0 ],
					"text" : "print tudo-pong"
				}

			}
, 			{
				"box" : 				{
					"id" : "p5",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 840.0, 464.0, 107.0, 22.0 ],
					"text" : "print tudo-columns"
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"destination" : [ "poly", 0 ],
					"source" : [ "app", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "coll", 0 ],
					"source" : [ "clrcoll", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "poly", 0 ],
					"source" : [ "clrmsg", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m0", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m1", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m2", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m3", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m4", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m5", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m6", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "send", 0 ],
					"source" : [ "m7", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-17", 1 ],
					"order" : 0,
					"source" : [ "obj-1", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-17", 0 ],
					"order" : 1,
					"source" : [ "obj-1", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-1", 0 ],
					"source" : [ "obj-15", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-15", 0 ],
					"source" : [ "obj-16", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-8", 0 ],
					"source" : [ "obj-16", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-16", 0 ],
					"source" : [ "obj-7", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-9", 0 ],
					"source" : [ "obj-8", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "obj-1", 0 ],
					"source" : [ "obj-9", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "route", 0 ],
					"source" : [ "recv", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "coll", 0 ],
					"order" : 0,
					"source" : [ "route", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "p0", 0 ],
					"source" : [ "route", 2 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "p1", 0 ],
					"source" : [ "route", 3 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "p2", 0 ],
					"source" : [ "route", 4 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "p3", 0 ],
					"source" : [ "route", 5 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "p4", 0 ],
					"source" : [ "route", 6 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "p5", 0 ],
					"source" : [ "route", 7 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "tclear", 0 ],
					"source" : [ "route", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "unp", 0 ],
					"order" : 1,
					"source" : [ "route", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "clrcoll", 0 ],
					"source" : [ "tclear", 1 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "clrmsg", 0 ],
					"source" : [ "tclear", 0 ]
				}

			}
, 			{
				"patchline" : 				{
					"destination" : [ "app", 0 ],
					"source" : [ "unp", 2 ]
				}

			}
 ],
		"dependency_cache" : [  ],
		"autosave" : 0
	}

}
