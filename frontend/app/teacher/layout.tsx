import AppHeader from "@/components/AppHeader";

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppHeader homeHref="/teacher" />
      {children}
    </>
  );
}
