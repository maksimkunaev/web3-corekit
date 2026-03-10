"use client";

import { createAppKit } from "@reown/appkit/react";
import { arbitrum, mainnet } from "@reown/appkit/networks";
import { createSIWEConfig, formatMessage } from "@reown/appkit-siwe";
import { BASE_URL } from "@/configs/baseConfig";
import {
    PROJECT_ID,
    APP_NAME,
    APP_DESCRIPTION,
    APP_URL,
    APP_ICONS,
    DOMAIN,
    CHAINS,
    SIWE_STATEMENT,
} from "@/configs/reownConfig";
import { WagmiProvider } from "wagmi";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiAdapter } from "@reown/appkit-adapter-wagmi";

// Simple event emitter for SIWE events
class SIWEEventEmitter {
    private listeners: { [key: string]: Function[] } = {};

    on(event: string, callback: Function) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(callback);
    }

    off(event: string, callback: Function) {
        if (!this.listeners[event]) return;
        this.listeners[event] = this.listeners[event].filter((cb) => cb !== callback);
    }

    emit(event: string, ...args: any[]) {
        if (!this.listeners[event]) return;
        this.listeners[event].forEach((callback) => callback(...args));
    }
}

export const siweEvents = new SIWEEventEmitter();

const queryClient = new QueryClient();
const providers = [mainnet, arbitrum];

const wagmiAdapter = new WagmiAdapter({
    networks: providers,
    projectId: PROJECT_ID,
    ssr: false,
});

const siweConfig = createSIWEConfig({
    getMessageParams: async () => ({
        domain: DOMAIN,
        uri: APP_URL,
        chains: CHAINS,
        statement: SIWE_STATEMENT,
    }),
    createMessage: ({ address, ...args }) => {
        const cleanAddress = address.startsWith("did:pkh:eip155:")
            ? address.split(":").pop()
            : address;
        return formatMessage(args, cleanAddress!);
    },
    getNonce: async () => {
        const res = await fetch(`${BASE_URL}/api/nonce`, { credentials: "include" });
        const data = await res.json();
        return data?.nonce;
    },
    getSession: async () => {
        try {
            const res = await fetch(`${BASE_URL}/api/session`, { credentials: "include" });
            if (!res.ok) return null;
            const data = await res.json();
            return {
                address: data.session.address,
                chainId: parseInt(data.session.chains[0]),
            };
        } catch {
            return null;
        }
    },
    verifyMessage: async ({ message, signature }) => {
        try {
            const res = await fetch(`${BASE_URL}/api/verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ message, signature }),
            });
            const data = await res.json();
            return data.valid;
        } catch {
            return false;
        }
    },
    signOut: async () => {
        try {
            const res = await fetch(`${BASE_URL}/api/signout`, {
                method: "POST",
                credentials: "include",
            });
            const data = await res.json();
            return data.success;
        } catch {
            return false;
        }
    },
    onSignIn: (session) => {
        siweEvents.emit("siwe:signed-in", session);
    },
    onSignOut: () => {
        siweEvents.emit("siwe:signed-out");
    },
});

createAppKit({
    adapters: [wagmiAdapter],
    // @ts-ignore
    networks: providers,
    projectId: PROJECT_ID,
    metadata: {
        name: APP_NAME,
        description: APP_DESCRIPTION,
        url: APP_URL,
        icons: APP_ICONS,
    },
    siweConfig,
    features: {
        analytics: false,
        email: false,
        socials: false,
        emailShowWallets: false,
    },
    enableAnalytics: false,
});

export default function AppKitProvider({ children }: { children: React.ReactNode }) {
    return (
        <WagmiProvider config={wagmiAdapter.wagmiConfig}>
            <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
        </WagmiProvider>
    );
}
