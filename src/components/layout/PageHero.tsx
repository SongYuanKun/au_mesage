interface PageHeroProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}

export default function PageHero({ eyebrow, title, subtitle, children }: PageHeroProps) {
  return (
    <section className="koen-hero-compact koen-container" aria-labelledby="page-hero-title">
      {eyebrow && <p className="koen-eyebrow">{eyebrow}</p>}
      <h1 id="page-hero-title" className="koen-hero-title">
        {title}
      </h1>
      {subtitle && <p className="koen-hero-sub">{subtitle}</p>}
      {children}
    </section>
  );
}
