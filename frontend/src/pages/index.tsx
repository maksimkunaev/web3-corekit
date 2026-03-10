// Demo page — shows all three modules side by side
// Remove any module import you don't need

"use client";

import dynamic from "next/dynamic";

const DynamicDemo = dynamic(() => Promise.resolve(DemoPage), { ssr: false });

function DemoPage() {
    const AppKitProvider = require("@/components/AppKitProvider").default;
    const AuthModule = require("@/modules/AuthModule").default;
    const CryptoPaymentModule = require("@/modules/CryptoPaymentModule").default;
    const BalanceCheckModule = require("@/modules/BalanceCheckModule").default;

    return (
        <AppKitProvider>
            <div style={{
                padding: "6rem 2rem",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "5rem",
            }}>
                <header style={{ textAlign: "center" }}>
                    <h1 style={{
                        color: "var(--text-main)",
                        fontSize: "3rem",
                        fontWeight: 800,
                        marginBottom: "0.75rem",
                        letterSpacing: "-0.04em",
                    }} className="font-heading animate-premium">
                        Web3<span style={{ color: "var(--accent-secondary)", fontWeight: 500 }}>Corekit</span>
                    </h1>
                    <p style={{
                        color: "var(--text-muted)",
                        fontSize: "1rem",
                        maxWidth: "500px",
                        margin: "0 auto",
                        lineHeight: 1.5,
                        opacity: 0.8,
                    }} className="animate-premium">
                        Industrial-grade modular components for Ethereum applications.
                        Minimal. Professional. Premium.
                    </p>
                </header>

                <main style={{
                    display: "grid",
                    gridTemplateColumns: "1fr",
                    gap: "4rem",
                    width: "100%",
                    maxWidth: "1000px",
                }}>
                    <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))",
                        gap: "2.5rem",
                    }}>
                        {/* Module 1: Auth */}
                        <div className="animate-premium">
                            <h2 style={sectionLabel}>Identity</h2>
                            <AuthModule />
                        </div>

                        {/* Module 3: Balance */}
                        <div className="animate-premium" style={{ animationDelay: '0.1s' }}>
                            <h2 style={sectionLabel}>Asset Ledger</h2>
                            <BalanceCheckModule />
                        </div>
                    </div>

                    {/* Module 2: Subscriptions */}
                    <div className="animate-premium" style={{ animationDelay: '0.2s' }}>
                        <h2 style={sectionLabel}>Subscription Engine</h2>
                        <CryptoPaymentModule />
                    </div>
                </main>

                <footer style={{ marginTop: "6rem", color: "var(--text-dim)", fontSize: "0.8rem", letterSpacing: "0.05em" }}>
                    COREKIT &copy; 2026 • SYSTEM VERSION 1.0.4
                </footer>
            </div>
        </AppKitProvider>
    );
}

const sectionLabel: React.CSSProperties = {
    color: "var(--text-dim)",
    fontSize: "0.7rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.2em",
    marginBottom: "1.25rem",
    textAlign: "center",
};

export default DynamicDemo;
