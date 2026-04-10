import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Network Hub",
};

export default function NetworkLayout({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
}
