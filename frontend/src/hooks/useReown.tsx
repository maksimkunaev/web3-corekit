"use client";

import {
    useAppKit,
    useAppKitAccount,
    useDisconnect,
    useAppKitState,
} from "@reown/appkit/react";
import { useEffect, useState } from "react";
import { BASE_URL } from "@/configs/baseConfig";
import { siweEvents } from "@/components/AppKitProvider";

interface SessionData {
    address: string;
    chains: string[];
}

export function useReown() {
    const [session, setSession] = useState<SessionData | null>(null);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [isCheckingSession, setIsCheckingSession] = useState(false);
    const [tokenBalance, setTokenBalance] = useState<number | null>(null);
    const [tokenSymbol, setTokenSymbol] = useState<string>("$TOKEN");

    const { open, close } = useAppKit();
    const { disconnect } = useDisconnect();
    const { address, isConnected, caipAddress, status } = useAppKitAccount();

    const persistSessionId = (id: string | null) => {
        if (typeof window !== "undefined") {
            if (id) window.localStorage.setItem("siwe_session_id", id);
            else window.localStorage.removeItem("siwe_session_id");
        }
        setSessionId(id);
    };

    const checkSession = async () => {
        setIsCheckingSession(true);
        try {
            const res = await fetch(`${BASE_URL}/api/session`, { credentials: "include" });
            if (res.ok) {
                const data = await res.json();
                setSession(data.session);
                return data.session;
            } else {
                setSession(null);
                return null;
            }
        } catch {
            setSession(null);
            return null;
        } finally {
            setIsCheckingSession(false);
        }
    };

    const connect = () => open();

    // Listen for SIWE events
    useEffect(() => {
        const handleSignIn = () => checkSession();
        const handleSignOut = () => {
            persistSessionId(null);
            setSession(null);
        };
        siweEvents.on("siwe:signed-in", handleSignIn);
        siweEvents.on("siwe:signed-out", handleSignOut);
        return () => {
            siweEvents.off("siwe:signed-in", handleSignIn);
            siweEvents.off("siwe:signed-out", handleSignOut);
        };
    }, []);

    // Check session when wallet connects
    useEffect(() => {
        if (isConnected) checkSession();
        else setSession(null);
    }, [isConnected]);

    // Fetch token balance when authenticated
    const fetchTokenBalance = async () => {
        try {
            const res = await fetch(`${BASE_URL}/api/balance`, { credentials: "include" });
            if (res.ok) {
                const data = await res.json();
                setTokenBalance(data.balance);
                if (data.symbol) setTokenSymbol(data.symbol);
            }
        } catch (e) {
            console.error("Error fetching balance:", e);
        }
    };

    useEffect(() => {
        if (session && isConnected) fetchTokenBalance();
        else setTokenBalance(null);
    }, [session, isConnected]);

    // Disconnect wallet + backend session
    const disconnectWallet = async () => {
        try {
            if (sessionId) {
                await fetch(`${BASE_URL}/api/signout`, {
                    method: "POST",
                    credentials: "include",
                });
            }
        } catch (e) {
            console.error("Error disconnecting:", e);
        } finally {
            persistSessionId(null);
            disconnect();
            setSession(null);
        }
    };

    // Chain ID helpers
    const { selectedNetworkId } = useAppKitState();
    const getChainId = () => {
        if (selectedNetworkId) {
            const parts = selectedNetworkId.split(":");
            return parts.length > 1 ? parts[1] : selectedNetworkId;
        }
        if (caipAddress) {
            const parts = caipAddress.split(":");
            return parts.length > 2 ? parts[1] : null;
        }
        if (session?.chains?.[0]) return session.chains[0];
        return null;
    };

    return {
        address,
        isConnected,
        caipAddress,
        status,
        tokenBalance,
        tokenSymbol,
        chainId: getChainId(),
        session,
        isCheckingSession,
        isAuthenticated: !!session,
        connect,
        disconnect: disconnectWallet,
        checkSession,
        persistSessionId,
        openModal: open,
        closeModal: close,
    };
}
