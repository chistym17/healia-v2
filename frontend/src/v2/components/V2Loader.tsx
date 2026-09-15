import { cn } from "@/lib/utils";

type V2LoaderProps = {
  label?: string;
  className?: string;
  /** full = fills parent / screen area */
  full?: boolean;
  size?: "sm" | "md" | "lg";
};

const sizeMap = {
  sm: "h-5 w-5 border-2",
  md: "h-8 w-8 border-[2.5px]",
  lg: "h-10 w-10 border-[3px]",
};

export function V2Loader({
  label = "Loading",
  className,
  full = false,
  size = "md",
}: V2LoaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3",
        full && "min-h-[12rem] flex-1",
        className,
      )}
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <span className="relative flex items-center justify-center">
        <span
          className={cn(
            "rounded-full border-healia-brand/20 border-t-healia-brand animate-spin",
            sizeMap[size],
          )}
        />
        <span className="absolute h-1.5 w-1.5 rounded-full bg-healia-brand" />
      </span>
      {label ? (
        <p className="text-sm text-healia-text-secondary">{label}</p>
      ) : null}
    </div>
  );
}

export function V2PageLoader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="v2-root flex min-h-screen items-center justify-center bg-healia-bg">
      <V2Loader label={label} size="lg" />
    </div>
  );
}
