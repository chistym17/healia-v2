import type { ReactNode } from "react";
import { V2Navigation } from "./V2Navigation";
import { V2Footer } from "./V2Footer";

export function V2Layout({ children }: { children: ReactNode }) {
  return (
    <div className="v2-root flex min-h-screen flex-col">
      <V2Navigation />
      <main className="flex-1">{children}</main>
      <V2Footer />
    </div>
  );
}
