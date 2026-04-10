"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import type { Hub, HubMemberRole, NetworkContextValue } from "@/types/network";

const NetworkContext = createContext<NetworkContextValue>({
  activeHub: null,
  setActiveHub: () => {},
  userHubRole: null,
  orgId: null,
});

export function NetworkProvider({
  children,
  orgId,
}: {
  children: ReactNode;
  orgId: number | null;
}) {
  const [activeHub, setActiveHub] = useState<Hub | null>(null);
  const [userHubRole] = useState<HubMemberRole | null>(null);

  return (
    <NetworkContext.Provider
      value={{ activeHub, setActiveHub, userHubRole, orgId }}
    >
      {children}
    </NetworkContext.Provider>
  );
}

export function useNetwork() {
  return useContext(NetworkContext);
}
