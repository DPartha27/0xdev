import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "SenseNet",
};

export default function NetworkLayout({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
}
