const PLATFORM_CONFIG = {
  xiaohongshu: {
    domain: ".xiaohongshu.com",
    loginUrl: "https://www.xiaohongshu.com",
    sessionCookie: "web_session"
  },
  douyin: {
    domain: ".douyin.com",
    loginUrl: "https://www.douyin.com",
    sessionCookie: "sessionid"
  }
};

const DEFAULT_SERVER_URL = "http://127.0.0.1:9090";

// XHS intercepted data cache
const xhsInterceptedCache = {};
const XHS_CACHE_MAX_SIZE = 50;

// XHS signature cache
const xhsSignatureCache = [];
const XHS_SIGNATURE_MAX_AGE = 5 * 60 * 1000; // 5 minutes

async function getConfig() {
  const result = await chrome.storage.local.get(["serverUrl", "authToken"]);
  return {
    serverUrl: result.serverUrl || DEFAULT_SERVER_URL,
    authToken: result.authToken || ""
  };
}

async function syncCookiesToBackend(platform, cookies) {
  const config = await getConfig();
  if (!config.authToken) {
    console.warn("Intent Money: No auth token configured, proceeding with sync anyway");
  }
  const headers = {
    "Content-Type": "application/json"
  };
  if (config.authToken) {
    headers["Authorization"] = `Bearer ${config.authToken}`;
  }
  const response = await fetch(`${config.serverUrl}/api/v1/accounts/${platform}/extension`, {
    method: "POST",
    headers: headers,
    body: JSON.stringify({ cookies: cookies })
  });
  if (!response.ok) {
    throw new Error(`Sync failed with status ${response.status}`);
  }
  return response;
}

async function broadcastStatusToTabs(platform, loggedIn, cookieCount) {
  try {
    const tabs = await chrome.tabs.query({
      url: ["http://localhost:*/*", "http://127.0.0.1:*/*"]
    });
    const timestamp = Date.now();
    for (const tab of tabs) {
      try {
        await chrome.tabs.sendMessage(tab.id, {
          action: "STATUS_UPDATE",
          platform,
          loggedIn,
          cookieCount,
          timestamp
        });
      } catch (err) {
        // Tab may not have content script loaded, ignore
      }
    }
  } catch (err) {
    console.error("Intent Money: Broadcast error", err);
  }
}

chrome.cookies.onChanged.addListener(async (changeInfo) => {
  const { cookie, removed } = changeInfo;
  for (const [platform, cfg] of Object.entries(PLATFORM_CONFIG)) {
    if (cookie.domain.endsWith(cfg.domain)) {
      if (!removed && cookie.name === cfg.sessionCookie) {
        const allCookies = await chrome.cookies.getAll({ domain: cfg.domain });
        await syncCookiesToBackend(platform, allCookies);
        const sessionCookie = allCookies.find((c) => c.name === cfg.sessionCookie);
        const loggedIn = !!sessionCookie && !!sessionCookie.value;
        await broadcastStatusToTabs(platform, loggedIn, allCookies.length);
      }
    }
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handler = messageHandlers[message.action];
  if (handler) {
    handler(message, sender, sendResponse);
    return true;
  }
});

const messageHandlers = {
  GET_COOKIES: async (message, sender, sendResponse) => {
    try {
      const platform = message.platform || "xiaohongshu";
      const cfg = PLATFORM_CONFIG[platform];
      if (!cfg) {
        sendResponse({ success: false, error: `Unknown platform: ${platform}` });
        return;
      }
      const cookies = await chrome.cookies.getAll({ domain: cfg.domain });
      sendResponse({ success: true, cookies: cookies });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  OPEN_LOGIN: async (message, sender, sendResponse) => {
    try {
      const platform = message.platform || "xiaohongshu";
      const cfg = PLATFORM_CONFIG[platform];
      if (!cfg) {
        sendResponse({ success: false, error: `Unknown platform: ${platform}` });
        return;
      }
      await chrome.tabs.create({ url: cfg.loginUrl });
      sendResponse({ success: true });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  CHECK_LOGIN: async (message, sender, sendResponse) => {
    try {
      const platform = message.platform || "xiaohongshu";
      const cfg = PLATFORM_CONFIG[platform];
      if (!cfg) {
        sendResponse({ success: false, error: `Unknown platform: ${platform}` });
        return;
      }
      const cookies = await chrome.cookies.getAll({ domain: cfg.domain });
      const sessionCookie = cookies.find((c) => c.name === cfg.sessionCookie);
      sendResponse({
        success: true,
        loggedIn: !!sessionCookie && !!sessionCookie.value,
        cookieName: cfg.sessionCookie,
        cookieExists: !!sessionCookie
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  SET_CONFIG: async (message, sender, sendResponse) => {
    try {
      const data = {};
      if (message.serverUrl !== undefined) data.serverUrl = message.serverUrl;
      if (message.authToken !== undefined) data.authToken = message.authToken;
      await chrome.storage.local.set(data);
      sendResponse({ success: true });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  GET_CONFIG: async (message, sender, sendResponse) => {
    try {
      const config = await getConfig();
      sendResponse({ success: true, config: config });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  SYNC_COOKIES: async (message, sender, sendResponse) => {
    try {
      const platform = message.platform || "xiaohongshu";
      const cfg = PLATFORM_CONFIG[platform];
      if (!cfg) {
        sendResponse({ success: false, error: `Unknown platform: ${platform}` });
        return;
      }
      const cookies = await chrome.cookies.getAll({ domain: cfg.domain });
      try {
        await syncCookiesToBackend(platform, cookies);
      } catch (syncErr) {
        sendResponse({ success: false, error: syncErr.message });
        return;
      }
      const sessionCookie = cookies.find((c) => c.name === cfg.sessionCookie);
      const loggedIn = !!sessionCookie && !!sessionCookie.value;
      await broadcastStatusToTabs(platform, loggedIn, cookies.length);
      sendResponse({ success: true, cookies: cookies });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  BROADCAST_STATUS: async (message, sender, sendResponse) => {
    try {
      const platform = message.platform || "xiaohongshu";
      const cfg = PLATFORM_CONFIG[platform];
      if (!cfg) {
        sendResponse({ success: false, error: `Unknown platform: ${platform}` });
        return;
      }
      const cookies = await chrome.cookies.getAll({ domain: cfg.domain });
      const sessionCookie = cookies.find((c) => c.name === cfg.sessionCookie);
      const loggedIn = !!sessionCookie && !!sessionCookie.value;
      await broadcastStatusToTabs(platform, loggedIn, cookies.length);
      sendResponse({ success: true, loggedIn, cookieCount: cookies.length });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  TRIGGER_POPUP: async (message, sender, sendResponse) => {
    try {
      if (chrome.action && chrome.action.openPopup) {
        await chrome.action.openPopup();
        sendResponse({ success: true });
      } else {
        sendResponse({ success: false, error: "当前浏览器不支持调起扩展弹窗" });
      }
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  SCRAPE_DOUYIN_SEARCH: async (message, sender, sendResponse) => {
    try {
      const keyword = message.keyword || "袜子";
      const limit = message.limit || 20;
      const platformId = message.platform_id || "";

      // Step 1: Try Service Worker fetch with real Cookie
      let videos = [];
      let source = "extension_api";

      try {
        const cfg = PLATFORM_CONFIG.douyin;
        const cookies = await chrome.cookies.getAll({ domain: cfg.domain });
        const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join("; ");

        // Try to find an active Douyin tab for X-Bogus signature
        let xbogus = null;
        const douyinTabs = await chrome.tabs.query({ url: "*://*.douyin.com/*" });

        if (douyinTabs.length > 0) {
          try {
            const signResult = await chrome.tabs.sendMessage(douyinTabs[0].id, {
              action: "GET_XBOGUS_SIGNATURE",
              url: `https://www.douyin.com/aweme/v1/search/item/?keyword=${encodeURIComponent(keyword)}&count=${limit}&offset=0&search_source=normal_search&type=1`
            });
            if (signResult && signResult.success) {
              xbogus = signResult.signature;
            }
          } catch (err) {
            console.warn("Intent Money: X-Bogus signature request failed", err);
          }
        }

        // Build API URL
        let apiUrl = `https://www.douyin.com/aweme/v1/search/item/?keyword=${encodeURIComponent(keyword)}&count=${limit}&offset=0&search_source=normal_search&type=1`;
        if (xbogus) {
          apiUrl += `&X-Bogus=${xbogus}`;
        }

        const response = await fetch(apiUrl, {
          method: "GET",
          headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json, text/plain, */*",
            "Cookie": cookieStr
          }
        });

        if (response.ok) {
          const data = await response.json();
          const items = data?.data || data?.data?.list || [];
          videos = items.map(item => {
            const aweme = item.aweme_info || item;
            const stats = aweme.statistics || {};
            return {
              video_id: String(aweme.aweme_id || aweme.id || ""),
              title: aweme.desc || "",
              author: {
                uid: String(aweme.author?.uid || ""),
                nickname: aweme.author?.nickname || ""
              },
              statistics: {
                play_count: stats.play_count || 0,
                digg_count: stats.digg_count || 0,
                comment_count: stats.comment_count || 0,
                share_count: stats.share_count || 0
              },
              tags: (aweme.text_extra || []).map(t => t.hashtag_name).filter(Boolean),
              share_url: aweme.share_url || ""
            };
          }).filter(v => v.video_id);
        } else {
          console.warn(`Intent Money: Douyin API returned ${response.status}`);
          source = "extension_api_failed";
        }
      } catch (apiErr) {
        console.warn("Intent Money: Douyin API fetch failed", apiErr);
        source = "extension_api_failed";
      }

      // Step 2: If API failed, try SSR data from active Douyin tab
      if (videos.length === 0) {
        const douyinTabs = await chrome.tabs.query({ url: "*://*.douyin.com/search/*" });
        if (douyinTabs.length > 0) {
          try {
            // Navigate to search page if not already there
            const searchUrl = `https://www.douyin.com/search/${encodeURIComponent(keyword)}?type=video`;
            const tab = douyinTabs[0];

            // Try to extract SSR data from the tab
            const ssrResult = await chrome.tabs.sendMessage(tab.id, {
              action: "EXTRACT_SSR_DATA"
            });

            if (ssrResult && ssrResult.success && ssrResult.videos.length > 0) {
              videos = ssrResult.videos;
              source = "extension_ssr";
            }
          } catch (ssrErr) {
            console.warn("Intent Money: SSR extraction failed", ssrErr);
          }
        }
      }

      // Step 3: If SSR also failed, try DOM parsing
      if (videos.length === 0) {
        const douyinTabs = await chrome.tabs.query({ url: "*://*.douyin.com/*" });
        if (douyinTabs.length > 0) {
          try {
            const domResult = await chrome.tabs.sendMessage(douyinTabs[0].id, {
              action: "EXTRACT_DOM_DATA"
            });

            if (domResult && domResult.success && domResult.videos.length > 0) {
              videos = domResult.videos;
              source = "extension_dom";
            }
          } catch (domErr) {
            console.warn("Intent Money: DOM extraction failed", domErr);
          }
        }
      }

      // Step 4: Sync results to backend
      if (videos.length > 0 && platformId) {
        const config = await getConfig();
        const headers = { "Content-Type": "application/json" };
        if (config.authToken) {
          headers["Authorization"] = `Bearer ${config.authToken}`;
        }

        try {
          await fetch(`${config.serverUrl}/api/v1/market/extension-scrape`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
              keyword: keyword,
              platform_id: platformId,
              videos: videos,
              source: source
            })
          });
        } catch (syncErr) {
          console.error("Intent Money: Failed to sync scrape results to backend", syncErr);
        }
      }

      sendResponse({ success: videos.length > 0, videos: videos, source: source, keyword: keyword });
    } catch (err) {
      sendResponse({ success: false, error: err.message, videos: [] });
    }
  },

  CHECK_DOUYIN_TAB: async (message, sender, sendResponse) => {
    try {
      const douyinTabs = await chrome.tabs.query({ url: "*://*.douyin.com/*" });
      const searchTabs = await chrome.tabs.query({ url: "*://*.douyin.com/search/*" });
      sendResponse({
        success: true,
        hasDouyinTab: douyinTabs.length > 0,
        hasSearchTab: searchTabs.length > 0,
        douyinTabCount: douyinTabs.length,
        searchTabCount: searchTabs.length
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  OPEN_DOUYIN_SEARCH: async (message, sender, sendResponse) => {
    try {
      const keyword = message.keyword || "袜子";
      const url = `https://www.douyin.com/search/${encodeURIComponent(keyword)}?type=video`;
      await chrome.tabs.create({ url: url });
      sendResponse({ success: true });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  HEARTBEAT: async (message, sender, sendResponse) => {
    try {
      const douyinTabs = await chrome.tabs.query({ url: "*://*.douyin.com/*" });
      const config = await getConfig();
      sendResponse({
        success: true,
        online: true,
        hasDouyinTab: douyinTabs.length > 0,
        timestamp: Date.now()
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  SCRAPE_XHS_SEARCH: async (message, sender, sendResponse) => {
    try {
      const keyword = message.keyword || "袜子";
      const platformId = message.platform_id || "";

      let notes = [];
      let source = "unknown";

      // Layer 1: Intercepted Data Cache (Priority)
      // Cache keys from XHS_INTERCEPTED_DATA: "search_${keyword}" or "search" or "unknown"
      const cacheKeys = [`search_${keyword}`, `search`, keyword];
      for (const ck of cacheKeys) {
        if (xhsInterceptedCache[ck]) {
          const cached = xhsInterceptedCache[ck];
          // Check if cache is not too old (within 10 minutes)
          if (Date.now() - cached.timestamp < 10 * 60 * 1000 && cached.notes && cached.notes.length > 0) {
            notes = cached.notes;
            source = "intercepted";
            break;
          }
        }
      }

      // Layer 2: Active API Call
      if (notes.length === 0) {
        try {
          const cookies = await chrome.cookies.getAll({ domain: ".xiaohongshu.com" });
          const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join("; ");

          // Try to get X-s/X-t signature from XHS tab content script
          let xsSignature = null;
          let xtTimestamp = null;
          const xhsTabs = await chrome.tabs.query({ url: "*://*.xiaohongshu.com/*" });

          const searchApiUrl = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes";
          const searchBody = JSON.stringify({
            keyword: keyword,
            page: 1,
            page_size: 20,
            search_id: "",
            sort: "general",
            note_type: 0
          });

          if (xhsTabs.length > 0) {
            try {
              const signResult = await chrome.tabs.sendMessage(xhsTabs[0].id, {
                action: "GET_XHS_SIGNATURE",
                url: searchApiUrl,
                body: searchBody
              });
              if (signResult && signResult.success && signResult.signature) {
                xsSignature = signResult.signature["X-s"] || signResult.signature.xs || "";
                xtTimestamp = signResult.signature["X-t"] || signResult.signature.xt || "";
              }
            } catch (err) {
              console.warn("Intent Money: XHS signature request failed", err);
            }
          }

          // Fallback: try to reuse cached signature
          if (!xsSignature && xhsSignatureCache.length > 0) {
            const now = Date.now();
            const validSig = xhsSignatureCache.find(s => (now - s.timestamp) < XHS_SIGNATURE_MAX_AGE);
            if (validSig) {
              xsSignature = validSig.xs;
              xtTimestamp = validSig.xt;
            }
          }

          if (xsSignature || xtTimestamp) {
            const response = await fetch(searchApiUrl, {
              method: "POST",
              headers: {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Origin": "https://www.xiaohongshu.com",
                "Referer": "https://www.xiaohongshu.com/",
                "Content-Type": "application/json",
                "Cookie": cookieStr,
                "X-s": xsSignature || "",
                "X-t": String(xtTimestamp || Date.now())
              },
              body: searchBody
            });

            if (response.ok) {
              const data = await response.json();
              const items = data?.data?.items || [];
              notes = items.map(item => {
                const noteCard = item.note_card || item;
                return {
                  note_id: noteCard.note_id || "",
                  title: noteCard.display_title || noteCard.title || "",
                  author: {
                    user_id: noteCard.user?.user_id || "",
                    nickname: noteCard.user?.nickname || ""
                  },
                  interact_info: {
                    liked_count: noteCard.interact_info?.liked_count || "0",
                    collected_count: noteCard.interact_info?.collected_count || "0",
                    comment_count: noteCard.interact_info?.comment_count || "0",
                    share_count: noteCard.interact_info?.share_count || "0"
                  },
                  note_type: noteCard.type || 0,
                  tag_list: (noteCard.tag_list || []).map(t => t.name).filter(Boolean)
                };
              }).filter(n => n.note_id);
              source = "api";
            } else {
              console.warn(`Intent Money: XHS API returned ${response.status}`);
            }
          }
        } catch (apiErr) {
          console.warn("Intent Money: XHS API fetch failed", apiErr);
        }
      }

      // Layer 3: SSR Data Extraction
      if (notes.length === 0) {
        const xhsTabs = await chrome.tabs.query({ url: "*://*.xiaohongshu.com/*" });
        if (xhsTabs.length > 0) {
          try {
            const ssrResult = await chrome.tabs.sendMessage(xhsTabs[0].id, {
              action: "EXTRACT_XHS_SSR"
            });
            // Main World returns { success, searchResults: [...], noteDetail, rawKeys }
            if (ssrResult && ssrResult.success) {
              const ssrNotes = ssrResult.searchResults || ssrResult.notes || [];
              if (ssrNotes.length > 0) {
                notes = ssrNotes;
                source = "ssr";
              }
            }
          } catch (ssrErr) {
            console.warn("Intent Money: XHS SSR extraction failed", ssrErr);
          }
        }
      }

      // Layer 4: DOM Parsing
      if (notes.length === 0) {
        const xhsTabs = await chrome.tabs.query({ url: "*://*.xiaohongshu.com/*" });
        if (xhsTabs.length > 0) {
          try {
            const domResult = await chrome.tabs.sendMessage(xhsTabs[0].id, {
              action: "EXTRACT_XHS_DOM"
            });
            if (domResult && domResult.success && domResult.notes && domResult.notes.length > 0) {
              notes = domResult.notes;
              source = "dom";
            }
          } catch (domErr) {
            console.warn("Intent Money: XHS DOM extraction failed", domErr);
          }
        }
      }

      // Final Step: Sync to Backend
      if (notes.length > 0 && platformId) {
        const config = await getConfig();
        const headers = { "Content-Type": "application/json" };
        if (config.authToken) {
          headers["Authorization"] = `Bearer ${config.authToken}`;
        }

        try {
          await fetch(`${config.serverUrl}/api/v1/market/extension-scrape-xhs`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
              keyword: keyword,
              platform_id: platformId,
              notes: notes,
              source: source
            })
          });
        } catch (syncErr) {
          console.error("Intent Money: Failed to sync XHS scrape results to backend", syncErr);
        }
      }

      sendResponse({ success: notes.length > 0, notes: notes, source: source, keyword: keyword });
    } catch (err) {
      sendResponse({ success: false, error: err.message, notes: [] });
    }
  },

  XHS_INTERCEPTED_DATA: async (message, sender, sendResponse) => {
    try {
      // Content script forwards: { action, requestId, data: { url, apiType, data, raw, timestamp } }
      const interceptedData = message.data || {};
      const apiType = interceptedData.apiType || "unknown";
      const keyword = interceptedData.keyword || "";
      const notesData = interceptedData.data || {};
      const cacheKey = keyword ? `${apiType}_${keyword}` : apiType;

      // Extract notes array from the intercepted data
      let notes = [];
      if (apiType === "search" && notesData.items) {
        notes = notesData.items;
      } else if (apiType === "feed" && notesData.items) {
        notes = notesData.items;
      } else if (Array.isArray(notesData)) {
        notes = notesData;
      }

      // Store in cache
      if (notes.length > 0) {
        xhsInterceptedCache[cacheKey] = {
          notes: notes,
          keyword: keyword,
          apiType: apiType,
          timestamp: Date.now()
        };
      }

      // Enforce FIFO max size
      const cacheKeys = Object.keys(xhsInterceptedCache);
      if (cacheKeys.length > XHS_CACHE_MAX_SIZE) {
        const sortedKeys = cacheKeys.sort((a, b) => {
          return (xhsInterceptedCache[a].timestamp || 0) - (xhsInterceptedCache[b].timestamp || 0);
        });
        const removeCount = cacheKeys.length - XHS_CACHE_MAX_SIZE;
        for (let i = 0; i < removeCount; i++) {
          delete xhsInterceptedCache[sortedKeys[i]];
        }
      }

      // Auto-sync to backend if authToken is configured
      const config = await getConfig();
      if (config.authToken && notes.length > 0) {
        const headers = { "Content-Type": "application/json" };
        headers["Authorization"] = `Bearer ${config.authToken}`;

        try {
          await fetch(`${config.serverUrl}/api/v1/market/extension-scrape-xhs`, {
            method: "POST",
            headers: headers,
            body: JSON.stringify({
              keyword: keyword,
              platform_id: "",
              notes: notes,
              source: "intercepted"
            })
          });
        } catch (syncErr) {
          console.error("Intent Money: Failed to auto-sync XHS intercepted data", syncErr);
        }
      }

      sendResponse({ success: true, cached: notes.length > 0, noteCount: notes.length });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  XHS_SIGNATURE_CAPTURED: async (message, sender, sendResponse) => {
    try {
      // Content script forwards: { action, requestId, data: { "X-s": ..., "X-t": ..., url, timestamp } }
      const sigData = message.data || {};
      const xs = sigData["X-s"] || sigData.xs || "";
      const xt = sigData["X-t"] || sigData.xt || "";

      if (xs || xt) {
        // Add to cache
        xhsSignatureCache.push({
          xs: xs,
          xt: xt,
          url: sigData.url || "",
          timestamp: sigData.timestamp || Date.now()
        });

        // Remove expired signatures and enforce max size (keep last 5)
        const now = Date.now();
        const validSigs = xhsSignatureCache.filter(s => (now - s.timestamp) < XHS_SIGNATURE_MAX_AGE);
        xhsSignatureCache.length = 0;
        xhsSignatureCache.push(...validSigs.slice(-5));
      }

      sendResponse({ success: true });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  CHECK_XHS_TAB: async (message, sender, sendResponse) => {
    try {
      const xhsTabs = await chrome.tabs.query({ url: "*://*.xiaohongshu.com/*" });
      const searchTabs = await chrome.tabs.query({ url: "*://*.xiaohongshu.com/search_result*" });
      sendResponse({
        success: true,
        hasXhsTab: xhsTabs.length > 0,
        hasSearchTab: searchTabs.length > 0,
        xhsTabCount: xhsTabs.length,
        searchTabCount: searchTabs.length
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  OPEN_XHS_SEARCH: async (message, sender, sendResponse) => {
    try {
      const keyword = message.keyword || "袜子";
      const url = `https://www.xiaohongshu.com/search_result?keyword=${encodeURIComponent(keyword)}&source=web_search_result_note`;
      await chrome.tabs.create({ url: url });
      sendResponse({ success: true });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  },

  XHS_SSR_DATA: async (message, sender, sendResponse) => {
    try {
      // Auto-extracted SSR data from content script on page load
      const ssrData = message.data || {};
      const searchResults = ssrData.searchResults || [];
      const noteDetail = ssrData.noteDetail || null;

      // Cache search results if available
      if (searchResults.length > 0) {
        const keyword = ssrData.keyword || "";
        const cacheKey = keyword ? `ssr_${keyword}` : "ssr";
        xhsInterceptedCache[cacheKey] = {
          notes: searchResults,
          keyword: keyword,
          apiType: "ssr",
          timestamp: Date.now()
        };
      }

      sendResponse({ success: true, searchResultCount: searchResults.length, hasNoteDetail: !!noteDetail });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  }
};
