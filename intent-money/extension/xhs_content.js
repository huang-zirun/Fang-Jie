// xhs_content.js - Xiaohongshu (RED) page content script for Intent Money extension
// Runs in the isolated world; bridges Main World <-> Background service worker

const CONTENT_SOURCE = "intent-money-xhs-content";
const MAIN_WORLD_SOURCE = "intent-money-xhs";

// ---------------------------------------------------------------------------
// Utility: parse formatted numbers ("1.2万" → 12000, "3.5亿" → 350000000)
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// 1. Main World Script Injection
// ---------------------------------------------------------------------------
function injectMainWorldScript() {
  const script = document.createElement("script");
  script.src = chrome.runtime.getURL("xhs_main_world.js");
  script.onload = function () {
    script.remove();
  };
  script.onerror = function () {
    console.warn("Intent Money XHS: Failed to inject xhs_main_world.js");
    script.remove();
  };
  (document.head || document.documentElement).appendChild(script);
}

// Inject on load
injectMainWorldScript();

// ---------------------------------------------------------------------------
// 2. Message Bridge: Main World → Content Script → Background
// ---------------------------------------------------------------------------
window.addEventListener("message", (event) => {
  if (event.source !== window) return;
  if (!event.data || event.data.source !== MAIN_WORLD_SOURCE) return;

  const { type, requestId, data } = event.data;

  switch (type) {
    case "XHS_SSR_DATA_RESULT":
      chrome.runtime.sendMessage({
        action: "XHS_SSR_DATA",
        requestId: requestId,
        data: data
      });
      break;

    case "XHS_INTERCEPTED_DATA":
      chrome.runtime.sendMessage({
        action: "XHS_INTERCEPTED_DATA",
        requestId: requestId,
        data: data
      });
      break;

    case "XHS_SIGNATURE_CAPTURED":
      chrome.runtime.sendMessage({
        action: "XHS_SIGNATURE_CAPTURED",
        requestId: requestId,
        data: data
      });
      break;

    case "XHS_SIGNATURE_RESULT":
      chrome.runtime.sendMessage({
        action: "XHS_SIGNATURE_RESULT",
        requestId: requestId,
        data: data
      });
      break;

    default:
      break;
  }
});

// ---------------------------------------------------------------------------
// 2b. Message Bridge: Background → Content Script → Main World
// ---------------------------------------------------------------------------
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Forward background requests to Main World
  if (message.action === "EXTRACT_XHS_SSR") {
    forwardToMainWorld("XHS_EXTRACT_SSR", message.requestId)
      .then((result) => sendResponse(result))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.action === "GET_XHS_SIGNATURE") {
    forwardToMainWorld("XHS_GET_SIGNATURE", message.requestId, message.url)
      .then((result) => sendResponse(result))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  // Handle direct content-script actions
  const handlers = {
    PING: async () => {
      return { success: true, url: window.location.href };
    },

    EXTRACT_XHS_SSR: async () => {
      return await extractSSRData();
    },

    EXTRACT_XHS_DOM: async () => {
      const url = window.location.href;
      if (url.includes("/search_result")) {
        const notes = parseSearchResultsFromDOM();
        return { success: notes.length > 0, source: "dom", notes: notes };
      }
      if (url.includes("/explore/") || url.includes("/discovery/item/")) {
        const note = parseNoteDetailFromDOM();
        return { success: !!note, source: "dom", note: note };
      }
      return { success: false, source: "dom", error: "Unsupported page type for DOM extraction" };
    },

    GET_XHS_SIGNATURE: async () => {
      const url = message.url || window.location.href;
      return await getSignatureFromMainWorld(url);
    }
  };

  const handler = handlers[message.action];
  if (handler) {
    handler()
      .then(sendResponse)
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // keep channel open for async
  }
});

// ---------------------------------------------------------------------------
// Forward message to Main World and wait for response (requestId pattern)
// ---------------------------------------------------------------------------
function forwardToMainWorld(type, requestId, extraPayload) {
  return new Promise((resolve) => {
    if (!requestId) {
      requestId = Date.now().toString();
    }

    const listener = (event) => {
      if (
        event.source === window &&
        event.data &&
        event.data.source === MAIN_WORLD_SOURCE &&
        event.data.requestId === requestId
      ) {
        window.removeEventListener("message", listener);
        resolve(event.data.data || null);
      }
    };
    window.addEventListener("message", listener);

    const payload = {
      source: CONTENT_SOURCE,
      type: type,
      requestId: requestId
    };
    if (extraPayload) {
      payload.url = extraPayload;
    }

    window.postMessage(payload, "*");

    // 3-second timeout
    setTimeout(() => {
      window.removeEventListener("message", listener);
      resolve(null);
    }, 3000);
  });
}

// ---------------------------------------------------------------------------
// Extract SSR data via Main World injection
// ---------------------------------------------------------------------------
function extractSSRData() {
  return new Promise((resolve) => {
    const requestId = Date.now().toString();

    const listener = (event) => {
      if (
        event.source === window &&
        event.data &&
        event.data.source === MAIN_WORLD_SOURCE &&
        event.data.requestId === requestId &&
        event.data.type === "XHS_SSR_DATA_RESULT"
      ) {
        window.removeEventListener("message", listener);
        resolve(event.data.data || null);
      }
    };
    window.addEventListener("message", listener);

    // Ask Main World to extract SSR data
    window.postMessage({
      source: CONTENT_SOURCE,
      type: "XHS_EXTRACT_SSR",
      requestId: requestId
    }, "*");

    // Also try inline injection as a fallback (in case Main World script
    // hasn't loaded yet or doesn't handle the message)
    const script = document.createElement("script");
    script.textContent = `
      (function() {
        var requestId = "${requestId}";
        var data = null;

        // XHS stores SSR data in __INIT_PROPS__ or __INITIAL_STATE__
        if (window.__INIT_PROPS__) {
          data = window.__INIT_PROPS__;
        } else if (window.__INITIAL_STATE__) {
          data = window.__INITIAL_STATE__;
        }

        window.postMessage({
          source: "${MAIN_WORLD_SOURCE}",
          type: "XHS_SSR_DATA_RESULT",
          requestId: requestId,
          data: data
        }, "*");
      })();
    `;
    document.documentElement.appendChild(script);
    script.remove();

    // 3-second timeout
    setTimeout(() => {
      window.removeEventListener("message", listener);
      resolve(null);
    }, 3000);
  });
}

// ---------------------------------------------------------------------------
// Get signature from Main World
// ---------------------------------------------------------------------------
function getSignatureFromMainWorld(url) {
  return new Promise((resolve) => {
    const requestId = Date.now().toString();

    const listener = (event) => {
      if (
        event.source === window &&
        event.data &&
        event.data.source === MAIN_WORLD_SOURCE &&
        event.data.requestId === requestId &&
        event.data.type === "XHS_SIGNATURE_RESULT"
      ) {
        window.removeEventListener("message", listener);
        resolve(event.data.signature || null);
      }
    };
    window.addEventListener("message", listener);

    // Ask Main World for signature
    window.postMessage({
      source: CONTENT_SOURCE,
      type: "XHS_GET_SIGNATURE",
      requestId: requestId,
      url: url
    }, "*");

    // Also try inline injection as fallback
    const script = document.createElement("script");
    script.textContent = `
      (function() {
        var requestId = "${requestId}";
        var url = "${url.replace(/"/g, '\\"')}";
        var signature = null;

        try {
          // XHS uses _webmsxyw for X-s and X-t signature generation
          if (window._webmsxyw) {
            signature = window._webmsxyw(url);
          } else if (window._sign) {
            signature = window._sign(url);
          }
        } catch(e) {}

        window.postMessage({
          source: "${MAIN_WORLD_SOURCE}",
          type: "XHS_SIGNATURE_RESULT",
          requestId: requestId,
          signature: signature
        }, "*");
      })();
    `;
    document.documentElement.appendChild(script);
    script.remove();

    // 3-second timeout
    setTimeout(() => {
      window.removeEventListener("message", listener);
      resolve(null);
    }, 3000);
  });
}

// ---------------------------------------------------------------------------
// 3. DOM Parsing Fallback
// ---------------------------------------------------------------------------

// Parse search result pages (xiaohongshu.com/search_result*)
function parseSearchResultsFromDOM() {
  const results = [];

  // Strategy 1: note-item elements with data-note-id
  const noteItems = document.querySelectorAll(
    'section.note-item, div.note-item, [data-note-id]'
  );

  if (noteItems.length > 0) {
    noteItems.forEach((item) => {
      const noteId =
        item.getAttribute("data-note-id") ||
        (item.querySelector("[data-note-id]")
          ? item.querySelector("[data-note-id]").getAttribute("data-note-id")
          : "");

      const titleEl = item.querySelector(
        '[class*="title"], [class*="desc"], .title, .note-content, footer span'
      );
      const authorEl = item.querySelector(
        '[class*="author"], [class*="name"], .author-wrapper span, .author .name'
      );
      const likeEl = item.querySelector(
        '[class*="like"], [class*="count"], .like-wrapper span, .engagement span'
      );
      const coverEl = item.querySelector("img");

      results.push({
        note_id: noteId || "",
        title: titleEl?.textContent?.trim() || "",
        author: authorEl?.textContent?.trim() || "",
        like_count: likeEl ? parseFormattedNumber(likeEl.textContent) : 0,
        cover_url: coverEl?.src || coverEl?.getAttribute("data-src") || ""
      });
    });
  }

  // Strategy 2: fallback — look for note links in feeds
  if (results.length === 0) {
    const noteLinks = document.querySelectorAll(
      'a[href*="/explore/"], a[href*="/discovery/item/"], a[href*="/search_result/"]'
    );

    noteLinks.forEach((link) => {
      const href = link.getAttribute("href") || "";
      const noteIdMatch =
        href.match(/\/explore\/([a-f0-9]+)/) ||
        href.match(/\/discovery\/item\/([a-f0-9]+)/) ||
        href.match(/noteId=([a-f0-9]+)/);
      const noteId = noteIdMatch ? noteIdMatch[1] : "";

      if (!noteId) return;

      const card = link.closest("section, div[class*=note], div[class*=card]");
      if (!card) return;

      const titleEl = card.querySelector(
        '[class*="title"], [class*="desc"], .title, footer span'
      );
      const authorEl = card.querySelector(
        '[class*="author"], [class*="name"], .author-wrapper span'
      );
      const likeEl = card.querySelector(
        '[class*="like"], [class*="count"], .like-wrapper span'
      );
      const coverEl = card.querySelector("img");

      results.push({
        note_id: noteId,
        title: titleEl?.textContent?.trim() || "",
        author: authorEl?.textContent?.trim() || "",
        like_count: likeEl ? parseFormattedNumber(likeEl.textContent) : 0,
        cover_url: coverEl?.src || coverEl?.getAttribute("data-src") || ""
      });
    });
  }

  return results.filter((n) => n.note_id);
}

// Parse note detail pages (xiaohongshu.com/explore/* or /discovery/item/*)
function parseNoteDetailFromDOM() {
  const url = window.location.href;
  const noteIdMatch =
    url.match(/\/explore\/([a-f0-9]+)/) ||
    url.match(/\/discovery\/item\/([a-f0-9]+)/);
  const noteId = noteIdMatch ? noteIdMatch[1] : "";

  // Title
  const titleEl = document.querySelector(
    '#detail-title, [class*="title"], .note-content .title'
  );

  // Description / body
  const descEl = document.querySelector(
    '#detail-desc, [class*="desc"], .note-content .desc, .note-text span'
  );

  // Author
  const authorEl = document.querySelector(
    '[class*="author"] [class*="name"], [class*="username"], .user-nickname, .author-wrapper .name'
  );
  const authorIdEl = document.querySelector(
    'a[href*="/user/profile/"]'
  );
  const authorIdMatch = authorIdEl
    ? (authorIdEl.getAttribute("href") || "").match(/\/user\/profile\/([a-f0-9]+)/)
    : null;

  // Interaction stats
  const likeEl = document.querySelector(
    '[class*="like"] [class*="count"], [class*="like-wrapper"] span, .engagement-bar [class*="like"]'
  );
  const collectEl = document.querySelector(
    '[class*="collect"] [class*="count"], [class*="star-wrapper"] span, .engagement-bar [class*="collect"]'
  );
  const commentEl = document.querySelector(
    '[class*="comment"] [class*="count"], [class*="chat-wrapper"] span, .engagement-bar [class*="comment"]'
  );

  // Tags
  const tagEls = document.querySelectorAll(
    '[class*="tag"] a, #hash-tag a, .tag span'
  );
  const tags = Array.from(tagEls)
    .map((el) => el.textContent?.trim().replace(/^#/, ""))
    .filter(Boolean);

  // Images
  const imageEls = document.querySelectorAll(
    '.note-content img, .swiper-slide img, [class*="carousel"] img'
  );
  const images = Array.from(imageEls)
    .map((img) => img.src || img.getAttribute("data-src"))
    .filter(Boolean);

  return {
    note_id: noteId,
    title: titleEl?.textContent?.trim() || "",
    description: descEl?.textContent?.trim() || "",
    author: {
      nickname: authorEl?.textContent?.trim() || "",
      user_id: authorIdMatch ? authorIdMatch[1] : ""
    },
    statistics: {
      like_count: likeEl ? parseFormattedNumber(likeEl.textContent) : 0,
      collect_count: collectEl ? parseFormattedNumber(collectEl.textContent) : 0,
      comment_count: commentEl ? parseFormattedNumber(commentEl.textContent) : 0
    },
    tags: tags,
    images: images
  };
}

// ---------------------------------------------------------------------------
// 4. Auto-extract on Page Load
// ---------------------------------------------------------------------------
(async function autoExtract() {
  try {
    const ssrData = await extractSSRData();
    if (ssrData) {
      chrome.runtime.sendMessage({
        action: "XHS_SSR_DATA",
        requestId: "auto-" + Date.now(),
        data: ssrData
      });
    }
  } catch (err) {
    // Silently ignore — passive collection should not disrupt the page
  }
})();
