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
  const [health, setHealth] = useState<{ status: string; clock_utc: string; clock_local: string; planner_mode?: string } | null>(null);
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const [clockOffsetMs, setClockOffsetMs] = useState<number>(0);

  useEffect(() => {
    api.getHealth()
      .then((data: any) => {
        setHealth(data);
        if (data.clock_utc || data.clock_local) {
          const serverMs = new Date(data.clock_utc || data.clock_local).getTime();
          setClockOffsetMs(serverMs - Date.now());
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const displayDate = new Date(currentTime.getTime() + clockOffsetMs);
  const kolkataTimeStr = displayDate.toLocaleTimeString('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/70 text-slate-900 font-sans antialiased">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 text-white p-2 rounded-xl shadow-xs ring-2 ring-indigo-50">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold text-slate-900 tracking-tight">LoyaltyGuard AI</h1>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60 uppercase tracking-wide">
                  Demo
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">Points Expiry Tracker & Human-in-the-Loop Agent</p>
            </div>
          </div>

          {/* Clock & Status */}
          <div className="flex items-center space-x-2 sm:space-x-3 text-xs">
            <div className="flex items-center space-x-2 bg-slate-100/80 px-2.5 py-1.5 rounded-lg font-mono text-slate-700 border border-slate-200/60 text-[11px] sm:text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Kolkata (IST): {kolkataTimeStr}</span>
            </div>
            <span className="bg-indigo-50 text-indigo-700 font-medium px-2.5 py-1.5 rounded-lg border border-indigo-200/80 text-[11px] sm:text-xs whitespace-nowrap shadow-xs">
              {health?.planner_mode || "Planner: rule-based (LLM off)"}
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-100 flex space-x-2 sm:space-x-8 overflow-x-auto text-sm no-scrollbar">
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
                className={`flex items-center py-3.5 px-3 border-b-2 font-medium text-xs sm:text-sm whitespace-nowrap transition-colors duration-150 ${
                  isActive
                    ? 'border-indigo-600 text-indigo-600 font-semibold'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2 flex-shrink-0" />
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
