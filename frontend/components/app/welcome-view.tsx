'use client';

import { ArrowRight, LockKeyhole, Mic, RotateCcw, ShieldCheck, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  isConnecting?: boolean;
  isEnded?: boolean;
  microphoneError?: string | null;
}

const FEATURES = [
  { icon: Sparkles, label: 'Simple goal estimate' },
  { icon: ShieldCheck, label: 'Privacy-first guidance' },
  { icon: Mic, label: 'English, Hindi & Hinglish' },
];

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  isConnecting = false,
  isEnded = false,
  microphoneError,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="dhan-page min-h-svh overflow-y-auto px-4 py-6 sm:px-6 lg:py-10">
      <div className="mx-auto flex min-h-[calc(100svh-3rem)] max-w-6xl flex-col">
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
              <p className="text-[11px] font-bold tracking-[0.18em] text-fuchsia-600 uppercase">
                Voice savings planner
              </p>
            </div>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-violet-200 bg-white/70 px-4 py-2 text-xs font-bold text-violet-800 shadow-sm backdrop-blur sm:flex dark:border-white/10 dark:bg-white/5 dark:text-violet-100">
            <span className="size-2 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.12)]" />
            Educational estimates only
          </div>
        </header>

        <main className="grid min-w-0 flex-1 items-center gap-10 py-10 lg:grid-cols-[minmax(0,1fr)_400px] lg:gap-8 lg:py-12">
          <section className="max-w-2xl min-w-0">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-100/80 px-3 py-1.5 text-xs font-black tracking-wide text-amber-900 uppercase dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200">
              <Sparkles className="size-3.5" />
              Financial Services · VoiceForBharat
            </div>

            <h1 className="text-5xl leading-[0.98] font-black tracking-[-0.055em] text-balance text-violet-950 sm:text-6xl dark:text-white">
              Make your savings goal <span className="dhan-gradient-text">feel possible.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 font-medium text-violet-900/70 sm:text-lg dark:text-violet-100/70">
              Tell DhanBuddy your goal, deadline and monthly savings. Get a clear, zero-return
              estimate in a natural Indian voice.
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              {FEATURES.map(({ icon: Icon, label }) => (
                <div
                  key={label}
                  className="flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/65 px-3 py-2 text-xs font-bold text-violet-800 backdrop-blur dark:border-white/10 dark:bg-white/5 dark:text-violet-100"
                >
                  <Icon className="size-4 text-fuchsia-600 dark:text-fuchsia-400" />
                  {label}
                </div>
              ))}
            </div>
          </section>

          <section className="relative mx-auto w-full max-w-md min-w-0">
            <div className="dhan-orbit dhan-orbit-one" />
            <div className="dhan-orbit dhan-orbit-two" />
            <div className="dhan-card relative z-10 p-6 sm:p-8">
              <div className="mb-7 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      'grid size-12 place-items-center rounded-2xl shadow-lg',
                      isEnded
                        ? 'bg-violet-100 text-violet-700 dark:bg-violet-400/15 dark:text-violet-200'
                        : 'bg-gradient-to-br from-amber-300 to-yellow-500 text-violet-950'
                    )}
                  >
                    {isEnded ? <RotateCcw className="size-6" /> : <Mic className="size-6" />}
                  </div>
                  <div>
                    <p className="text-xs font-black tracking-[0.16em] text-fuchsia-600 uppercase dark:text-fuchsia-400">
                      {isEnded ? 'Call ended' : isConnecting ? 'Connecting' : 'Ready'}
                    </p>
                    <p className="mt-1 text-sm font-bold text-violet-950 dark:text-white">
                      {isEnded
                        ? 'Plan another goal anytime'
                        : isConnecting
                          ? 'Joining your private session'
                          : 'Your goal. One simple conversation.'}
                    </p>
                  </div>
                </div>
                <div className="dhan-sound-dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
              </div>

              {microphoneError && (
                <div
                  role="alert"
                  className="mb-5 rounded-2xl border border-rose-300 bg-rose-50 p-4 text-left dark:border-rose-400/30 dark:bg-rose-400/10"
                >
                  <p className="text-sm font-black text-rose-900 dark:text-rose-100">
                    Microphone access is blocked
                  </p>
                  <p className="mt-1 text-xs leading-5 font-medium text-rose-800/80 dark:text-rose-100/70">
                    {microphoneError} Select the lock icon near the address bar, allow Microphone,
                    then try again.
                  </p>
                </div>
              )}

              <Button
                size="lg"
                onClick={onStartCall}
                disabled={isConnecting}
                className="dhan-primary-button h-14 w-full rounded-2xl text-sm font-black tracking-wide"
              >
                {isConnecting ? (
                  <>
                    <span className="dhan-spinner" />
                    Connecting… please wait
                  </>
                ) : (
                  <>
                    {isEnded ? 'Start again' : startButtonText}
                    <ArrowRight className="size-5" />
                  </>
                )}
              </Button>

              <div className="mt-5 flex items-start gap-3 rounded-2xl bg-violet-50/80 p-4 dark:bg-violet-400/10">
                <LockKeyhole className="mt-0.5 size-4 shrink-0 text-violet-700 dark:text-violet-300" />
                <p className="text-xs leading-5 font-semibold text-violet-900/70 dark:text-violet-100/70">
                  Never share an OTP, PIN, password, account number or card details. DhanBuddy will
                  never ask for them.
                </p>
              </div>
            </div>
          </section>
        </main>

        <footer className="flex flex-col gap-2 border-t border-violet-200/70 pt-5 text-xs font-semibold text-violet-800/60 sm:flex-row sm:items-center sm:justify-between dark:border-white/10 dark:text-violet-100/50">
          <p>Powered by Murf Falcon · LiveKit · Deepgram · Gemini</p>
          <p>Educational estimate · No investment returns assumed</p>
        </footer>
      </div>
    </div>
  );
};
