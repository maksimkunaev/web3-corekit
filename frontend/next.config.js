/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Load env from parent dir (backend .env) for NEXT_PUBLIC_ vars
    env: {},
};

module.exports = nextConfig;
