// modules/CryptoPaymentModule.tsx
// Module 2 Frontend: Plans grid + subscription status + invoice creation
// Self-contained subscription UI

"use client";

import React, { useState, useEffect } from "react";
import { BASE_URL } from "@/configs/baseConfig";

interface Feature {
    icon: string;
    title: string;
    text: string;
}

interface Plan {
    id: string;
    title: string;
    price: number;
    duration_days: number;
    features: Feature[];
    is_popular?: boolean;
    is_base?: boolean;
    per_period_label?: string;
}

// --- Inline styles ---
const s: Record<string, React.CSSProperties> = {
    container: {
        padding: "2rem",
        maxWidth: "960px",
        margin: "0 auto",
        animation: "fadeInScale 0.4s ease-out forwards",
    },
    title: {
        fontSize: "1.5rem",
        fontWeight: 700,
        color: "var(--text-main)",
        marginBottom: "0.5rem",
        textAlign: "center",
        letterSpacing: "-0.01em",
    },
    subtitle: {
        fontSize: "0.95rem",
        color: "var(--text-muted)",
        marginBottom: "2.5rem",
        textAlign: "center",
    },
    grid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: "1.5rem",
    },
    card: {
        position: "relative",
        borderRadius: "var(--radius-card)",
        padding: "2rem",
        background: "var(--glass-bg)",
        backdropFilter: "var(--glass-blur)",
        WebkitBackdropFilter: "var(--glass-blur)",
        border: "1px solid var(--glass-border)",
        display: "flex",
        flexDirection: "column",
        transition: "all 0.3s ease",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4)",
    },
    popularBadge: {
        position: "absolute",
        top: "12px",
        right: "12px",
        background: "var(--accent-primary)",
        color: "white",
        padding: "4px 10px",
        borderRadius: "4px",
        fontSize: "0.65rem",
        fontWeight: 800,
        textTransform: "uppercase",
    },
    planTitle: {
        fontSize: "1.2rem",
        fontWeight: 700,
        color: "var(--text-main)",
        marginBottom: "0.5rem",
    },
    price: {
        fontSize: "1.75rem",
        fontWeight: 800,
        color: "var(--text-main)",
        marginBottom: "0.25rem",
    },
    period: {
        fontSize: "0.85rem",
        color: "var(--text-dim)",
        marginBottom: "1.5rem",
    },
    featureList: {
        listStyle: "none",
        padding: 0,
        margin: "0 0 2rem 0",
        flex: 1,
    },
    feature: {
        fontSize: "0.85rem",
        color: "var(--text-muted)",
        padding: "10px 0",
        display: "flex",
        alignItems: "center",
        gap: "10px",
        borderBottom: "1px solid rgba(255,255,255,0.03)",
    },
    btn: {
        padding: "0.85rem",
        borderRadius: "var(--radius-btn)",
        border: "none",
        fontWeight: 700,
        fontSize: "0.9rem",
        cursor: "pointer",
        width: "100%",
        transition: "all 0.2s",
    },
    btnCurrent: {
        background: "rgba(34, 197, 94, 0.1)",
        color: "#4ade80",
        cursor: "default",
    },
    statusBar: {
        padding: "1rem",
        borderRadius: "var(--radius-inner)",
        background: "rgba(255,255,255,0.02)",
        border: "1px solid rgba(255,255,255,0.04)",
        marginBottom: "2rem",
        fontSize: "0.85rem",
        color: "var(--text-muted)",
        textAlign: "center",
    },
    loading: {
        textAlign: "center",
        color: "var(--text-dim)",
        padding: "4rem",
    },
};

export default function CryptoPaymentModule() {
    const [plans, setPlans] = useState<Plan[]>([]);
    const [subStatus, setSubStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [plansRes, subRes] = await Promise.all([
                fetch(`${BASE_URL}/api/crypto/plans`, { credentials: "include" }),
                fetch(`${BASE_URL}/api/crypto/my-subscription`, { credentials: "include" }),
            ]);
            const plansData = await plansRes.json();
            const subData = await subRes.json();
            if (plansData.result) setPlans(plansData.result);
            setSubStatus(subData);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const createInvoice = async (planId: string) => {
        const newTab = window.open("", "_blank");
        try {
            const res = await fetch(`${BASE_URL}/api/crypto/create-invoice`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ plan_id: planId }),
                credentials: "include",
            });
            const data = await res.json();
            if (data.invoice_url && newTab) {
                newTab.location.href = data.invoice_url;
            }
        } catch (e: any) {
            if (newTab) newTab.close();
            alert(e.message);
        }
    };

    const getButtonText = (plan: Plan) => {
        if (plan.id === subStatus?.plan_id && subStatus?.is_active) return "Current Plan";
        if (plan.id === subStatus?.plan_id && subStatus?.status === "PENDING") return "Pending Payment";
        if (plan.is_base) return "Free Plan";
        return `Upgrade to ${plan.title}`;
    };

    if (loading) return <div style={s.loading}>Loading plans...</div>;

    return (
        <div style={s.container}>
            <div style={s.title} className="font-heading">Select Plan</div>
            <div style={s.subtitle}>Professional solutions for your needs</div>

            {subStatus && subStatus.plan_id !== "base_tier" && (
                <div style={s.statusBar}>
                    Active: {subStatus.plan_id} • {subStatus.status}
                    {subStatus.expire_in_days != null && ` • ${subStatus.expire_in_days} days left`}
                </div>
            )}

            <div style={s.grid}>
                {plans.map((plan) => {
                    const isCurrent = plan.id === subStatus?.plan_id && subStatus?.is_active;
                    return (
                        <div
                            key={plan.id}
                            style={s.card}
                        >
                            {plan.is_popular && <div style={s.popularBadge}>Popular</div>}
                            <div style={s.planTitle} className="font-heading">{plan.title}</div>
                            <div style={s.price}>{plan.price > 0 ? `$${plan.price}` : "Free"}</div>
                            <div style={s.period}>{plan.per_period_label}</div>
                            <ul style={s.featureList}>
                                {plan.features.map((f, i) => (
                                    <li key={i} style={s.feature}>
                                        <span style={{ opacity: 0.5 }}>•</span>
                                        <span>{f.title}: {f.text}</span>
                                    </li>
                                ))}
                            </ul>
                            <button
                                style={{ ...s.btn, ...(isCurrent ? s.btnCurrent : {}) }}
                                onClick={() => !isCurrent && !plan.is_base && createInvoice(plan.id)}
                                disabled={isCurrent || plan.is_base}
                                className={!isCurrent && !plan.is_base ? "btn-accent" : ""}
                            >
                                {getButtonText(plan)}
                            </button>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
