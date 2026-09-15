import type { ReactNode } from "react";
import { V2Navigation } from "./V2Navigation";
import { V2Footer } from "./V2Footer";

type V2LayoutProps = {
  children: ReactNode;
  footer?: "full" | "compact" | "none";
};

export function V2Layout({ children, footer = "full" }: V2LayoutProps) {
  return (
    <div className="v2-root flex min-h-screen flex-col">
      <V2Navigation />
      <main className="flex min-h-0 flex-1 flex-col">{children}</main>
      {footer !== "none" ? <V2Footer variant={footer} /> : null}
    </div>
  );
}
