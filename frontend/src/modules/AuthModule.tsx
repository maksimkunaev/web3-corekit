// modules/AuthModule.tsx
// Module 1 Frontend: Login button + session status display
// Self-contained auth demo using useReown hook

"use client";

import React from "react";
import { useReown } from "@/hooks/useReown";

const styles: Record<string, React.CSSProperties> = {
    container: {
        padding: "2rem",
        borderRadius: "var(--radius-card)",
        background: "var(--glass-bg)",
        backdropFilter: "var(--glass-blur)",
        WebkitBackdropFilter: "var(--glass-blur)",
        border: "1px solid var(--glass-border)",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4)",
        maxWidth: "440px",
        margin: "1rem auto",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        animation: "fadeInScale 0.4s ease-out forwards",
    },
    title: {
        fontSize: "1.25rem",
        fontWeight: 700,
        color: "var(--text-main)",
        textAlign: "left",
        letterSpacing: "-0.01em",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        paddingBottom: "0.75rem",
    },
    status: {
        padding: "1rem",
        borderRadius: "var(--radius-inner)",
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.04)",
        fontSize: "0.85rem",
        color: "var(--text-muted)",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
    },
    statusRow: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
    },
    address: {
        fontSize: "0.75rem",
        fontFamily: "'Inter', monospace",
        color: "var(--text-dim)",
        background: "rgba(0,0,0,0.3)",
        padding: "2px 6px",
        borderRadius: "4px",
    },
    button: {
        padding: "0.75rem 1.25rem",
        borderRadius: "var(--radius-btn)",
        border: "none",
        fontWeight: 600,
        fontSize: "0.9rem",
        cursor: "pointer",
        transition: "all 0.2s ease",
    },
    connectBtn: {
        background: "var(--accent-primary)",
        color: "white",
    },
    disconnectBtn: {
        background: "transparent",
        color: "var(--text-muted)",
        border: "1px solid rgba(255,255,255,0.1)",
    },
    badge: {
        padding: "2px 8px",
        borderRadius: "4px",
        fontSize: "0.65rem",
        fontWeight: 700,
        textTransform: "uppercase",
    },
    connected: {
        background: "rgba(34, 197, 94, 0.1)",
        color: "#4ade80",
    },
    disconnected: {
        background: "rgba(245, 158, 11, 0.1)",
        color: "#fbbf24",
    },
};

export default function AuthModule() {
    const { address, isConnected, isAuthenticated, session, connect, disconnect, status } = useReown();

    return (
        <div style={styles.container}>
            <div style={styles.title} className="font-heading">Authentication</div>

            <div style={styles.status}>
                <div style={styles.statusRow}>
                    <span>State</span>
                    <span style={{ ...styles.badge, ...(isAuthenticated ? styles.connected : styles.disconnected) }}>
                        {isAuthenticated ? "Session Active" : status || "No Wallet"}
                    </span>
                </div>
                {address && (
                    <div style={styles.statusRow}>
                        <span>Address</span>
                        <span style={styles.address}>
                            {address.slice(0, 6)}...{address.slice(-4)}
                        </span>
                    </div>
                )}
                {session && (
                    <div style={styles.statusRow}>
                        <span>Network</span>
                        <span>{session.chains?.[0] || "—"}</span>
                    </div>
                )}
            </div>

            {!isConnected ? (
                <button
                    style={{ ...styles.button, ...styles.connectBtn }}
                    onClick={connect}
                    className="btn-accent"
                >
                    Connect Wallet
                </button>
            ) : (
                <button
                    style={{ ...styles.button, ...styles.disconnectBtn }}
                    onClick={disconnect}
                >
                    Sign Out
                </button>
            )}
        </div>
    );
}
