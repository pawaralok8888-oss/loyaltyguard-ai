import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CheckRun, AgentTrace } from '../types';
import { Cpu, CheckCircle2, AlertOctagon, Terminal, ChevronDown, ChevronRight, RefreshCw } from 'lucide-react';

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
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 border border-green-200">
          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Post-Run Verified
        </span>
      );
    }
    if (vStatus === 'mismatch') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
          <AlertOctagon className="w-3.5 h-3.5 mr-1" /> Verification Mismatch
        </span>
      );
    }
    if (vStatus === 'verification_failed') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-200">
          <AlertOctagon className="w-3.5 h-3.5 mr-1" /> Verification Failed
        </span>
      );
    }
    return <span className="text-xs text-gray-400">None</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Agent Activity & Reasoning Traces</h2>
          <p className="text-sm text-gray-500">
            Visible agent decision loop: tool selection, fallback policies, error handling, and post-run verification.
          </p>
        </div>
        <button
          onClick={loadRuns}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded text-xs font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh Runs
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
          {error}
        </div>
      )}

      {loadingRuns ? (
        <div className="p-12 text-center text-gray-500">Loading check runs...</div>
      ) : runs.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-500">
          No agent check runs recorded yet. Go to Accounts and click "Check now".
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Runs List */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden flex flex-col h-[650px]">
            <div className="p-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase text-gray-600">Recent Check Runs ({runs.length})</span>
              <Cpu className="w-4 h-4 text-blue-600" />
            </div>
            <div className="divide-y divide-gray-100 overflow-y-auto flex-1">
              {runs.map(r => (
                <div
                  key={r.id}
                  onClick={() => setSelectedRunId(r.id)}
                  className={`p-4 cursor-pointer transition ${
                    selectedRunId === r.id ? 'bg-blue-50 border-l-4 border-blue-600' : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-sm text-gray-900">Run #{r.id}</span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-medium ${
                        r.outcome === 'success'
                          ? 'bg-green-100 text-green-800'
                          : r.outcome === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {r.outcome}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-gray-500 flex justify-between">
                    <span>Account #{r.loyalty_account_id}</span>
                    <span>{new Date(r.started_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="mt-2 text-xs">
                    {getVerificationBadge(r.verification_status)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Trace Timeline */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 shadow-sm p-6 flex flex-col h-[650px]">
            {selectedRun ? (
              <div className="flex flex-col h-full">
                {/* Run Header */}
                <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-start">
                  <div>
                    <h3 className="text-base font-bold text-gray-900">
                      Check Run #{selectedRun.id} — Execution Traces
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Started: {new Date(selectedRun.started_at).toLocaleString()} | Finished:{' '}
                      {selectedRun.finished_at ? new Date(selectedRun.finished_at).toLocaleString() : 'In Progress'}
                    </p>
                  </div>
                  <div>{getVerificationBadge(selectedRun.verification_status)}</div>
                </div>

                {/* Evidence / Error Summary if Failed */}
                {selectedRun.error_code && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                    <span className="font-bold">Error Encountered:</span> {selectedRun.error_code}
                  </div>
                )}

                {/* Traces List */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                  {loadingTraces ? (
                    <div className="p-8 text-center text-gray-400">Loading traces...</div>
                  ) : traces.length === 0 ? (
                    <div className="p-8 text-center text-gray-400">No traces recorded for this run.</div>
                  ) : (
                    traces.map((trace, idx) => (
                      <div key={trace.id} className="border border-gray-200 rounded-lg p-3.5 bg-gray-50 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-bold">
                              {idx + 1}
                            </span>
                            <span className="font-mono text-xs font-bold text-gray-900">{trace.tool_name}</span>
                            <span className="font-mono text-[10px] px-2 py-0.5 bg-gray-200 text-gray-700 rounded">
                              {trace.decision_type}
                            </span>
                          </div>
                          <span className="text-[11px] text-gray-400">
                            {new Date(trace.created_at).toLocaleTimeString()}
                          </span>
                        </div>

                        <p className="text-xs text-gray-700 pl-7">{trace.explanation}</p>

                        {/* Collapsible Payload Inspection */}
                        {(trace.input_redacted_json || trace.output_redacted_json) && (
                          <div className="pl-7 pt-1">
                            <button
                              onClick={() => toggleExpand(trace.id)}
                              className="inline-flex items-center text-[11px] text-blue-600 hover:underline"
                            >
                              {expandedTraceIds[trace.id] ? (
                                <ChevronDown className="w-3 h-3 mr-1" />
                              ) : (
                                <ChevronRight className="w-3 h-3 mr-1" />
                              )}
                              {expandedTraceIds[trace.id] ? 'Hide Payload Details' : 'View Payload Details'}
                            </button>

                            {expandedTraceIds[trace.id] && (
                              <div className="mt-2 space-y-2">
                                {trace.input_redacted_json && (
                                  <div>
                                    <span className="text-[10px] font-semibold text-gray-500 uppercase">Input</span>
                                    <pre className="mt-1 p-2 bg-gray-900 text-gray-100 rounded text-[11px] font-mono overflow-x-auto">
                                      {JSON.stringify(JSON.parse(trace.input_redacted_json), null, 2)}
                                    </pre>
                                  </div>
                                )}
                                {trace.output_redacted_json && (
                                  <div>
                                    <span className="text-[10px] font-semibold text-gray-500 uppercase">Output</span>
                                    <pre className="mt-1 p-2 bg-gray-900 text-green-300 rounded text-[11px] font-mono overflow-x-auto">
                                      {JSON.stringify(JSON.parse(trace.output_redacted_json), null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-gray-400">Select a check run from the left panel.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
