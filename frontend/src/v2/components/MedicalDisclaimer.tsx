export function MedicalDisclaimer() {
  return (
    <aside className="bg-healia-bg-secondary">
      <div className="mx-auto max-w-page px-5 pb-16 md:px-8 md:pb-20 lg:px-12">
        <div className="rounded-lg border border-healia-border-subtle bg-healia-bg px-5 py-4 md:px-6">
          <p className="text-sm leading-relaxed text-healia-text-muted">
            <span className="font-medium text-healia-text-secondary">
              Medical disclaimer:{" "}
            </span>
            Healia does not provide a medical diagnosis and is not a substitute
            for professional medical advice. Always consult a qualified
            healthcare provider for health concerns. Call emergency services for
            urgent symptoms.
          </p>
        </div>
      </div>
    </aside>
  );
}
