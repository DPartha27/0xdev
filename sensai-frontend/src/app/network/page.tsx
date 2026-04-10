"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/layout/header";
import NetworkDashboard from "@/components/network/NetworkDashboard";

export default function NetworkPage() {
    const [entered, setEntered] = useState(false);

    useEffect(() => {
        document.title = 'SenseNet · SensAI';
        // Play a subtle arrival chime
        try {
            const ctx = new AudioContext();
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            osc.type = "sine";
            osc.frequency.setValueAtTime(660, now);
            osc.frequency.setValueAtTime(880, now + 0.08);
            osc.frequency.setValueAtTime(1100, now + 0.16);
            const gain = ctx.createGain();
            gain.gain.setValueAtTime(0, now);
            gain.gain.linearRampToValueAtTime(0.12, now + 0.03);
            gain.gain.linearRampToValueAtTime(0.08, now + 0.1);
            gain.gain.linearRampToValueAtTime(0, now + 0.3);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.35);
        } catch {}
        // Trigger entrance animation
        requestAnimationFrame(() => setEntered(true));
    }, []);

    return (
        <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
            <div className={`transition-all duration-500 ease-out ${entered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
                <Header />
            </div>
            <div className={`transition-all duration-700 ease-out delay-150 ${entered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}`}>
                <NetworkDashboard />
            </div>
        </div>
    );
}
