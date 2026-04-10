"use client";

import { useEffect } from "react";
import { Header } from "@/components/layout/header";
import MentorDashboard from "@/components/network/MentorDashboard";

export default function MentorDashboardPage() {
    useEffect(() => {
        document.title = 'Mentor Dashboard · SensAI';
    }, []);

    return (
        <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
            <Header />
            <MentorDashboard />
        </div>
    );
}
