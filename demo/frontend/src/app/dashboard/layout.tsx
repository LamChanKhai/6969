import DashboardLayout from '@/components/layout/dashboard-layout';
import DashboardPage from '@/components/dashboard/dashboard-page';

export default function DashboardRoot() {
  return (
    <DashboardLayout>
      <DashboardPage />
    </DashboardLayout>
  );
}
