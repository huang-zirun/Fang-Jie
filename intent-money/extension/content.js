const EXTENSION_ID = chrome.runtime.id;

window.addEventListener("message", async (event) => {
  if (event.data && event.data.source === "intent-money-extension") return;

  const { type, payload, requestId } = event.data || {};

  const handlers = {
    INTENT_MONEY_PING: async () => {
      window.postMessage(
        { source: "intent-money-extension", type: "INTENT_MONEY_PONG", requestId: requestId },
        "*"
      );
    },

    INTENT_MONEY_GET_COOKIES: async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "GET_COOKIES",
          platform: payload?.platform || "xiaohongshu"
        });
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_COOKIES_RESULT",
            requestId: requestId,
            success: response.success,
            cookies: response.cookies,
            error: response.error
          },
          "*"
        );
      } catch (err) {
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_COOKIES_RESULT",
            requestId: requestId,
            success: false,
            error: err.message
          },
          "*"
        );
      }
    },

    INTENT_MONEY_OPEN_LOGIN: async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "OPEN_LOGIN",
          platform: payload?.platform || "xiaohongshu"
        });
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_OPEN_LOGIN_RESULT",
            requestId: requestId,
            success: response.success,
            error: response.error
          },
          "*"
        );
      } catch (err) {
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_OPEN_LOGIN_RESULT",
            requestId: requestId,
            success: false,
            error: err.message
          },
          "*"
        );
      }
    },

    INTENT_MONEY_CHECK_LOGIN: async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "CHECK_LOGIN",
          platform: payload?.platform || "xiaohongshu"
        });
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_CHECK_LOGIN_RESULT",
            requestId: requestId,
            success: response.success,
            loggedIn: response.loggedIn,
            cookieName: response.cookieName,
            cookieExists: response.cookieExists,
            error: response.error
          },
          "*"
        );
      } catch (err) {
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_CHECK_LOGIN_RESULT",
            requestId: requestId,
            success: false,
            error: err.message
          },
          "*"
        );
      }
    },

    INTENT_MONEY_SET_CONFIG: async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "SET_CONFIG",
          serverUrl: payload?.serverUrl,
          authToken: payload?.authToken
        });
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_SET_CONFIG_RESULT",
            requestId: requestId,
            success: response.success,
            error: response.error
          },
          "*"
        );
      } catch (err) {
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_SET_CONFIG_RESULT",
            requestId: requestId,
            success: false,
            error: err.message
          },
          "*"
        );
      }
    },

    INTENT_MONEY_TRIGGER_POPUP: async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "TRIGGER_POPUP",
          platform: payload?.platform || "xiaohongshu"
        });
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_TRIGGER_POPUP_RESULT",
            requestId: requestId,
            success: response.success,
            error: response.error
          },
          "*"
        );
      } catch (err) {
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_TRIGGER_POPUP_RESULT",
            requestId: requestId,
            success: false,
            error: err.message
          },
          "*"
        );
      }
    },

    INTENT_MONEY_TRIGGER_SCRAPE: async () => {
      try {
        const response = await chrome.runtime.sendMessage({
          action: "SCRAPE_DOUYIN_SEARCH",
          keyword: payload?.keyword || "袜子",
          platform_id: payload?.platform_id || "",
          limit: payload?.limit || 20
        });
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_SCRAPE_RESULT",
            requestId: requestId,
            success: response.success,
            videos: response.videos,
            source: response.source,
            keyword: response.keyword,
            error: response.error
          },
          "*"
        );
      } catch (err) {
        window.postMessage(
          {
            source: "intent-money-extension",
            type: "INTENT_MONEY_SCRAPE_RESULT",
            requestId: requestId,
            success: false,
            error: err.message
          },
          "*"
        );
      }
    }
  };

  const handler = handlers[type];
  if (handler) {
    handler();
  }
});

// Listen for status updates from background script and forward to page
chrome.runtime.onMessage.addListener((message) => {
  if (message.action === "STATUS_UPDATE") {
    window.postMessage(
      {
        source: "intent-money-extension",
        type: "INTENT_MONEY_STATUS_UPDATE",
        platform: message.platform,
        loggedIn: message.loggedIn,
        cookieCount: message.cookieCount,
        timestamp: message.timestamp
      },
      "*"
    );
  }
});
