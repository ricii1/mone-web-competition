import BackLink from "@/components/BackLink";

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
  /** Round icon chip shown before the title. */
  icon?: React.ReactNode;
  back?: { href: string; label: string };
  width?: Width;
  /** Big friendly text for pages used by students. */
  kid?: boolean;
}

export default function PageShell({
  children,
  title,
  subtitle,
  actions,
  icon,
  back,
  width = "wide",
  kid = false,
}: PageShellProps) {
  return (
    <main className={`mx-auto w-full ${WIDTH[width]} px-4 pb-16 pt-3 sm:px-6 lg:px-8 ${kid ? "kid" : ""}`}>
      {back && (
        <div className="mb-2">
          <BackLink href={back.href}>{back.label}</BackLink>
        </div>
      )}
      {(title || actions) && (
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            {icon && (
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-highlight text-ink shadow-[0_3px_0_0_#c98f00]">
                {icon}
              </span>
            )}
            <div className="min-w-0">
              {title && <h1 className="text-3xl sm:text-4xl">{title}</h1>}
              {subtitle && <div className="mt-1 text-ink/75">{subtitle}</div>}
            </div>
          </div>
          {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
        </div>
      )}
      {children}
    </main>
  );
}
