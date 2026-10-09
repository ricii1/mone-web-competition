import AppHeader from "@/components/AppHeader";
import CloudSky from "@/components/CloudSky";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <CloudSky variant="page" />
      <AppHeader homeHref="/student" />
      <div className="kid">{children}</div>
    </>
  );
}
