import DashboardLayout from '@/components/layout/dashboard-layout';
import DashboardPage from '@/components/dashboard/dashboard-page';

export const dynamic = 'force-dynamic';

export default function DashboardRoot() {
  return (
    <DashboardLayout>
      <DashboardPage />
    </DashboardLayout>
  );
}
