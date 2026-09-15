import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type AuthFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
};

export function AuthField({
  label,
  hint,
  error,
  className,
  id,
  ...props
}: AuthFieldProps) {
  const fieldId = id || props.name;

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={fieldId}
        className="text-sm font-medium text-healia-text"
      >
        {label}
      </label>
      <input
        id={fieldId}
        className={cn(
          "w-full rounded-lg border border-healia-border bg-healia-bg px-3.5 py-2.5 text-sm text-healia-text outline-none transition-colors placeholder:text-healia-text-muted focus:border-healia-brand focus:ring-2 focus:ring-healia-brand/20",
          error && "border-healia-danger focus:border-healia-danger focus:ring-healia-danger/20",
          className,
        )}
        {...props}
      />
      {hint && !error ? (
        <p className="text-xs text-healia-text-muted">{hint}</p>
      ) : null}
      {error ? <p className="text-xs text-healia-danger">{error}</p> : null}
    </div>
  );
}
