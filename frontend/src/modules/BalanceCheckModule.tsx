// modules/BalanceCheckModule.tsx
// Module 3 Frontend: Token balance display + holder status
// Self-contained balance UI

"use client";

import React from "react";
import { useReown } from "@/hooks/useReown";

const s: Record<string, React.CSSProperties> = {
    container: {
        padding: "2rem",
        borderRadius: "var(--radius-card)",
        background: "var(--glass-bg)",
        backdropFilter: "var(--glass-blur)",
        WebkitBackdropFilter: "var(--glass-blur)",
        border: "1px solid var(--glass-border)",
        maxWidth: "440px",
        margin: "1rem auto",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
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
    balanceRow: {
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "1rem",
        borderRadius: "var(--radius-inner)",
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.04)",
    },
    label: {
        fontSize: "0.85rem",
        color: "var(--text-muted)",
        fontWeight: 500,
    },
    value: {
        fontSize: "1.1rem",
        fontWeight: 700,
        color: "var(--text-main)",
        fontFamily: "'Inter', sans-serif",
    },
    notConnected: {
        textAlign: "center",
        color: "var(--text-dim)",
        fontSize: "0.85rem",
        padding: "1rem",
        background: "rgba(0,0,0,0.1)",
        borderRadius: "var(--radius-inner)",
    },
};

export default function BalanceCheckModule() {
    const { isAuthenticated, tokenBalance, tokenSymbol } = useReown();

    if (!isAuthenticated) {
        return (
            <div style={s.container}>
                <div style={s.title}>💰 Token Balance</div>
                <div style={s.notConnected}>Connect wallet to view balance</div>
            </div>
        );
    }

    return (
        <div style={s.container}>
            <div style={s.title} className="font-heading">Token Balance</div>

            <div style={s.balanceRow}>
                <span style={s.label}>Amount</span>
                <span style={s.value}>
                    {tokenBalance !== null ? tokenBalance.toLocaleString() : "0"}
                </span>
            </div>

            <div style={s.balanceRow}>
                <span style={s.label}>Asset</span>
                <span style={{ ...s.value, fontSize: "0.9rem", color: "var(--accent-primary)" }}>
                    {tokenSymbol}
                </span>
            </div>
        </div>
    );
}
