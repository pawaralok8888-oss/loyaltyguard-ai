import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CheckRun, AgentTrace } from '../types';
import { Cpu, CheckCircle2, AlertOctagon, Terminal, ChevronDown, ChevronRight, RefreshCw, Clock } from 'lucide-react';
import { EmptyAgentRunsIllustration } from './Illustrations';

export const AgentActivityView: React.FC = () => {
  const [runs, setRuns] = useState<CheckRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [traces, setTraces] = useState<AgentTrace[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [loadingTraces, setLoadingTraces] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedTraceIds, setExpandedTraceIds] = useState<Record<number, boolean>>({});

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    if (selectedRunId !== null) {
      loadTraces(selectedRunId);
    }
  }, [selectedRunId]);

  const loadRuns = async () => {
    try {
      setLoadingRuns(true);
      setError(null);
      const data = await api.getRuns();
      setRuns(data);
      if (data.length > 0 && selectedRunId === null) {
        setSelectedRunId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch check runs');
    } finally {
      setLoadingRuns(false);
    }
  };

  const loadTraces = async (runId: number) => {
    try {
      setLoadingTraces(true);
      const data = await api.getTraces(runId);
      // Sort ascending by step/id
      data.sort((a, b) => a.id - b.id);
      setTraces(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch traces');
    } finally {
      setLoadingTraces(false);
    }
  };

  const toggleExpand = (traceId: number) => {
    setExpandedTraceIds(prev => ({ ...prev, [traceId]: !prev[traceId] }));
  };

  const selectedRun = runs.find(r => r.id === selectedRunId);

  const getVerificationBadge = (vStatus: string | null) => {
    if (vStatus === 'verified') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
          <CheckCircle2 className="w-3 h-3 mr-1" /> Post-Run Verified
        </span>
      );
    }
    if (vStatus === 'mismatch') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
          <AlertOctagon className="w-3 h-3 mr-1" /> Verification Mismatch
        </span>
      );
    }
    if (vStatus === 'verification_failed') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
          <AlertOctagon className="w-3 h-3 mr-1" /> Verification Failed
        </span>
      );
    }
    return <span className="text-[11px] text-slate-400">None</span>;
  };

  return (
    <div className="space-y-6 min-w-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900">Agent Activity & Reasoning Traces</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Transparent agent decision loop: tool selection, fallback policies, error handling, and post-run verification.
          </p>
        </div>
        <button
          onClick={loadRuns}
          className="inline-flex items-center px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 shadow-xs transition self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5 text-slate-500" /> Refresh Runs
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs shadow-xs">
          {error}
        </div>
      )}

      {loadingRuns ? (
        <div className="p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm">Loading check runs...</span>
        </div>
      ) : runs.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200/80 p-12 text-center text-slate-500 flex flex-col items-center justify-center space-y-3 shadow-xs">
          <EmptyAgentRunsIllustration className="w-20 h-20" />
          <div className="text-sm font-semibold text-slate-700">No agent check runs recorded yet</div>
          <p className="text-xs text-slate-500 max-w-sm">
            Navigate to the Accounts page and click "Check now" to initiate an agentic balance check and trace.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-w-0 items-start">
          {/* Left Column: Runs List */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden flex flex-col h-auto max-h-[600px] lg:h-[720px] lg:max-h-none min-w-0">
            <div className="p-4 border-b border-slate-100 bg-slate-50/60 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-600">Recent Check Runs ({runs.length})</span>
              <Cpu className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="divide-y divide-slate-100 overflow-y-auto flex-1">
              {runs.map(r => (
                <div
                  key={r.id}
                  onClick={() => setSelectedRunId(r.id)}
                  className={`p-4 cursor-pointer transition-colors duration-150 ${
                    selectedRunId === r.id ? 'bg-indigo-50/70 border-l-4 border-indigo-600' : 'hover:bg-slate-50/60'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs text-slate-900">Run #{r.id}</span>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
                        r.outcome === 'success'
                          ? 'bg-teal-50 text-teal-700 border border-teal-200'
                          : r.outcome === 'failed'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {r.outcome}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-slate-500 flex justify-between">
                    <span>Account #{r.loyalty_account_id}</span>
                    <span className="font-mono text-[11px]">{new Date(r.started_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="mt-2 text-xs">
                    {getVerificationBadge(r.verification_status)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Trace Timeline (fixed cut-off with min-w-0 and vertical line) */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 shadow-xs p-5 sm:p-6 flex flex-col min-w-0 h-auto lg:h-[720px] overflow-hidden">
            {selectedRun ? (
              <div className="flex flex-col h-full min-w-0">
                {/* Run Header */}
                <div className="border-b border-slate-100 pb-4 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 min-w-0">
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <Terminal className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                      <h3 className="text-sm sm:text-base font-bold text-slate-900 truncate">
                        Check Run #{selectedRun.id} — Execution Traces
                      </h3>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 truncate">
                      Started: {new Date(selectedRun.started_at).toLocaleString()} | Finished:{' '}
                      {selectedRun.finished_at ? new Date(selectedRun.finished_at).toLocaleString() : 'In Progress'}
                    </p>
                  </div>
                  <div className="flex-shrink-0">{getVerificationBadge(selectedRun.verification_status)}</div>
                </div>

                {/* Evidence / Error Summary if Failed */}
                {selectedRun.error_code && (
                  <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center space-x-2 shadow-xs">
                    <AlertOctagon className="w-4 h-4 flex-shrink-0 text-rose-600" />
                    <div>
                      <span className="font-bold">Error Encountered:</span> {selectedRun.error_code}
                    </div>
                  </div>
                )}

                {/* Traces List with Vertical Connecting Line */}
                <div className="flex-1 overflow-y-auto pr-1 min-w-0">
                  {loadingTraces ? (
                    <div className="p-8 text-center text-slate-400 text-xs">Loading execution traces...</div>
                  ) : traces.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 text-xs">No traces recorded for this run.</div>
                  ) : (
                    <div className="relative pl-7 sm:pl-8 space-y-5 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-indigo-100 min-w-0">
                      {traces.map((trace, idx) => (
                        <div key={trace.id} className="relative group min-w-0">
                          {/* Numbered Step Node on the Line */}
                          <div className="absolute -left-7 sm:-left-8 top-1 w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[11px] font-bold ring-4 ring-white shadow-xs">
                            {idx + 1}
                          </div>

                          {/* Step Content Card */}
                          <div className="border border-slate-200/80 rounded-xl p-4 bg-slate-50/50 hover:bg-slate-50 transition space-y-2 min-w-0">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 min-w-0">
                              <div className="flex items-center space-x-2 min-w-0 flex-wrap">
                                <span className="font-mono text-xs font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200 shadow-xs">
                                  {trace.tool_name}
                                </span>
                                <span className="font-mono text-[10px] px-2 py-0.5 bg-indigo-50 text-indigo-700 font-medium rounded border border-indigo-200/60">
                                  {trace.decision_type}
                                </span>
                              </div>
                              <span className="text-[11px] text-slate-400 font-mono flex-shrink-0">
                                {new Date(trace.created_at).toLocaleTimeString()}
                              </span>
                            </div>

                            <p className="text-xs text-slate-700 leading-relaxed break-words">{trace.explanation}</p>

                            {/* Collapsible Payload Inspection */}
                            {(trace.input_redacted_json || trace.output_redacted_json) && (
                              <div className="pt-1 min-w-0">
                                <button
                                  onClick={() => toggleExpand(trace.id)}
                                  className="inline-flex items-center text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 transition"
                                >
                                  {expandedTraceIds[trace.id] ? (
                                    <ChevronDown className="w-3.5 h-3.5 mr-1" />
                                  ) : (
                                    <ChevronRight className="w-3.5 h-3.5 mr-1" />
                                  )}
                                  {expandedTraceIds[trace.id] ? 'Hide Payload Details' : 'View Payload Details'}
                                </button>

                                {expandedTraceIds[trace.id] && (
                                  <div className="mt-2.5 space-y-2 min-w-0">
                                    {trace.input_redacted_json && (
                                      <div className="min-w-0">
                                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Input Payload</span>
                                        <pre className="mt-1 p-3 bg-slate-900 text-slate-100 rounded-lg text-[11px] font-mono overflow-x-auto max-w-full">
                                          {JSON.stringify(JSON.parse(trace.input_redacted_json), null, 2)}
                                        </pre>
                                      </div>
                                    )}
                                    {trace.output_redacted_json && (
                                      <div className="min-w-0">
                                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Output Payload</span>
                                        <pre className="mt-1 p-3 bg-slate-900 text-teal-300 rounded-lg text-[11px] font-mono overflow-x-auto max-w-full">
                                          {JSON.stringify(JSON.parse(trace.output_redacted_json), null, 2)}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center justify-center h-full">
                Select a check run from the left panel to inspect step-by-step reasoning traces.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
