import React from "react";
import { NetworkProvider } from "@/context/NetworkContext";

interface NetworkLayoutProps {
  children: React.ReactNode;
  params: { id: string };
}

export default async function NetworkLayout({
  children,
  params,
}: NetworkLayoutProps) {
  // org_id resolution happens client-side via useSchools hook;
  // pass null here and let child pages set it via context
  return <NetworkProvider orgId={null}>{children}</NetworkProvider>;
}
