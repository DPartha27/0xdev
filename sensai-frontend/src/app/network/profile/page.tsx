"use client";

import { useEffect } from "react";
import { Header } from "@/components/layout/header";
import UserProfileDashboard from "@/components/network/UserProfileDashboard";

export default function ProfilePage() {
    useEffect(() => {
        document.title = "My Profile · SensAI";
    }, []);

    return (
        <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
            <Header />
            <UserProfileDashboard />
        </div>
    );
}
