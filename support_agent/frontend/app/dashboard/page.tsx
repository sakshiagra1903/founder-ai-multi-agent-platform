import { redirect } from 'next/navigation';

export default function DashboardPage() {
  // Automatically redirect to the chat agent page
  redirect('/dashboard/chat');
}
