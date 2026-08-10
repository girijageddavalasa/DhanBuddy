'use client';

import React, { useEffect, useRef, useState } from 'react';
import { RoomEvent } from 'livekit-client';
import {
  ArrowDown,
  AudioLines,
  CalendarClock,
  CircleStop,
  IndianRupee,
  LockKeyhole,
  MessageSquareText,
  Mic,
  Radio,
  Sparkles,
  TrendingUp,
  Volume2,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { cn } from '@/lib/shadcn/utils';
import { AudioVisualizer } from './audio-visualizer';

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  className?: string;
}

const STATE_COPY = {
  disconnected: { label: 'Connecting', detail: 'Joining your private room', icon: Radio },
  connecting: { label: 'Connecting', detail: 'Joining your private room', icon: Radio },
  initializing: { label: 'Connecting', detail: 'Preparing DhanBuddy', icon: Sparkles },
  listening: { label: 'Listening to you', detail: 'Tell me in your own words', icon: Mic },
  thinking: { label: 'Calculating', detail: 'No investment returns assumed', icon: Sparkles },
  speaking: {
    label: 'DhanBuddy is speaking',
    detail: 'Here is your simple estimate',
    icon: Volume2,
  },
  failed: { label: 'Call ended', detail: 'You can start a fresh plan', icon: CircleStop },
} as const;

const JOURNEY = ['Goal', 'Target', 'Timeline', 'Savings', 'Estimate'];
const PIPELINE = ['Deepgram hears', 'Gemini understands', 'Murf Falcon speaks'];

interface ScenarioResult {
  target_amount: number;
  current_projected_amount: number;
  current_monthly_saving: number;
  current_months: number;
  on_track: boolean;
  required_monthly_saving: number;
  monthly_increase_needed: number;
  months_needed_at_current_saving: number | null;
  deadline_extension_months: number | null;
  calculated_at: string;
  data_source: string;
}

interface ToolActivity {
  tool: string;
  status: 'running' | 'completed' | 'failed';
  message: string;
}

const formatRupees = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);

export function AgentSessionView_01({
  preConnectMessage = 'Start with one dream. What are you saving for?',
  supportsChatInput = true,
  supportsVideoInput = false,
  supportsScreenShare = false,
  isPreConnectBufferEnabled = true,
  audioVisualizerType = 'wave',
  audioVisualizerColor = '#D946EF',
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const [chatOpen, setChatOpen] = useState(true);
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(null);
  const [toolActivity, setToolActivity] = useState<ToolActivity[]>([]);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const state = STATE_COPY[agentState as keyof typeof STATE_COPY] ?? STATE_COPY.connecting;
  const StateIcon = state.icon;
  const completedSteps = Math.min(Math.ceil(messages.length / 2), JOURNEY.length);

  const controls: AgentControlBarControls = {
    leave: false,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    if (transcriptRef.current) transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    const handleToolResult = (
      payload: Uint8Array,
      _participant?: unknown,
      _kind?: unknown,
      topic?: string
    ) => {
      if (topic !== 'dhanbuddy.tool_result') return;
      try {
        const message = JSON.parse(new TextDecoder().decode(payload)) as {
          type?: string;
          success?: boolean;
          result?: ScenarioResult;
          tool?: string;
          status?: ToolActivity['status'];
          message?: string;
        };
        if (message.type === 'tool_status' && message.tool && message.status && message.message) {
          setToolActivity((current) => {
            const next = current.filter((item) => item.tool !== message.tool);
            return [
              ...next,
              { tool: message.tool!, status: message.status!, message: message.message! },
            ].slice(-3);
          });
        }
        if (message.type === 'savings_scenarios' && message.success && message.result) {
          setScenarioResult(message.result);
        }
      } catch {
        // Ignore malformed third-party room data instead of breaking the call UI.
      }
    };
    session.room.on(RoomEvent.DataReceived, handleToolResult);
    return () => {
      session.room.off(RoomEvent.DataReceived, handleToolResult);
    };
  }, [session.room]);

  return (
    <section
      ref={ref}
      className={cn('dhan-page min-h-svh w-full overflow-y-auto', className)}
      {...props}
    >
      <div className="mx-auto min-h-svh max-w-[1500px] px-3 py-3 sm:px-5 sm:py-5">
        <header className="dhan-live-header">
          <div className="flex min-w-0 items-center gap-3">
            <div className="dhan-logo-wrap shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/dhanbuddy-logo.svg" alt="DhanBuddy" className="size-10" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <p className="truncate text-lg font-black tracking-tight text-violet-950 dark:text-white">
                  DhanBuddy
                </p>
                <span className="hidden rounded-full bg-yellow-300 px-2 py-0.5 text-[9px] font-black tracking-wider text-violet-950 uppercase sm:inline">
                  Live plan
                </span>
              </div>
              <p className="truncate text-[10px] font-bold tracking-[0.14em] text-fuchsia-600 uppercase dark:text-fuchsia-300">
                Your dream, mapped in rupees
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-2 md:flex">
            <div className="dhan-stream-badge">
              <Radio className="size-3.5" /> Real-time voice pipeline
            </div>
            <div className="dhan-state-pill" data-state={agentState} aria-live="polite">
              <span className="dhan-state-dot" />
              {state.label}
            </div>
          </div>

          <button type="button" onClick={() => session.end()} className="dhan-end-call">
            <CircleStop className="size-4" />
            <span className="hidden sm:inline">End session</span>
            <span className="sm:hidden">End</span>
          </button>
        </header>

        <main className="mt-3 grid gap-3 xl:grid-cols-[190px_minmax(0,1fr)_300px]">
          <aside className="dhan-journey-rail order-2 xl:order-1">
            <div>
              <p className="dhan-eyebrow">Savings journey</p>
              <p className="mt-2 text-xl font-black tracking-tight text-violet-950 dark:text-white">
                From dream to doable.
              </p>
            </div>
            <div className="mt-6 grid grid-cols-5 gap-2 xl:grid-cols-1 xl:gap-0">
              {JOURNEY.map((step, index) => {
                const done = index < completedSteps;
                const active = index === completedSteps;
                return (
                  <div
                    key={step}
                    className="relative flex flex-col items-center xl:min-h-16 xl:flex-row xl:items-start xl:gap-3"
                  >
                    {index < JOURNEY.length - 1 && (
                      <span className={cn('dhan-journey-line', done && 'is-done')} />
                    )}
                    <span
                      className={cn('dhan-journey-node', done && 'is-done', active && 'is-active')}
                    >
                      {done ? '✓' : index + 1}
                    </span>
                    <div className="mt-2 text-center xl:mt-1 xl:text-left">
                      <p
                        className={cn(
                          'text-[10px] font-black tracking-wider uppercase xl:text-xs',
                          done || active ? 'text-violet-950 dark:text-white' : 'text-violet-400'
                        )}
                      >
                        {step}
                      </p>
                      <p className="mt-0.5 hidden text-[10px] text-violet-500/70 xl:block">
                        {done ? 'Captured' : active ? 'Up next' : 'Waiting'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-auto hidden rounded-3xl bg-violet-950 p-4 text-white xl:block">
              <LockKeyhole className="size-4 text-yellow-300" />
              <p className="mt-3 text-xs font-black">Keep secrets secret</p>
              <p className="mt-1.5 text-[10px] leading-4 text-violet-200">
                Never share OTP, PIN, account or card details.
              </p>
            </div>
          </aside>

          <section className="dhan-conversation-stage order-1 xl:order-2">
            <div className="dhan-conversation-topline">
              <div className="flex items-center gap-3">
                <div className="dhan-mini-pulse" data-state={agentState}>
                  <StateIcon className="size-4" />
                </div>
                <div>
                  <p className="text-sm font-black text-violet-950 dark:text-white">
                    {state.label}
                  </p>
                  <p className="text-[11px] font-medium text-violet-500 dark:text-violet-300/70">
                    {state.detail}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setChatOpen((value) => !value)}
                className="dhan-icon-button"
                aria-label={chatOpen ? 'Hide transcript' : 'Show transcript'}
              >
                <MessageSquareText className="size-4" />
              </button>
            </div>

            <AnimatePresence mode="wait">
              {chatOpen ? (
                <motion.div
                  key="conversation"
                  ref={transcriptRef}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="dhan-flowing-transcript"
                >
                  {messages.length === 0 && isPreConnectBufferEnabled ? (
                    <div className="flex min-h-[360px] flex-col justify-center px-5 py-10 sm:px-12">
                      <p className="dhan-eyebrow">Conversation canvas</p>
                      <h2 className="mt-4 max-w-xl text-3xl leading-tight font-black tracking-[-0.04em] text-violet-950 sm:text-5xl dark:text-white">
                        {preConnectMessage}
                      </h2>
                      <p className="mt-4 max-w-lg text-sm leading-6 font-medium text-violet-600/70 dark:text-violet-200/60">
                        Speak naturally in English, Hindi, or Hinglish. Your words and DhanBuddy’s
                        reply will flow here as readable text.
                      </p>
                      <div className="mt-8 flex items-center gap-2 text-xs font-black text-fuchsia-600 dark:text-fuchsia-300">
                        <ArrowDown className="size-4 animate-bounce" /> Live transcript appears
                        below
                      </div>
                    </div>
                  ) : (
                    <AgentChatTranscript
                      agentState={agentState}
                      messages={messages}
                      className="min-h-[400px] [&_.is-user>div]:rounded-[22px_22px_5px_22px] [&>div>div]:px-5 [&>div>div]:py-6 sm:[&>div>div]:px-8"
                    />
                  )}
                </motion.div>
              ) : (
                <motion.div
                  key="hidden"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="grid min-h-[400px] place-items-center p-8 text-center"
                >
                  <div>
                    <LockKeyhole className="mx-auto size-9 text-fuchsia-500" />
                    <p className="mt-4 font-black text-violet-950 dark:text-white">
                      Transcript hidden for privacy
                    </p>
                    <p className="mt-2 text-xs text-violet-500">
                      Select the message button to bring it back.
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <div className="dhan-dock">
              <div className="hidden items-center gap-2 sm:flex">
                <span
                  className={cn('dhan-speaker-tag', agentState === 'listening' && 'is-active-user')}
                >
                  <Mic className="size-3.5" /> You
                </span>
                <span
                  className={cn('dhan-speaker-tag', agentState === 'speaking' && 'is-active-agent')}
                >
                  <Volume2 className="size-3.5" /> DhanBuddy
                </span>
              </div>
              <AgentControlBar
                variant="livekit"
                controls={controls}
                isChatOpen={chatOpen}
                isConnected={session.isConnected}
                onIsChatOpenChange={setChatOpen}
                className="dhan-compact-controls"
              />
              <p className="hidden text-[10px] font-bold text-violet-500 lg:block">
                Say “bye” to finish
              </p>
            </div>
          </section>

          <aside className="order-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            {toolActivity.length > 0 && (
              <div className="dhan-tool-monitor sm:col-span-2 xl:col-span-1" aria-live="polite">
                <div className="flex items-center justify-between">
                  <p className="dhan-eyebrow">Live tool activity</p>
                  <span className="text-[9px] font-black tracking-wider text-slate-400 uppercase">
                    Function calls
                  </span>
                </div>
                <div className="mt-3 space-y-2">
                  {toolActivity.map((activity) => (
                    <div
                      key={activity.tool}
                      className="dhan-tool-event"
                      data-status={activity.status}
                    >
                      <span className="dhan-tool-event-dot" />
                      <div>
                        <p>{activity.tool.replaceAll('_', ' ')}</p>
                        <span>{activity.message}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {scenarioResult && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="dhan-result-panel sm:col-span-2 xl:col-span-1"
                aria-live="polite"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="dhan-eyebrow">Your options</p>
                    <p className="mt-1 text-sm font-black text-slate-950 dark:text-white">
                      Savings gap comparison
                    </p>
                  </div>
                  <span className="dhan-result-status">
                    {scenarioResult.on_track ? 'On track' : 'Gap found'}
                  </span>
                </div>
                <div className="mt-4 grid gap-2">
                  <div className="dhan-result-row">
                    <IndianRupee className="size-4" />
                    <div>
                      <p>Current path</p>
                      <strong>{formatRupees(scenarioResult.current_projected_amount)}</strong>
                      <span> by {scenarioResult.current_months} months</span>
                    </div>
                  </div>
                  <div className="dhan-result-row">
                    <TrendingUp className="size-4" />
                    <div>
                      <p>Monthly path</p>
                      <strong>{formatRupees(scenarioResult.required_monthly_saving)}</strong>
                      <span> needed each month</span>
                    </div>
                  </div>
                  <div className="dhan-result-row">
                    <CalendarClock className="size-4" />
                    <div>
                      <p>More-time path</p>
                      <strong>
                        {scenarioResult.deadline_extension_months === null
                          ? 'Needs monthly savings'
                          : `${scenarioResult.deadline_extension_months} extra months`}
                      </strong>
                      <span> at the current monthly amount</span>
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-[9px] leading-4 text-slate-400">
                  Calculated {new Date(scenarioResult.calculated_at).toLocaleString()} · Zero
                  investment returns
                </p>
              </motion.div>
            )}

            <div className="dhan-voice-orbit" data-state={agentState}>
              <div className="dhan-orbit-ring" />
              <AudioVisualizer
                isChatOpen={false}
                audioVisualizerType={audioVisualizerType}
                audioVisualizerColor={audioVisualizerColor}
                audioVisualizerColorShift={audioVisualizerColorShift}
                audioVisualizerBarCount={audioVisualizerBarCount}
                audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
                audioVisualizerRadialRadius={audioVisualizerRadialRadius}
                audioVisualizerGridRowCount={audioVisualizerGridRowCount}
                audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
                audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
                className="relative z-10 !size-[190px]"
                style={{ color: audioVisualizerColor }}
              />
              <div className="pointer-events-none absolute inset-0 grid place-items-center">
                <IndianRupee className="size-8 text-violet-950 dark:text-white" />
              </div>
              <div className="absolute right-4 bottom-4 left-4 text-center">
                <p className="text-xs font-black text-violet-950 dark:text-white">Voice pulse</p>
                <p className="text-[10px] text-violet-500">Moves with the conversation</p>
              </div>
            </div>

            <div className="dhan-pipeline-card">
              <div className="flex items-center justify-between">
                <p className="dhan-eyebrow">Fast voice flow</p>
                <AudioLines className="size-4 text-fuchsia-500" />
              </div>
              <div className="mt-4 space-y-2">
                {PIPELINE.map((item, index) => (
                  <div key={item} className="dhan-pipeline-step">
                    <span>{index + 1}</span>
                    <p>{item}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded-2xl bg-yellow-300 p-3 text-violet-950">
                <p className="text-[10px] font-black tracking-wider uppercase">
                  Streaming response
                </p>
                <p className="mt-1 text-[11px] font-semibold">
                  Audio starts as the reply is generated.
                </p>
              </div>
            </div>

            <div className="dhan-memory-card sm:col-span-2 xl:col-span-1">
              <div className="flex items-center gap-2">
                <LockKeyhole className="size-4 text-violet-700 dark:text-violet-300" />
                <p className="text-xs font-black text-violet-950 dark:text-white">
                  Memory is consent-only
                </p>
              </div>
              <p className="mt-2 text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                DhanBuddy asks before remembering your name or savings plan. Say “forget me” to
                remove saved data.
              </p>
            </div>
          </aside>
        </main>
      </div>
    </section>
  );
}
