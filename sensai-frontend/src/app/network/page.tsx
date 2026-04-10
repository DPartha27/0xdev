"use client";

import { useEffect } from "react";
import { Header } from "@/components/layout/header";
import NetworkDashboard from "@/components/network/NetworkDashboard";

export default function NetworkPage() {
    useEffect(() => {
        document.title = 'Network Hub · SensAI';
    }, []);

    return (
        <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
            <Header />
            <NetworkDashboard />
        </div>
    );
}
