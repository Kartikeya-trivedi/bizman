export default function SettingsPage() {
  return (
    <main className="ml-(--spacing-sidebar-width) min-h-screen">
      <div className="pt-24 px-6 pb-10 max-w-screen-2xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-on-surface">Settings</h1>
          <p className="text-sm text-on-surface-variant mt-0.5">Manage your workspace preferences.</p>
        </header>

        <div className="bg-surface border border-outline-variant rounded-2xl p-8 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-full bg-primary-container/20 flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-3xl text-primary">build</span>
          </div>
          <h2 className="text-xl font-semibold text-on-surface mb-2">Settings Coming Soon</h2>
          <p className="text-sm text-on-surface-variant max-w-md">
            This module is currently under development. Soon you will be able to manage your API keys, subscription plans, and team members here.
          </p>
        </div>
      </div>
    </main>
  );
}
