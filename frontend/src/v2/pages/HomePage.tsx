import { V2Layout } from "@/v2/components/V2Layout";
import { HeroSection } from "@/v2/components/HeroSection";
import { HowItWorks } from "@/v2/components/HowItWorks";
import { ValueSection } from "@/v2/components/ValueSection";
import { CtaSection } from "@/v2/components/CtaSection";
import { MedicalDisclaimer } from "@/v2/components/MedicalDisclaimer";

export default function HomePage() {
  return (
    <V2Layout>
      <HeroSection />
      <HowItWorks />
      <ValueSection />
      <CtaSection />
      <MedicalDisclaimer />
    </V2Layout>
  );
}
