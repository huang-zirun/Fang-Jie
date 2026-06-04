// xhs_main_world.js - Intent Money Extension: Xiaohongshu Main World Script
// Runs in the page's main world context (NOT isolated content script world)
// Manifest V3: injected via content_scripts with "world": "MAIN"

(function () {
  "use strict";

  var SOURCE = "intent-money-xhs";
  var CONTENT_SOURCE = "intent-money-xhs-content";
  var XHS_API_BASE = "edith.xiaohongshu.com/api/sns/web/";

  // ==================== Utility Functions ====================

  // Parse formatted numbers like "1.2万" -> 12000, "3.5亿" -> 350000000
  function parseFormattedNumber(text) {
    if (!text && text !== 0) return 0;
    text = String(text).trim();
    if (!text) return 0;
    if (text.includes("亿")) {
      return Math.round(parseFloat(text.replace("亿", "")) * 100000000);
    }
    if (text.includes("万")) {
      return Math.round(parseFloat(text.replace("万", "")) * 10000);
    }
    return parseInt(text.replace(/[^\d.-]/g, ""), 10) || 0;
  }

  // Safe nested property access
  function getNestedValue(obj) {
    var paths = Array.prototype.slice.call(arguments, 1);
    for (var i = 0; i < paths.length; i++) {
      if (obj == null) return undefined;
      obj = obj[paths[i]];
    }
    return obj;
  }

  // Send message to content script / other listeners
  function sendMessage(type, data, requestId) {
    window.postMessage(
      {
        source: SOURCE,
        type: type,
        requestId: requestId || Date.now().toString(),
        data: data,
      },
      "*"
    );
  }

  // ==================== SSR Data Extraction ====================

  function extractSSRData() {
    try {
      var initProps = window.__INIT_PROPS__;
      if (!initProps) {
        return null;
      }
      return initProps;
    } catch (e) {
      console.warn("[Intent Money XHS] Failed to extract SSR data:", e);
      return null;
    }
  }

  // Parse search results from SSR data
  function parseSearchResultsFromSSR(ssrData) {
    var items = [];

    if (!ssrData) return items;

    // Try various paths where search results might be stored
    var candidates = [
      getNestedValue(ssrData, "search", "notes"),
      getNestedValue(ssrData, "search", "data"),
      getNestedValue(ssrData, "search", "items"),
      getNestedValue(ssrData, "search", "list"),
      getNestedValue(ssrData, "pageProps", "search", "notes"),
      getNestedValue(ssrData, "initialState", "search", "notes"),
    ];

    for (var i = 0; i < candidates.length; i++) {
      if (Array.isArray(candidates[i])) {
        items = candidates[i];
        break;
      }
      if (candidates[i] && Array.isArray(candidates[i].notes)) {
        items = candidates[i].notes;
        break;
      }
      if (candidates[i] && Array.isArray(candidates[i].items)) {
        items = candidates[i].items;
        break;
      }
      if (candidates[i] && Array.isArray(candidates[i].data)) {
        items = candidates[i].data;
        break;
      }
    }

    return items.map(function (item) {
      var note = item.note_card || item.noteCard || item;
      var user = note.user || note.author || {};
      var interact = note.interact_info || note.interactInfo || {};

      return {
        note_id: note.note_id || note.noteId || note.id || "",
        title: note.title || note.display_title || "",
        desc: note.desc || note.description || "",
        type: note.type || "",
        author: {
          user_id: user.user_id || user.userId || user.uid || "",
          nickname: user.nickname || user.nick_name || "",
          avatar: user.avatar || user.image || "",
        },
        statistics: {
          liked_count:
            parseFormattedNumber(interact.liked_count) ||
            note.liked_count ||
            0,
          collected_count:
            parseFormattedNumber(interact.collected_count) ||
            note.collected_count ||
            0,
          comment_count:
            parseFormattedNumber(interact.comment_count) ||
            note.comment_count ||
            0,
          share_count:
            parseFormattedNumber(interact.share_count) ||
            note.share_count ||
            0,
        },
        cover: note.cover || note.image_list || "",
        tags: (note.tag_list || note.tags || []).map(function (t) {
          return t.name || t.tag_name || "";
        }).filter(Boolean),
        xsec_token: note.xsec_token || "",
      };
    }).filter(function (n) {
      return n.note_id;
    });
  }

  // Parse note detail from SSR data
  function parseNoteDetailFromSSR(ssrData) {
    if (!ssrData) return null;

    // Try noteDetailMap path
    var detailMap = getNestedValue(ssrData, "noteDetailMap") ||
      getNestedValue(ssrData, "note", "noteDetailMap");

    if (detailMap) {
      // detailMap is an object keyed by note_id
      var keys = Object.keys(detailMap);
      for (var i = 0; i < keys.length; i++) {
        var detail = detailMap[keys[i]];
        if (detail && detail.note) {
          return parseSingleNoteDetail(detail.note);
        }
      }
    }

    // Try direct note path
    var note = getNestedValue(ssrData, "note") ||
      getNestedValue(ssrData, "noteDetail");
    if (note) {
      return parseSingleNoteDetail(note);
    }

    return null;
  }

  function parseSingleNoteDetail(note) {
    var user = note.user || {};
    var interact = note.interact_info || note.interactInfo || {};

    return {
      note_id: note.note_id || note.noteId || note.id || "",
      title: note.title || "",
      desc: note.desc || note.description || "",
      type: note.type || "",
      author: {
        user_id: user.user_id || user.userId || user.uid || "",
        nickname: user.nickname || user.nick_name || "",
        avatar: user.avatar || user.image || "",
      },
      statistics: {
        liked_count:
          parseFormattedNumber(interact.liked_count) || note.liked_count || 0,
        collected_count:
          parseFormattedNumber(interact.collected_count) ||
          note.collected_count ||
          0,
        comment_count:
          parseFormattedNumber(interact.comment_count) ||
          note.comment_count ||
          0,
        share_count:
          parseFormattedNumber(interact.share_count) || note.share_count || 0,
      },
      image_list: note.image_list || note.images || [],
      video: note.video || null,
      tags: (note.tag_list || note.tags || []).map(function (t) {
        return {
          id: t.id || t.tag_id || "",
          name: t.name || t.tag_name || "",
          type: t.type || "",
        };
      }),
      time: note.time || note.last_update_time || 0,
      xsec_token: note.xsec_token || "",
    };
  }

  // ==================== Fetch/XHR Interception ====================

  var _originalFetch = window.fetch;

  function patchFetch() {
    if (window.fetch.__intentMoneyPatched) return;

    window.fetch = function () {
      var args = Array.prototype.slice.call(arguments);
      var input = args[0];
      var init = args[1] || {};

      var url = "";
      if (typeof input === "string") {
        url = input;
      } else if (input instanceof Request) {
        url = input.url;
      }

      // Only intercept XHS API requests
      if (url.indexOf(XHS_API_BASE) !== -1) {
        // Capture request headers (X-s, X-t)
        var headers = {};
        if (init.headers) {
          if (init.headers instanceof Headers) {
            init.headers.forEach(function (value, key) {
              headers[key] = value;
            });
          } else if (typeof init.headers === "object") {
            headers = Object.assign({}, init.headers);
          }
        }

        var xs = headers["X-s"] || headers["x-s"] || "";
        var xt = headers["X-t"] || headers["x-t"] || "";

        if (xs || xt) {
          sendMessage("XHS_SIGNATURE_CAPTURED", {
            "X-s": xs,
            "X-t": xt,
            url: url,
            timestamp: Date.now(),
          });
        }

        // Call original fetch and intercept response
        return _originalFetch.apply(this, args).then(function (response) {
          try {
            var clonedResponse = response.clone();
            clonedResponse
              .json()
              .then(function (jsonData) {
                var parsed = parseInterceptedResponse(url, jsonData);
                if (parsed) {
                  sendMessage("XHS_INTERCEPTED_DATA", {
                    url: url,
                    apiType: parsed.type,
                    data: parsed.data,
                    raw: jsonData,
                    timestamp: Date.now(),
                  });
                }
              })
              .catch(function () {
                // Response not JSON, ignore
              });
          } catch (e) {
            // Cloning or parsing failed, ignore
          }
          return response;
        });
      }

      return _originalFetch.apply(this, args);
    };

    window.fetch.__intentMoneyPatched = true;
  }

  // ==================== XHR Interception ====================

  var _originalXHROpen = XMLHttpRequest.prototype.open;
  var _originalXHRSend = XMLHttpRequest.prototype.send;

  function patchXHR() {
    if (XMLHttpRequest.prototype.open.__intentMoneyPatched) return;

    XMLHttpRequest.prototype.open = function (method, url) {
      this.__intentMoneyUrl = url || "";
      this.__intentMoneyMethod = method || "GET";
      return _originalXHROpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function (body) {
      if (this.__intentMoneyUrl && this.__intentMoneyUrl.indexOf(XHS_API_BASE) !== -1) {
        var xhr = this;
        var originalOnReadyStateChange = xhr.onreadystatechange;

        xhr.onreadystatechange = function () {
          if (xhr.readyState === 4 && xhr.status === 200) {
            try {
              var jsonData = JSON.parse(xhr.responseText);
              var parsed = parseInterceptedResponse(xhr.__intentMoneyUrl, jsonData);
              if (parsed) {
                sendMessage("XHS_INTERCEPTED_DATA", {
                  url: xhr.__intentMoneyUrl,
                  apiType: parsed.type,
                  data: parsed.data,
                  raw: jsonData,
                  timestamp: Date.now(),
                });
              }
            } catch (e) {
              // Response not JSON, ignore
            }
          }
          if (originalOnReadyStateChange) {
            return originalOnReadyStateChange.apply(this, arguments);
          }
        };
      }
      return _originalXHRSend.apply(this, arguments);
    };

    XMLHttpRequest.prototype.open.__intentMoneyPatched = true;
  }

  // Parse intercepted API response
  function parseInterceptedResponse(url, jsonData) {
    if (!jsonData || !jsonData.data) return null;

    // Search results
    if (url.indexOf("/search/notes") !== -1) {
      var searchItems = jsonData.data.items || jsonData.data.notes || [];
      var parsed = searchItems.map(function (item) {
        var note = item.note_card || item.noteCard || item;
        var user = note.user || {};
        var interact = note.interact_info || note.interactInfo || {};

        return {
          note_id: note.note_id || note.noteId || note.id || "",
          title: note.title || note.display_title || "",
          desc: note.desc || "",
          type: note.type || "",
          author: {
            user_id: user.user_id || user.userId || user.uid || "",
            nickname: user.nickname || user.nick_name || "",
          },
          statistics: {
            liked_count:
              parseFormattedNumber(interact.liked_count) ||
              note.liked_count ||
              0,
            collected_count:
              parseFormattedNumber(interact.collected_count) ||
              note.collected_count ||
              0,
            comment_count:
              parseFormattedNumber(interact.comment_count) ||
              note.comment_count ||
              0,
            share_count:
              parseFormattedNumber(interact.share_count) ||
              note.share_count ||
              0,
          },
          tags: (note.tag_list || []).map(function (t) {
            return t.name || t.tag_name || "";
          }).filter(Boolean),
          xsec_token: note.xsec_token || "",
        };
      }).filter(function (n) {
        return n.note_id;
      });

      return {
        type: "search",
        data: {
          items: parsed,
          total: jsonData.data.total || 0,
          has_more: jsonData.data.has_more || false,
          cursor: jsonData.data.cursor || "",
        },
      };
    }

    // Note detail (feed)
    if (url.indexOf("/feed") !== -1) {
      var noteItems = jsonData.data.items || [];
      var feedParsed = noteItems.map(function (item) {
        var note = item.note_card || item.noteCard || item;
        return parseSingleNoteDetail(note);
      }).filter(Boolean);

      return {
        type: "feed",
        data: {
          items: feedParsed,
        },
      };
    }

    // Comments
    if (url.indexOf("/comment/page") !== -1) {
      var comments = jsonData.data.comments || [];
      var commentParsed = comments.map(function (c) {
        return {
          comment_id: c.id || "",
          content: c.content || "",
          user: {
            user_id: (c.user || {}).user_id || "",
            nickname: (c.user || {}).nickname || "",
          },
          liked_count: parseFormattedNumber(c.liked_count) || 0,
          sub_comment_count: c.sub_comment_count || 0,
          create_time: c.create_time || 0,
        };
      });

      return {
        type: "comments",
        data: {
          comments: commentParsed,
          has_more: jsonData.data.has_more || false,
          cursor: jsonData.data.cursor || "",
          total: jsonData.data.total || 0,
        },
      };
    }

    // Unknown API, return raw
    return {
      type: "unknown",
      data: jsonData.data,
    };
  }

  // ==================== X-s / X-t Signature Generation ====================

  // Try to locate XHS signing function
  var _signFunction = null;

  function findSignFunction() {
    if (_signFunction) return _signFunction;

    // Try known locations
    var candidates = [
      function () { return window.__xhsSign; },
      function () { return window._xhsSign; },
      function () { return window.xhsSign; },
      function () {
        // Try to find in webpack chunks
        if (window.webpackChunk_xhs) {
          var chunks = window.webpackChunk_xhs;
          for (var i = 0; i < chunks.length; i++) {
            var modules = chunks[i] && chunks[i][1];
            if (modules) {
              var keys = Object.keys(modules);
              for (var j = 0; j < keys.length; j++) {
                try {
                  var mod = {};
                  modules[keys[j]](mod, mod, function (id) { return mod; });
                  if (typeof mod.exports === "function" && mod.exports.toString().indexOf("X-s") !== -1) {
                    return mod.exports;
                  }
                  if (mod.exports && typeof mod.exports.sign === "function") {
                    return mod.exports.sign;
                  }
                } catch (e) {
                  // Module execution failed, skip
                }
              }
            }
          }
        }
        return null;
      },
      function () {
        // Try to find via global function scan
        var globals = ["__xhs_sign", "_webmsxyw", "xywSign", "_sign"];
        for (var i = 0; i < globals.length; i++) {
          if (typeof window[globals[i]] === "function") {
            return window[globals[i]];
          }
        }
        return null;
      },
    ];

    for (var i = 0; i < candidates.length; i++) {
      try {
        var fn = candidates[i]();
        if (fn && typeof fn === "function") {
          _signFunction = fn;
          return fn;
        }
      } catch (e) {
        // Continue searching
      }
    }

    return null;
  }

  function generateSignature(url, body) {
    var signFn = findSignFunction();
    if (!signFn) return null;

    try {
      // Different XHS versions may have different calling conventions
      // Convention 1: signFn(url, body) -> { "X-s": "...", "X-t": "..." }
      var result = signFn(url, body || "");
      if (result && (result["X-s"] || result["X-t"] || result.xs || result.xt)) {
        return {
          "X-s": result["X-s"] || result.xs || "",
          "X-t": result["X-t"] || result.xt || "",
        };
      }

      // Convention 2: signFn({ url: url, data: body }) -> string
      if (typeof result === "string") {
        return {
          "X-s": result,
          "X-t": Date.now().toString(),
        };
      }

      // Convention 3: signFn returns object with different key names
      if (result && typeof result === "object") {
        var keys = Object.keys(result);
        var xsKey = keys.find(function (k) {
          return k.toLowerCase().indexOf("x-s") !== -1 || k.toLowerCase().indexOf("xs") !== -1;
        });
        var xtKey = keys.find(function (k) {
          return k.toLowerCase().indexOf("x-t") !== -1 || k.toLowerCase().indexOf("xt") !== -1;
        });
        if (xsKey || xtKey) {
          return {
            "X-s": xsKey ? String(result[xsKey]) : "",
            "X-t": xtKey ? String(result[xtKey]) : Date.now().toString(),
          };
        }
      }

      return null;
    } catch (e) {
      console.warn("[Intent Money XHS] Signature generation failed:", e);
      return null;
    }
  }

  // ==================== Message Handler ====================

  window.addEventListener("message", function (event) {
    if (event.source !== window) return;
    if (!event.data || event.data.source !== CONTENT_SOURCE) return;

    var type = event.data.type;
    var requestId = event.data.requestId;
    var payload = event.data.payload || {};

    switch (type) {
      case "XHS_EXTRACT_SSR": {
        var ssrData = extractSSRData();
        if (ssrData) {
          var searchResults = parseSearchResultsFromSSR(ssrData);
          var noteDetail = parseNoteDetailFromSSR(ssrData);
          sendMessage("XHS_SSR_DATA_RESULT", {
            success: true,
            searchResults: searchResults,
            noteDetail: noteDetail,
            rawKeys: Object.keys(ssrData),
          }, requestId);
        } else {
          sendMessage("XHS_SSR_DATA_RESULT", {
            success: false,
            searchResults: [],
            noteDetail: null,
            error: "No __INIT_PROPS__ found on window",
          }, requestId);
        }
        break;
      }

      case "XHS_GET_SIGNATURE": {
        var url = payload.url || "";
        var body = payload.body || "";
        if (!url) {
          sendMessage("XHS_SIGNATURE_RESULT", {
            success: false,
            error: "No URL provided",
            signature: null,
          }, requestId);
          break;
        }

        var sig = generateSignature(url, body);
        if (sig) {
          sendMessage("XHS_SIGNATURE_RESULT", {
            success: true,
            signature: sig,
          }, requestId);
        } else {
          sendMessage("XHS_SIGNATURE_RESULT", {
            success: false,
            error: "XHS signing function not found or failed",
            signature: null,
          }, requestId);
        }
        break;
      }

      default:
        break;
    }
  });

  // ==================== Initialization ====================

  function init() {
    // Patch fetch and XHR for request interception
    patchFetch();
    patchXHR();

    // Extract and send initial SSR data if available
    try {
      var ssrData = extractSSRData();
      if (ssrData) {
        var searchResults = parseSearchResultsFromSSR(ssrData);
        var noteDetail = parseNoteDetailFromSSR(ssrData);
        sendMessage("XHS_SSR_DATA_RESULT", {
          success: true,
          searchResults: searchResults,
          noteDetail: noteDetail,
          rawKeys: Object.keys(ssrData),
          autoExtracted: true,
        });
      }
    } catch (e) {
      // SSR extraction on init is best-effort
    }

    // Try to locate sign function eagerly
    findSignFunction();
  }

  init();
})();
