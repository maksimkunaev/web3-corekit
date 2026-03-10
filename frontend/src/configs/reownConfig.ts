// @/configs/reownConfig.ts
export const PROJECT_ID = process.env.NEXT_PUBLIC_REOWN_PROJECT_ID as string;
export const APP_NAME = process.env.NEXT_PUBLIC_REOWN_APP_NAME || "Web3 Corekit";
export const APP_DESCRIPTION = process.env.NEXT_PUBLIC_REOWN_APP_DESCRIPTION || "Modular Web3 Toolkit";
export const APP_URL = process.env.NEXT_PUBLIC_REOWN_APP_URL as string;
export const APP_ICONS: string[] = [];
export const DOMAIN = process.env.NEXT_PUBLIC_REOWN_DOMAIN as string;
export const CHAINS = [1, 42161];
export const SIWE_STATEMENT = "Sign in with your wallet to access the toolkit";
