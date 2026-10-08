import AppHeader from "@/components/AppHeader";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppHeader homeHref="/student" />
      <div className="kid">{children}</div>
    </>
  );
}
