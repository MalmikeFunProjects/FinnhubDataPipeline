import { renderHook, act } from "@testing-library/react";
import { useJsonWebSocket } from "./useJsonWebSocket";

jest.mock("global", () => ({
    ...global,
    WebSocket: jest.fn(),
}));

describe("useJsonWebSocket", () => {
    let mockWebSocket: jest.Mocked<WebSocket>;

    beforeEach(() => {
        mockWebSocket = {
            send: jest.fn(),
            close: jest.fn(),
            readyState: WebSocket.OPEN,
            onopen: null,
            onclose: null,
            onmessage: null,
            onerror: null,
        } as unknown as jest.Mocked<WebSocket>;

        (global.WebSocket as unknown as jest.Mock).mockImplementation(() => mockWebSocket);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it("should initialize with connecting status", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));
        expect(result.current.status).toBe("connecting");
    });

    it("should set status to open when WebSocket connection opens", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));

        act(() => {
            mockWebSocket.onopen?.(new Event("open"));
        });

        expect(result.current.status).toBe("open");
    });

    it("should set status to closed when WebSocket connection closes", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));

        act(() => {
            mockWebSocket.onclose?.(new CloseEvent("close"));
        });

        expect(result.current.status).toBe("closed");
    });

    it("should handle incoming messages and update messages state", () => {
        const { result } = renderHook(() => useJsonWebSocket<{ message: string }>("ws://test-url"));

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
            useJsonWebSocket<{ message: string }>("ws://test-url", { onMessage })
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
            useJsonWebSocket<{}, { message: string }>("ws://test-url")
        );

        const messageToSend = { message: "Test message" };

        act(() => {
            result.current.sendMessage(messageToSend);
        });

        expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(messageToSend));
    });

    it("should close the WebSocket connection when disconnect is called", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));

        act(() => {
            result.current.disconnect();
        });

        expect(mockWebSocket.close).toHaveBeenCalled();
        expect(result.current.status).toBe("closed");
    });

    it("should reconnect when reconnect is called", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));

        act(() => {
            result.current.reconnect();
        });

        expect(mockWebSocket.close).toHaveBeenCalled();
        expect(global.WebSocket).toHaveBeenCalledWith("ws://test-url", undefined);
    });

    it("should add a connection query and reconnect", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));

        act(() => {
            result.current.addConnectionQuery("token=123");
        });

        expect(global.WebSocket).toHaveBeenCalledWith("ws://test-url?token=123", undefined);
    });

    it("should clear the connection query and reconnect", () => {
        const { result } = renderHook(() => useJsonWebSocket("ws://test-url"));

        act(() => {
            result.current.addConnectionQuery("token=123");
            result.current.clearConnectionQuery();
        });

        expect(global.WebSocket).toHaveBeenCalledWith("ws://test-url", undefined);
    });

    it("should clear messages", () => {
        const { result } = renderHook(() => useJsonWebSocket<{ message: string }>("ws://test-url"));

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
});
