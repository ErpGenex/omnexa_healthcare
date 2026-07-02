/**
 * Telemedicine Realtime Client
 * Uses Frappe publish_realtime with optional polling fallback.
 */

class TelemedicineSocket {
    constructor(config = {}) {
        this.connected = false;
        this.sessionId = null;
        this.user = null;
        this.token = null;
        this.eventHandlers = {};
        this.realtimeHandlers = {};
        this.config = {
            poll_interval_ms: config.poll_interval_ms || 5000,
            ...config
        };
        this.pollingInterval = null;
        this.pollingActive = false;
    }

    async connect(user, sessionId = null) {
        try {
            const authResult = await this.getAuthToken(user, sessionId);
            if (!authResult.success) {
                console.error('Failed to get auth token:', authResult.error);
                return false;
            }

            this.token = authResult.token;
            this.user = user;
            this.sessionId = sessionId;

            if (typeof frappe !== 'undefined' && typeof frappe.realtime !== 'undefined') {
                this.setupRealtimeListeners();
                this.connected = true;
                this.emit('connected', { transport: 'frappe_realtime' });
                return true;
            }

            console.warn('Frappe realtime not available. Using polling fallback.');
            this.startFallbackPolling();
            this.connected = true;
            this.emit('connected', { transport: 'polling' });
            return true;
        } catch (error) {
            console.error('Realtime connection error:', error);
            return false;
        }
    }

    async getAuthToken(user, sessionId) {
        try {
            const response = await frappe.call({
                method: 'omnexa_healthcare.api.telemedicine_socket.get_socket_auth_token',
                args: { user, session_id: sessionId }
            });
            return response.message || { success: false, error: 'No response' };
        } catch (error) {
            console.error('Failed to get auth token:', error);
            return { success: false, error: error.message };
        }
    }

    setupRealtimeListeners() {
        const bindings = {
            telemedicine_session: 'session_status',
            telemedicine_queue: 'queue_update',
            telemedicine_chat: 'chat_message',
            telemedicine_device_alert: 'device_alert',
        };

        Object.entries(bindings).forEach(([event, handlerName]) => {
            const handler = (payload) => {
                if (handlerName === 'chat_message' && payload.message) {
                    this.emit('chat_message', payload.message);
                    return;
                }
                this.emit(handlerName, payload);
            };
            frappe.realtime.on(event, handler);
            this.realtimeHandlers[event] = handler;
        });
    }

    on(event, callback) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(callback);
    }

    off(event, callback) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event] = this.eventHandlers[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(callback => callback(data));
        }
    }

    joinSession(sessionId) {
        this.sessionId = sessionId;
    }

    leaveSession() {
        this.sessionId = null;
    }

    async sendChatMessage(sessionId, message) {
        try {
            const response = await frappe.call({
                method: 'omnexa_healthcare.api.telemedicine_socket.send_session_chat_message',
                args: { session_id: sessionId, message }
            });
            return response.message || { success: false };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    subscribeToQueue(practitioner) {
        this.practitioner = practitioner;
    }

    subscribeToDeviceAlerts(patient) {
        this.patient = patient;
    }

    disconnect() {
        if (typeof frappe !== 'undefined' && typeof frappe.realtime !== 'undefined') {
            Object.entries(this.realtimeHandlers).forEach(([event, handler]) => {
                frappe.realtime.off(event, handler);
            });
        }
        this.realtimeHandlers = {};
        this.stopFallbackPolling();
        this.connected = false;
        this.emit('disconnected');
    }

    startFallbackPolling() {
        this.pollingActive = true;
        this.pollQueue();
    }

    pollQueue() {
        if (!this.pollingActive) return;

        this.pollingInterval = setInterval(() => {
            if (this.sessionId) {
                frappe.call({
                    method: 'omnexa_healthcare.api.telemedicine.get_telemedicine_session',
                    args: { session_id: this.sessionId },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            this.emit('session_status', r.message.session);
                        }
                    }
                });
            }
        }, this.config.poll_interval_ms);
    }

    stopFallbackPolling() {
        this.pollingActive = false;
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}

window.TelemedicineSocket = TelemedicineSocket;
