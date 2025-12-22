export const WS_STATE = {
  DISCONNECTED: "DISCONNECTED",
  CONNECTING: "CONNECTING",
  CONNECTED: "CONNECTED",
  RECONNECTING: "RECONNECTING",
};

export class GameWebSocket {
  constructor({ onOpen, onClose, onMessage, onError, onStatusChange } = {}) {
    this.ws = null;
    this.state = WS_STATE.DISCONNECTED;
    this.onOpen = onOpen || (() => {});
    this.onClose = onClose || (() => {});
    this.onMessage = onMessage || (() => {});
    this.onError = onError || (() => {});
    this.onStatusChange = onStatusChange || (() => {});

    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.reconnectDelayBase = 2000;
    this.shouldReconnect = false;
    this.lastToken = "";
    this.heartbeatTimer = null;
  }

  _updateState(next) {
    if (this.state === next) return;
    this.state = next;
    this.onStatusChange(next);
  }

  _buildUrl(token) {
    const protocol = location.protocol === "https:" ? "wss://" : "ws://";
    return `${protocol}${location.host}/ws?token=${encodeURIComponent(token)}`;
  }

  connect(token) {
    if (!token) {
      this.onError(new Error("缺少 token，无法连接 WebSocket"));
      return;
    }
    if (this.ws && (this.state === WS_STATE.CONNECTED || this.state === WS_STATE.CONNECTING)) {
      return;
    }

    this.lastToken = token;
    this.shouldReconnect = true;
    this._updateState(this.reconnectAttempts > 0 ? WS_STATE.RECONNECTING : WS_STATE.CONNECTING);

    const url = this._buildUrl(token);
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this._updateState(WS_STATE.CONNECTED);
      this.onOpen();
      this._startHeartbeat();
    };

    this.ws.onclose = (event) => {
      this._stopHeartbeat();
      const wasConnected = this.state === WS_STATE.CONNECTED;
      this.ws = null;
      this._updateState(WS_STATE.DISCONNECTED);
      this.onClose(event);

      // 1000 正常关闭; 1008 无效 token / 权限; 1011 服务器错误
      if (!this.shouldReconnect) return;
      if (event && (event.code === 1008 || event.code === 4001)) {
        // 明确的权限 / token 问题，不要再重连
        this.shouldReconnect = false;
        return;
      }

      if (wasConnected && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts += 1;
        const delay = this.reconnectDelayBase * this.reconnectAttempts;
        setTimeout(() => {
          if (this.shouldReconnect && this.lastToken) {
            this.connect(this.lastToken);
          }
        }, delay);
      }
    };

    this.ws.onerror = (event) => {
      this.onError(event);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onMessage(data);
      } catch {
        this.onMessage({ type: "raw", data: event.data });
      }
    };
  }

  disconnect() {
    this.shouldReconnect = false;
    this._stopHeartbeat();
    if (this.ws) {
      try {
        this.ws.close(1000, "client disconnect");
      } catch {
        // ignore
      }
      this.ws = null;
    }
    this._updateState(WS_STATE.DISCONNECTED);
  }

  _startHeartbeat() {
      this._stopHeartbeat();
      // 发送轻量 stats 命令作为心跳，间隔 45s
      this.heartbeatTimer = setInterval(() => {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        try {
          this.sendCommand("stats");
        } catch {
          // ignore, reconnect logic will handle failures
        }
      }, 45000);
  }

  _stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  sendCommand(cmd) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket 未连接");
    }
    const payload = { action: "command", data: cmd };
    this.ws.send(JSON.stringify(payload));
  }
}


