// douyin_content.js - Douyin page content script for Intent Money extension

const EXTENSION_SOURCE = "intent-money-douyin";

// Parse formatted numbers like "1.6万" → 16000, "234" → 234
function parseFormattedNumber(text) {
  if (!text) return 0;
  text = text.trim();
  if (text.includes("亿")) {
    return Math.round(parseFloat(text.replace("亿", "")) * 100000000);
  }
  if (text.includes("万")) {
    return Math.round(parseFloat(text.replace("万", "")) * 10000);
  }
  return parseInt(text.replace(/[^\d]/g, ""), 10) || 0;
}

// Extract SSR data by injecting a Main World script
function extractSSRData() {
  return new Promise((resolve) => {
    const requestId = Date.now().toString();

    const listener = (event) => {
      if (
        event.data &&
        event.data.source === EXTENSION_SOURCE &&
        event.data.requestId === requestId &&
        event.data.type === "SSR_DATA_RESULT"
      ) {
        window.removeEventListener("message", listener);
        resolve(event.data.data || null);
      }
    };
    window.addEventListener("message", listener);

    // Inject script into Main World
    const script = document.createElement("script");
    script.textContent = `
      (function() {
        var requestId = "${requestId}";
        var data = null;

        // Try __INIT_PROPS__ first
        if (window.__INIT_PROPS__) {
          data = window.__INIT_PROPS__;
        }
        // Try __NEXT_DATA__
        else if (window.__NEXT_DATA__ && window.__NEXT_DATA__.props) {
          data = window.__NEXT_DATA__.props;
        }

        window.postMessage({
          source: "${EXTENSION_SOURCE}",
          type: "SSR_DATA_RESULT",
          requestId: requestId,
          data: data
        }, "*");
      })();
    `;
    document.documentElement.appendChild(script);
    script.remove();

    // Timeout after 3 seconds
    setTimeout(() => {
      window.removeEventListener("message", listener);
      resolve(null);
    }, 3000);
  });
}

// Parse search results from SSR data
function parseSearchResultsFromSSR(ssrData) {
  // SSR data structure varies; try common paths
  let items = [];

  if (ssrData) {
    // Try various paths where search results might be stored
    const paths = [
      ssrData?.search?.data,
      ssrData?.search?.list,
      ssrData?.data,
      ssrData?.aweme_list,
      ssrData?.pageProps?.data,
    ];

    for (const path of paths) {
      if (Array.isArray(path)) {
        items = path;
        break;
      }
      if (path && Array.isArray(path.list)) {
        items = path.list;
        break;
      }
      if (path && Array.isArray(path.data)) {
        items = path.data;
        break;
      }
    }
  }

  return items.map((item) => {
    const aweme = item?.aweme_info || item;
    return {
      video_id: aweme?.aweme_id || aweme?.id || "",
      title: aweme?.desc || "",
      author: {
        uid: aweme?.author?.uid || "",
        nickname: aweme?.author?.nickname || "",
      },
      statistics: {
        play_count: aweme?.statistics?.play_count || 0,
        digg_count: aweme?.statistics?.digg_count || 0,
        comment_count: aweme?.statistics?.comment_count || 0,
        share_count: aweme?.statistics?.share_count || 0,
      },
      tags: (aweme?.text_extra || []).map(t => t.hashtag_name).filter(Boolean),
      share_url: aweme?.share_url || "",
    };
  }).filter(v => v.video_id);
}

// Parse search results from DOM
function parseSearchResultsFromDOM() {
  const results = [];

  // Try data-e2e attribute selectors first (more stable)
  const cards = document.querySelectorAll('[data-e2e="search-card"], [data-e2e="search-result-card"]');

  if (cards.length === 0) {
    // Fallback: look for video link patterns
    const videoLinks = document.querySelectorAll('a[href*="/video/"]');
    videoLinks.forEach((link) => {
      const card = link.closest('div[class]')?.parentElement;
      if (!card) return;

      const titleEl = card.querySelector('p, span, [class*="title"], [class*="desc"]');
      const authorEl = card.querySelector('[class*="author"], [class*="name"]');
      const statsEls = card.querySelectorAll('span[class*="count"], [class*="num"]');

      const videoId = (link.href.match(/\/video\/(\d+)/) || [])[1] || "";

      results.push({
        video_id: videoId,
        title: titleEl?.textContent?.trim() || "",
        author: { uid: "", nickname: authorEl?.textContent?.trim() || "" },
        statistics: {
          play_count: statsEls[0] ? parseFormattedNumber(statsEls[0].textContent) : 0,
          digg_count: statsEls[1] ? parseFormattedNumber(statsEls[1].textContent) : 0,
          comment_count: statsEls[2] ? parseFormattedNumber(statsEls[2].textContent) : 0,
          share_count: 0,
        },
        tags: [],
        share_url: link.href || "",
      });
    });
  } else {
    cards.forEach((card) => {
      const link = card.querySelector('a[href*="/video/"]');
      const videoId = (link?.href?.match(/\/video\/(\d+)/) || [])[1] || "";
      const titleEl = card.querySelector('[class*="title"], [class*="desc"], p');
      const authorEl = card.querySelector('[class*="author"], [class*="name"]');

      results.push({
        video_id: videoId,
        title: titleEl?.textContent?.trim() || "",
        author: { uid: "", nickname: authorEl?.textContent?.trim() || "" },
        statistics: { play_count: 0, digg_count: 0, comment_count: 0, share_count: 0 },
        tags: [],
        share_url: link?.href || "",
      });
    });
  }

  return results.filter(v => v.video_id);
}

// Get X-Bogus signature via Main World injection
function getXBogusSignature(url) {
  return new Promise((resolve) => {
    const requestId = Date.now().toString();

    const listener = (event) => {
      if (
        event.data &&
        event.data.source === EXTENSION_SOURCE &&
        event.data.requestId === requestId &&
        event.data.type === "XBOGUS_RESULT"
      ) {
        window.removeEventListener("message", listener);
        resolve(event.data.signature || null);
      }
    };
    window.addEventListener("message", listener);

    const script = document.createElement("script");
    script.textContent = `
      (function() {
        var requestId = "${requestId}";
        var url = "${url.replace(/"/g, '\\"')}";
        var signature = null;

        try {
          // Try common signing function locations
          if (window._bytedAcrawler && window._bytedAcrawler.sign) {
            signature = window._bytedAcrawler.sign({ url: url });
          } else if (window.byted_acrawler && window.byted_acrawler.sign) {
            signature = window.byted_acrawler.sign({ url: url });
          } else if (window._signature) {
            signature = window._signature(url);
          }
        } catch(e) {}

        window.postMessage({
          source: "${EXTENSION_SOURCE}",
          type: "XBOGUS_RESULT",
          requestId: requestId,
          signature: signature
        }, "*");
      })();
    `;
    document.documentElement.appendChild(script);
    script.remove();

    setTimeout(() => {
      window.removeEventListener("message", listener);
      resolve(null);
    }, 3000);
  });
}

// Message handler
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const handlers = {
    PING: async () => {
      return { success: true, url: window.location.href };
    },

    EXTRACT_SSR_DATA: async () => {
      const ssrData = await extractSSRData();
      if (ssrData) {
        const videos = parseSearchResultsFromSSR(ssrData);
        return { success: true, source: "ssr", videos: videos, rawKeys: ssrData ? Object.keys(ssrData) : [] };
      }
      return { success: false, source: "ssr", videos: [], error: "No SSR data found" };
    },

    EXTRACT_DOM_DATA: async () => {
      const videos = parseSearchResultsFromDOM();
      return { success: videos.length > 0, source: "dom", videos: videos };
    },

    GET_XBOGUS_SIGNATURE: async () => {
      const url = message.url || window.location.href;
      const signature = await getXBogusSignature(url);
      if (signature) {
        return { success: true, signature: signature };
      }
      return { success: false, error: "X-Bogus signing function not available" };
    },
  };

  const handler = handlers[message.action];
  if (handler) {
    handler().then(sendResponse).catch(err => sendResponse({ success: false, error: err.message }));
    return true; // Keep message channel open for async response
  }
});
