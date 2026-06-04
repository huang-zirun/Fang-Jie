let currentPlatform = "xiaohongshu";

const platformBtns = document.querySelectorAll(".platform-btn");
const loginStatusEl = document.getElementById("loginStatus");
const cookieCountEl = document.getElementById("cookieCount");
const lastSyncEl = document.getElementById("lastSync");
const btnGetCookies = document.getElementById("btnGetCookies");
const btnOpenLogin = document.getElementById("btnOpenLogin");
const resultArea = document.getElementById("resultArea");
const serverUrlDisplay = document.getElementById("serverUrlDisplay");

platformBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    platformBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentPlatform = btn.dataset.platform;
    checkLoginStatus();
  });
});

btnGetCookies.addEventListener("click", async () => {
  btnGetCookies.disabled = true;
  btnGetCookies.textContent = "获取中...";
  showResult("正在获取Cookie...", "");

  try {
    const response = await chrome.runtime.sendMessage({
      action: "SYNC_COOKIES",
      platform: currentPlatform
    });

    if (response.success) {
      const count = response.cookies ? response.cookies.length : 0;
      cookieCountEl.textContent = count;
      const now = new Date().toLocaleTimeString("zh-CN");
      lastSyncEl.textContent = now;
      showResult(`同步成功! 共获取 ${count} 个Cookie`, "success");
    } else {
      showResult(`同步失败: ${response.error || "未知错误"}`, "error");
    }
  } catch (err) {
    showResult(`操作异常: ${err.message}`, "error");
  } finally {
    btnGetCookies.disabled = false;
    btnGetCookies.textContent = "获取Cookie并同步";
    checkLoginStatus();
  }
});

btnOpenLogin.addEventListener("click", async () => {
  btnOpenLogin.disabled = true;
  try {
    const response = await chrome.runtime.sendMessage({
      action: "OPEN_LOGIN",
      platform: currentPlatform
    });
    if (response.success) {
      showResult("已打开登录页面，请登录后重试获取Cookie", "");
    } else {
      showResult(`打开失败: ${response.error || "未知错误"}`, "error");
    }
  } catch (err) {
    showResult(`操作异常: ${err.message}`, "error");
  } finally {
    btnOpenLogin.disabled = false;
  }
});

async function checkLoginStatus() {
  loginStatusEl.innerHTML = '<span class="status-dot unknown"></span>检测中...';
  try {
    const response = await chrome.runtime.sendMessage({
      action: "CHECK_LOGIN",
      platform: currentPlatform
    });
    if (response.success) {
      if (response.cookieExists) {
        loginStatusEl.innerHTML = '<span class="status-dot online"></span>已登录';
      } else {
        loginStatusEl.innerHTML = '<span class="status-dot offline"></span>未登录';
      }
    } else {
      loginStatusEl.innerHTML = '<span class="status-dot offline"></span>检测失败';
    }
  } catch (err) {
    loginStatusEl.innerHTML = '<span class="status-dot offline"></span>检测异常';
  }
}

async function loadServerUrl() {
  try {
    const response = await chrome.runtime.sendMessage({ action: "GET_CONFIG" });
    if (response.success) {
      serverUrlDisplay.textContent = `服务器: ${response.config.serverUrl}`;
    } else {
      serverUrlDisplay.textContent = "服务器: 配置获取失败";
    }
  } catch (err) {
    serverUrlDisplay.textContent = "服务器: 通信异常";
  }
}

function showResult(message, type) {
  resultArea.textContent = message;
  resultArea.className = "result-area visible";
  if (type === "error") {
    resultArea.classList.add("error");
  } else if (type === "success") {
    resultArea.classList.add("success");
  }
}

checkLoginStatus();
loadServerUrl();
