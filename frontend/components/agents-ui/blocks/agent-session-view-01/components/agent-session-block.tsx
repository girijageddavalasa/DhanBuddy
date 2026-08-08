'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Headphones, LockKeyhole, MessageSquareText, Mic, Sparkles, Volume2 } from 'lucide-react';
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
  disconnected: {
    label: 'Connecting',
    detail: 'DhanBuddy is joining your session',
    icon: Sparkles,
  },
  connecting: {
    label: 'Connecting',
    detail: 'DhanBuddy is joining your session',
    icon: Sparkles,
  },
  initializing: {
    label: 'Connecting',
    detail: 'DhanBuddy is getting ready',
    icon: Sparkles,
  },
  listening: { label: 'Listening', detail: 'Listening to you', icon: Mic },
  thinking: { label: 'Thinking', detail: 'Working out a clear answer', icon: Headphones },
  speaking: { label: 'Speaking', detail: 'DhanBuddy is speaking', icon: Volume2 },
  failed: { label: 'Call ended', detail: 'The agent could not continue', icon: Sparkles },
} as const;

export function AgentSessionView_01({
  preConnectMessage = 'DhanBuddy is ready. Tell me what you are saving for.',
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
  const transcriptRef = useRef<HTMLDivElement>(null);
  const state = STATE_COPY[agentState as keyof typeof STATE_COPY] ?? STATE_COPY.connecting;
  const StateIcon = state.icon;

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <section
      ref={ref}
      className={cn('dhan-page z-10 h-full w-full overflow-y-auto', className)}
      {...props}
    >
      <div className="mx-auto flex min-h-full max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="dhan-logo-wrap">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/dhanbuddy-logo.svg" alt="DhanBuddy" className="size-10" />
            </div>
            <div>
              <p className="text-lg font-black tracking-tight text-violet-950 dark:text-white">
                DhanBuddy
              </p>
              <p className="text-[10px] font-black tracking-[0.18em] text-fuchsia-600 uppercase dark:text-fuchsia-400">
                Private voice session
              </p>
            </div>
          </div>

          <div className="dhan-state-pill" data-state={agentState} aria-live="polite">
            <span className="dhan-state-dot" />
            {state.label}
          </div>
        </header>

        <main className="grid flex-1 items-center gap-5 py-5 lg:grid-cols-[minmax(0,1fr)_330px]">
          <div className="dhan-card flex min-h-[590px] flex-col overflow-hidden p-4 sm:p-6">
            <div className="flex items-center justify-between border-b border-violet-100 pb-4 dark:border-white/10">
              <div className="flex items-center gap-3">
                <div className="grid size-11 place-items-center rounded-2xl bg-gradient-to-br from-amber-300 to-yellow-500 text-violet-950 shadow-md">
                  <StateIcon className="size-5" />
                </div>
                <div>
                  <p className="text-xs font-black tracking-[0.14em] text-fuchsia-600 uppercase dark:text-fuchsia-400">
                    {state.label}
                  </p>
                  <p className="mt-0.5 text-sm font-bold text-violet-950 dark:text-white">
                    {state.detail}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setChatOpen((open) => !open)}
                className="grid size-10 place-items-center rounded-xl border border-violet-200 bg-white text-violet-700 transition hover:border-fuchsia-300 hover:text-fuchsia-600 dark:border-white/10 dark:bg-white/5 dark:text-violet-200"
                aria-label={chatOpen ? 'Hide transcript' : 'Show transcript'}
              >
                <MessageSquareText className="size-5" />
              </button>
            </div>

            <div className="grid flex-1 items-center gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
              <div className="flex flex-col items-center justify-center py-6">
                <div className="dhan-visualizer-shell" data-state={agentState}>
                  <div className="dhan-visualizer-glow" />
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
                    className="relative z-10 !size-[220px] sm:!size-[250px]"
                    style={{ color: audioVisualizerColor }}
                  />
                  <div className="pointer-events-none absolute inset-0 grid place-items-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src="/dhanbuddy-logo.svg"
                      alt=""
                      className="size-16 rounded-2xl bg-white/90 p-2 shadow-xl"
                    />
                  </div>
                </div>

                <p className="mt-4 text-center text-sm font-black text-violet-950 dark:text-white">
                  {state.detail}
                </p>
                <div className="mt-3 flex items-center gap-4 text-xs font-bold">
                  <span
                    className={cn(
                      'flex items-center gap-1.5 rounded-full px-3 py-1.5',
                      agentState === 'listening'
                        ? 'bg-amber-200 text-amber-950'
                        : 'bg-violet-100 text-violet-500 dark:bg-white/10 dark:text-violet-300'
                    )}
                  >
                    <Mic className="size-3.5" /> You
                  </span>
                  <span
                    className={cn(
                      'flex items-center gap-1.5 rounded-full px-3 py-1.5',
                      agentState === 'speaking'
                        ? 'bg-fuchsia-600 text-white'
                        : 'bg-violet-100 text-violet-500 dark:bg-white/10 dark:text-violet-300'
                    )}
                  >
                    <Volume2 className="size-3.5" /> DhanBuddy
                  </span>
                </div>
              </div>

              <AnimatePresence mode="wait">
                {chatOpen ? (
                  <motion.div
                    key="transcript"
                    ref={transcriptRef}
                    initial={{ opacity: 0, x: 8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 8 }}
                    className="h-[300px] overflow-y-auto rounded-3xl border border-violet-100 bg-violet-50/60 lg:h-[390px] dark:border-white/10 dark:bg-black/10"
                  >
                    {messages.length === 0 && isPreConnectBufferEnabled ? (
                      <div className="grid h-full place-items-center p-8 text-center">
                        <div>
                          <div className="mx-auto mb-3 grid size-11 place-items-center rounded-2xl bg-white text-fuchsia-600 shadow-sm dark:bg-white/10 dark:text-fuchsia-300">
                            <Sparkles className="size-5" />
                          </div>
                          <p className="text-sm font-black text-violet-950 dark:text-white">
                            {preConnectMessage}
                          </p>
                          <p className="mt-2 text-xs leading-5 font-medium text-violet-700/60 dark:text-violet-200/60">
                            Your conversation will appear here.
                          </p>
                        </div>
                      </div>
                    ) : (
                      <AgentChatTranscript
                        agentState={agentState}
                        messages={messages}
                        className="h-full [&_.is-user>div]:rounded-[20px] [&>div>div]:px-4 [&>div>div]:py-5"
                      />
                    )}
                  </motion.div>
                ) : (
                  <motion.div
                    key="privacy"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="grid h-[300px] place-items-center rounded-3xl border border-dashed border-violet-200 bg-white/40 p-8 text-center lg:h-[390px] dark:border-white/10 dark:bg-white/5"
                  >
                    <div>
                      <LockKeyhole className="mx-auto size-8 text-violet-500" />
                      <p className="mt-3 text-sm font-black text-violet-950 dark:text-white">
                        Transcript hidden
                      </p>
                      <p className="mt-2 text-xs text-violet-700/60 dark:text-violet-200/60">
                        Select the message icon to show it again.
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="border-t border-violet-100 pt-4 dark:border-white/10">
              <AgentControlBar
                variant="livekit"
                controls={controls}
                isChatOpen={chatOpen}
                isConnected={session.isConnected}
                onDisconnect={session.end}
                onIsChatOpenChange={setChatOpen}
                className="mx-auto"
              />
              <p className="mt-3 text-center text-[11px] font-bold tracking-wide text-violet-700/50 dark:text-violet-200/50">
                Say “bye” anytime to end the call
              </p>
            </div>
          </div>

          <aside className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <div className="dhan-card p-5">
              <p className="text-xs font-black tracking-[0.15em] text-fuchsia-600 uppercase dark:text-fuchsia-400">
                Your conversation path
              </p>
              <div className="mt-4 space-y-3">
                {[
                  'Your savings goal',
                  'Target and deadline',
                  'Current and monthly savings',
                  'Simple estimate',
                ].map((step, index) => (
                  <div key={step} className="flex items-center gap-3">
                    <span className="grid size-7 shrink-0 place-items-center rounded-full bg-violet-100 text-xs font-black text-violet-700 dark:bg-violet-400/15 dark:text-violet-200">
                      {index + 1}
                    </span>
                    <span className="text-xs font-bold text-violet-900/70 dark:text-violet-100/70">
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[28px] border border-amber-300/70 bg-gradient-to-br from-amber-100 to-yellow-50 p-5 shadow-sm dark:border-amber-300/20 dark:from-amber-400/15 dark:to-yellow-400/5">
              <div className="flex items-center gap-2 text-amber-950 dark:text-amber-100">
                <LockKeyhole className="size-4" />
                <p className="text-xs font-black tracking-[0.12em] uppercase">Privacy reminder</p>
              </div>
              <p className="mt-3 text-xs leading-5 font-semibold text-amber-950/70 dark:text-amber-100/70">
                Never share an OTP, PIN, password, account number, Aadhaar number or card details.
              </p>
            </div>

            <div className="rounded-[28px] bg-gradient-to-br from-violet-700 to-fuchsia-600 p-5 text-white shadow-xl shadow-fuchsia-500/10 sm:col-span-2 lg:col-span-1">
              <Sparkles className="size-5 text-yellow-300" />
              <p className="mt-3 text-sm font-black">Educational, not advisory</p>
              <p className="mt-2 text-xs leading-5 font-medium text-white/70">
                DhanBuddy assumes no investment returns and never recommends financial products.
              </p>
            </div>
          </aside>
        </main>
      </div>
    </section>
  );
}
