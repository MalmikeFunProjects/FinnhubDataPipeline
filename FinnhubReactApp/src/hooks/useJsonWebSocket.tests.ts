import { renderHook, act } from "@testing-library/react";
import { useJsonWebSocket } from "./useJsonWebSocket";

describe("useJsonWebSocket", () => {
    let mockWebSocket: jest.Mocked<WebSocket>;
    const TEST_URL = 'ws://test-url';
    let originalSetTimeout: any = (global as any).setTimeout;

    beforeEach(() => {
        (global as any).setTimeout = originalSetTimeout
        mockWebSocket = {
            send: jest.fn(),
            close: jest.fn(),
            readyState: WebSocket.OPEN,
            onopen: null,
            onclose: null,
            onmessage: null,
            onerror: null,
        } as unknown as jest.Mocked<WebSocket>;
        (global as any).WebSocket = jest.fn().mockImplementation(() => mockWebSocket);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it("should initialize with connecting status", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));
        expect(result.current.status).toBe("connecting");
    });

    it("should set status to open when WebSocket connection opens", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));

        act(() => {
            mockWebSocket.onopen?.(new Event("open"));
        });

        expect(result.current.status).toBe("open");
    });

    it("should set status to closed when WebSocket connection closes", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));

        act(() => {
            mockWebSocket.onclose?.(new CloseEvent("close"));
        });

        expect(result.current.status).toBe("closed");
    });

    it("should handle incoming messages and update messages state", () => {
        const { result } = renderHook(() => useJsonWebSocket<{ message: string }>(TEST_URL));

        const mockMessage = { message: "Hello, WebSocket!" };

        act(() => {
            mockWebSocket.onmessage?.(
                new MessageEvent("message", { data: JSON.stringify(mockMessage) })
            );
        });

        expect(result.current.messages).toEqual([mockMessage]);
    });

    it("should call onMessage callback when a message is received", () => {
        const onMessage = jest.fn();
        renderHook(() =>
            useJsonWebSocket<{ message: string }>(TEST_URL, { onMessage })
        );

        const mockMessage = { message: "Hello, WebSocket!" };

        act(() => {
            mockWebSocket.onmessage?.(
                new MessageEvent("message", { data: JSON.stringify(mockMessage) })
            );
        });

        expect(onMessage).toHaveBeenCalledWith(mockMessage, expect.any(MessageEvent));
    });

    it("should send a message through the WebSocket", () => {
        const { result } = renderHook(() =>
            useJsonWebSocket<{}, { message: string }>(TEST_URL)
        );

        const messageToSend = { message: "Test message" };

        act(() => {
            result.current.sendMessage(messageToSend);
        });

        expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(messageToSend));
    });

    it("should close the WebSocket connection when disconnect is called", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));

        act(() => {
            result.current.disconnect();
        });

        expect(mockWebSocket.close).toHaveBeenCalled();
        expect(result.current.status).toBe("closed");
    });

    it("should reconnect when reconnect is called", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));

        act(() => {
            result.current.reconnect();
        });

        expect(mockWebSocket.close).toHaveBeenCalled();
        expect(global.WebSocket).toHaveBeenCalledWith(TEST_URL, undefined);
    });

    it("should add a connection query and reconnect", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));

        act(() => {
            result.current.addConnectionQuery("token=123");
        });

        expect(global.WebSocket).toHaveBeenCalledWith(`${TEST_URL}?token=123`, undefined);
    });

    it("should clear the connection query and reconnect", () => {
        const { result } = renderHook(() => useJsonWebSocket(TEST_URL));

        act(() => {
            result.current.addConnectionQuery("token=123");
            result.current.clearConnectionQuery();
        });

        expect(global.WebSocket).toHaveBeenCalledWith(TEST_URL, undefined);
    });

    it("should clear messages", () => {
        const { result } = renderHook(() => useJsonWebSocket<{ message: string }>(TEST_URL));

        const mockMessage = { message: "Hello, WebSocket!" };

        act(() => {
            mockWebSocket.onmessage?.(
                new MessageEvent("message", { data: JSON.stringify(mockMessage) })
            );
        });

        expect(result.current.messages).toEqual([mockMessage]);

        act(() => {
            result.current.clearMessages();
        });

        expect(result.current.messages).toEqual([]);
    });

    it("should attempt to reconnect when the connection is closed and reconnectAttempts is greater than 0", () => {
        jest.useFakeTimers();
        const reconnectAttempts = 2;
        const reconnectInterval = 1000;

        renderHook(() =>
            useJsonWebSocket(TEST_URL, { reconnectAttempts, reconnectInterval })
        );

        act(() => {
            mockWebSocket.onclose?.(new CloseEvent("close"));
        });

        act(() => {
            jest.runOnlyPendingTimers();
        });

        expect(global.WebSocket).toHaveBeenCalledTimes(2);

        act(() => {
            mockWebSocket.onclose?.(new CloseEvent("close"));
            jest.runOnlyPendingTimers();
        });

        expect(global.WebSocket).toHaveBeenCalledTimes(3);

        jest.useRealTimers();
    });

    it("should not attempt to reconnect when reconnectAttempts is 0", () => {
        jest.useFakeTimers();
        (global as any).setTimeout = jest.fn(global.setTimeout);

        renderHook(() =>
            useJsonWebSocket(TEST_URL, { reconnectAttempts: 0})
        );

        act(() => {
            mockWebSocket.onclose?.(new CloseEvent("close"));
        });

        expect(setTimeout).not.toHaveBeenCalled();
        jest.useRealTimers();
    });

    it("should call onOpen callback when WebSocket connection opens", () => {
        const onOpen = jest.fn();
        renderHook(() => useJsonWebSocket(TEST_URL, { onOpen }));

        act(() => {
            mockWebSocket.onopen?.(new Event("open"));
        });

        expect(onOpen).toHaveBeenCalledWith(expect.any(Event));
    });

    it("should call onClose callback when WebSocket connection closes", () => {
        const onClose = jest.fn();
        renderHook(() => useJsonWebSocket(TEST_URL, { onClose }));

        act(() => {
            mockWebSocket.onclose?.(new CloseEvent("close"));
        });

        expect(onClose).toHaveBeenCalledWith(expect.any(CloseEvent));
    });

    it("should call onError callback when WebSocket encounters an error", () => {
        const onError = jest.fn();
        renderHook(() => useJsonWebSocket(TEST_URL, { onError }));

        act(() => {
            mockWebSocket.onerror?.(new Event("error"));
        });

        expect(onError).toHaveBeenCalledWith(expect.any(Event));
    });
});
