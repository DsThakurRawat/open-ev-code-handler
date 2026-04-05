import { useEffect, useRef } from "react";
import { useEventStore } from "../stores/eventStore";
export function useWebSocket() {
    const { push, setConnected } = useEventStore();
    const reconnectTimeout = useRef(null);
    useEffect(() => {
        let socket = null;
        let isMounted = true;
        function connect() {
            if (reconnectTimeout.current)
                clearTimeout(reconnectTimeout.current);
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const host = import.meta.env.DEV ? "localhost:7860" : window.location.host;
            const url = `${protocol}//${host}/ws/events`;
            socket = new WebSocket(url);
            socket.onopen = () => {
                if (!isMounted)
                    return;
                setConnected(true);
                console.log("WebSocket connected");
            };
            socket.onmessage = (event) => {
                if (!isMounted)
                    return;
                try {
                    const data = JSON.parse(event.data);
                    push({
                        ...data,
                        timestamp: new Date().toISOString(),
                    });
                }
                catch (err) {
                    console.error("Failed to parse WS message", err);
                }
            };
            socket.onclose = () => {
                if (!isMounted)
                    return;
                setConnected(false);
                console.log("WebSocket closed, reconnecting in 3s...");
                reconnectTimeout.current = setTimeout(connect, 3000);
            };
            socket.onerror = (err) => {
                console.error("WebSocket error", err);
                socket?.close();
            };
        }
        connect();
        return () => {
            isMounted = false;
            if (reconnectTimeout.current)
                clearTimeout(reconnectTimeout.current);
            socket?.close();
        };
    }, [push, setConnected]);
}
