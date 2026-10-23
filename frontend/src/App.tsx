import React, { useState, useEffect } from 'react';
import { DashboardView } from './components/DashboardView';
import { AccountsView } from './components/AccountsView';
import { CalendarView } from './components/CalendarView';
import { AlertsApprovalsView } from './components/AlertsApprovalsView';
import { AgentActivityView } from './components/AgentActivityView';
import { ShieldCheck, Calendar, Bell, Cpu, LayoutDashboard, UserCheck } from 'lucide-react';
import { api } from './api/client';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'accounts' | 'calendar' | 'alerts' | 'agent'>('dashboard');
  const [health, setHealth] = useState<{ status: string; clock_utc: string; clock_local: string } | null>(null);

  useEffect(() => {
    api.getHealth()
      .then(setHealth)
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 text-white p-2 rounded-lg shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900 tracking-tight">LoyaltyGuard AI</h1>
              <p className="text-xs text-slate-500 hidden sm:block">Points Expiry Tracker & Human Approval Agent</p>
            </div>
          </div>

          {/* Clock & Status */}
          <div className="flex items-center space-x-4 text-xs text-slate-500">
            {health && (
              <div className="hidden md:flex items-center space-x-2 bg-slate-100 px-3 py-1.5 rounded-md font-mono">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Kolkata: {new Date(health.clock_local).toLocaleTimeString()}</span>
              </div>
            )}
            <span className="bg-blue-50 text-blue-700 font-medium px-2.5 py-1 rounded border border-blue-200">
              Agentic Fallback: Active
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-100 flex space-x-1 sm:space-x-8 overflow-x-auto text-sm">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
            { id: 'accounts', label: 'Accounts', icon: UserCheck },
            { id: 'calendar', label: 'Points Calendar', icon: Calendar },
            { id: 'alerts', label: 'Alerts & Approvals', icon: Bell },
            { id: 'agent', label: 'Agent Activity & Traces', icon: Cpu },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center py-3.5 px-3 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition ${
                  isActive
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {activeTab === 'dashboard' && <DashboardView onNavigate={(tab) => setActiveTab(tab as any)} />}
        {activeTab === 'accounts' && <AccountsView />}
        {activeTab === 'calendar' && <CalendarView />}
        {activeTab === 'alerts' && <AlertsApprovalsView />}
        {activeTab === 'agent' && <AgentActivityView />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        LoyaltyGuard AI &copy; 2026 &bull; Ziro Agentic AI Hackathon &bull; Synthetic Data Only &bull; Human-in-the-Loop Enforced
      </footer>
    </div>
  );
};

export default App;
