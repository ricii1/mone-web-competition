import AppHeader from "@/components/AppHeader";
import CloudSky from "@/components/CloudSky";

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <CloudSky variant="page" />
      <AppHeader homeHref="/teacher" />
      {children}
    </>
  );
}
