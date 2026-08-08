'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { ConnectionState } from 'livekit-client';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS: MotionProps = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.35, ease: 'easeOut' },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const { resolvedTheme } = useTheme();
  const [startRequested, setStartRequested] = useState(false);
  const [isRequestingMicrophone, setIsRequestingMicrophone] = useState(false);
  const [callEnded, setCallEnded] = useState(false);
  const [microphoneError, setMicrophoneError] = useState<string | null>(null);
  const wasConnected = useRef(false);

  useEffect(() => {
    if (session.isConnected) {
      wasConnected.current = true;
      return;
    }
    if (wasConnected.current && session.connectionState === ConnectionState.Disconnected) {
      setCallEnded(true);
      setStartRequested(false);
      wasConnected.current = false;
    }
  }, [session.connectionState, session.isConnected]);

  const startCall = useCallback(async () => {
    setMicrophoneError(null);
    setCallEnded(false);
    setStartRequested(true);
    setIsRequestingMicrophone(true);

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('This browser cannot access a microphone.');
      }
      const previewStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      previewStream.getTracks().forEach((track) => track.stop());
      await session.start();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Microphone permission was denied.';
      setMicrophoneError(message);
      setStartRequested(false);
    } finally {
      setIsRequestingMicrophone(false);
    }
  }, [session]);

  const isConnecting =
    isRequestingMicrophone ||
    (startRequested && session.connectionState === ConnectionState.Connecting);

  return (
    <AnimatePresence mode="wait">
      {!session.isConnected && (
        <MotionWelcomeView
          key={callEnded ? 'ended' : 'welcome'}
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={startCall}
          isConnecting={isConnecting}
          isEnded={callEnded}
          microphoneError={microphoneError}
        />
      )}

      {session.isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          preConnectMessage="DhanBuddy is ready. Tell me what you are saving for."
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
