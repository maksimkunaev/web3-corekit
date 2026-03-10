import "@/styles/globals.css";
import type { AppProps } from "next/app";

export default function MyApp({ Component, pageProps }: AppProps) {
    return (
        <div style={{ background: "var(--bg-app)", minHeight: "100vh", backgroundAttachment: "fixed" }}>
            <Component {...pageProps} />
        </div>
    );
}
