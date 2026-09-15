import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";

type PlaceholderPageProps = {
  title: string;
  description: string;
};

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <V2Layout>
      <div className="mx-auto max-w-content px-5 py-16 md:py-24 lg:px-0">
        <h1 className="text-3xl font-semibold text-healia-text">{title}</h1>
        <p className="mt-4 text-lg leading-relaxed text-healia-text-secondary">
          {description}
        </p>
        <div className="mt-8">
          <V2Button to="/" variant="secondary">
            Back to Home
          </V2Button>
        </div>
      </div>
    </V2Layout>
  );
}
