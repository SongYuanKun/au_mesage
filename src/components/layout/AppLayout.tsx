import type { ReactNode } from "react";
import SiteNavbar from "./SiteNavbar";
import SiteFooter from "./SiteFooter";
import PageHero from "./PageHero";

interface AppLayoutProps {
  children: ReactNode;
  hero?: {
    eyebrow?: string;
    title: string;
    subtitle?: string;
  };
}

export default function AppLayout({ children, hero }: AppLayoutProps) {
  return (
    <div className="redesign-v2 min-h-screen flex flex-col">
      <SiteNavbar />
      <main className="koen-main flex-1">
        {hero && (
          <PageHero
            eyebrow={hero.eyebrow}
            title={hero.title}
            subtitle={hero.subtitle}
          />
        )}
        <div className="koen-section">
          <div className="koen-container">{children}</div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
