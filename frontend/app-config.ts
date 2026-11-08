export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Voice for Bharat',
  pageTitle: 'Real-Time Study Companion',
  pageDescription:
    '7th-Semester CS Professor & Exam Study Buddy — Powered by Murf Falcon TTS & Google Gemini',

  supportsChatInput: true,
  supportsVideoInput: true,
  supportsScreenShare: true,
  isPreConnectBufferEnabled: true,

  logo: '/murf-logo.svg',
  accent: '#6366F1',
  logoDark: '/murf-logo-dark.svg',
  accentDark: '#818cf8',
  startButtonText: 'Start revision session',

  // optional: audio visualization configuration
  audioVisualizerType: 'wave',
  audioVisualizerColor: '#6366f1',
  audioVisualizerColorDark: '#818cf8',
  audioVisualizerColorShift: 0.3,
  audioVisualizerWaveLineWidth: 2,

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? 'my-agent',

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};
