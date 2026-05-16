import Sidebar from "@/components/Sidebar";
import TopNavBar from "@/components/TopNavBar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Sidebar />
      <TopNavBar />
      {children}
    </>
  );
}
