import BackLink from "@/components/BackLink";
import Breadcrumb, { type Crumb } from "@/components/Breadcrumb";

type Width = "narrow" | "medium" | "wide";

const WIDTH: Record<Width, string> = {
  narrow: "max-w-md",
  medium: "max-w-3xl",
  wide: "max-w-6xl",
};

interface PageShellProps {
  children: React.ReactNode;
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  back?: { href: string; label: string };
  crumbs?: Crumb[];
  width?: Width;
}

export default function PageShell({
  children,
  title,
  subtitle,
  actions,
  back,
  crumbs,
  width = "wide",
}: PageShellProps) {
  return (
    <main className={`mx-auto w-full ${WIDTH[width]} px-4 pb-16 pt-4 sm:px-6 lg:px-8`}>
      {(back || crumbs) && (
        <div className="mb-3 flex flex-wrap items-center gap-x-4">
          {back && <BackLink href={back.href}>{back.label}</BackLink>}
          {crumbs && <Breadcrumb items={crumbs} />}
        </div>
      )}
      {(title || actions) && (
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            {title && <h1 className="font-display text-2xl sm:text-3xl">{title}</h1>}
            {subtitle && <div className="mt-1 text-ink/65">{subtitle}</div>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </main>
  );
}
