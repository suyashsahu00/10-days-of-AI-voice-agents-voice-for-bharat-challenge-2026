'use client';

import { useEffect, useRef, useState } from 'react';

interface Particle {
  t: number;
  jitter: number;
  size: number;
  phase: number;
  twinkleSpeed: number;
}

interface Stream {
  sx: number;
  sy: number;
  c1x: number;
  c1y: number;
  c2x: number;
  c2y: number;
  ex: number;
  ey: number;
  hue: number;
  particles: Particle[];
  width: number;
}

interface BokehCircle {
  x: number;
  y: number;
  r: number;
  hue: number;
  phase: number;
  speed: number;
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  wasConnected?: boolean;
}

const STATUS_COPY = {
  ready: {
    pill: 'Ready',
    status: 'Aaj kaunsa concept todna hai?',
    dotPulse: false,
  },
  connecting: {
    pill: 'Connecting',
    status: 'Sydney se connect ho raha hai, ek second...',
    dotPulse: true,
  },
  ended: {
    pill: 'Call ended',
    status: 'Session khatam. Phir se shuru karna hai?',
    dotPulse: false,
  },
};

const STATE_MOD = {
  ready: { speed: 0.5, glow: 1.1 },
  connecting: { speed: 0.8, glow: 1.3 },
  ended: { speed: 0.15, glow: 0.7 },
};

const SYDNEY_STYLES = `
  .sydney-welcome {
    --ink: #f2f3f7;
    --ink-dim: rgba(242, 243, 247, 0.72);
    --ink-faint: rgba(242, 243, 247, 0.48);
    --glass-bg: rgba(18, 18, 26, 0.4);
    --glass-border: rgba(255, 255, 255, 0.13);
    --bg: #050507;

    /* state accent colors — swap glow tint + label */
    --c-ready: #8fa4ff;
    --c-connecting: #ffd166;
    --c-listening: #7ee8c8;
    --c-speaking: #ff8fb3;
    --c-ended: #9a9aa5;

    position: relative;
    min-height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: hidden;
    background: var(--bg);
    color: var(--ink);
    font-family: 'Helvetica Neue', Arial, sans-serif;
  }

  .sydney-welcome canvas#field {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    display: block;
  }

  .sydney-welcome .vignette {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(ellipse at 50% 46%, transparent 30%, rgba(0,0,0,0.6) 100%);
  }

  .sydney-welcome nav {
    position: relative;
    z-index: 5;
    width: 100%;
    max-width: 1400px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 22px 40px;
  }

  .sydney-welcome .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    font-size: 1.05rem;
  }

  .sydney-welcome .brand .mark {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 1.5px solid var(--ink-dim);
    position: relative;
  }

  .sydney-welcome .brand .mark::after {
    content: '';
    position: absolute;
    inset: 5px;
    border-radius: 50%;
    background: var(--ink-dim);
  }

  .sydney-welcome .navlinks {
    display: flex;
    gap: 34px;
    font-size: 0.9rem;
    color: var(--ink-dim);
  }

  .sydney-welcome .navlinks a {
    color: inherit;
    text-decoration: none;
  }

  @media (max-width: 720px) {
    .sydney-welcome .navlinks {
      display: none;
    }
  }

  .sydney-welcome .navright {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.85rem;
    color: var(--ink-dim);
  }

  .sydney-welcome main {
    position: relative;
    z-index: 5;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 30px 24px 60px;
    width: 100%;
  }

  .sydney-welcome h1 {
    font-family: 'Georgia', 'Iowan Old Style', serif;
    font-size: clamp(2.1rem, 5.4vw, 4.2rem);
    font-weight: 400;
    line-height: 1.1;
    letter-spacing: -0.3px;
    max-width: 20ch;
    text-shadow: 0 4px 30px rgba(0,0,0,0.6);
  }

  .sydney-welcome h1 em {
    font-style: italic;
  }

  .sydney-welcome .sub {
    margin-top: 18px;
    color: var(--ink-dim);
    font-size: 0.98rem;
    line-height: 1.6;
    max-width: 46ch;
  }

  .sydney-welcome .greet {
    margin-top: 30px;
  }

  .sydney-welcome .greet .hi {
    font-size: 1.1rem;
    font-weight: 600;
  }

  .sydney-welcome .greet .status-line {
    color: var(--ink-faint);
    font-size: 0.92rem;
    margin-top: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .sydney-welcome .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--state-color, var(--c-ready));
    box-shadow: 0 0 10px var(--state-color, var(--c-ready));
  }

  .sydney-welcome .status-dot.pulse {
    animation: sydney-dotpulse 1.1s ease-in-out infinite;
  }

  @keyframes sydney-dotpulse {
    0%, 100% {
      opacity: 0.5;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.3);
    }
  }

  .sydney-welcome .orb-wrap {
    margin-top: 36px;
    position: relative;
    width: 150px;
    height: 150px;
  }

  .sydney-welcome .ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 1px solid color-mix(in srgb, var(--state-color, var(--c-ready)) 55%, transparent);
    opacity: 0;
    transform: scale(0.8);
  }

  .sydney-welcome .orb-wrap.active-listening .ring,
  .sydney-welcome .orb-wrap.active-speaking .ring,
  .sydney-welcome .orb-wrap.active-connecting .ring {
    animation: sydney-ringpulse 1.8s ease-out infinite;
  }

  .sydney-welcome .ring:nth-child(2) {
    animation-delay: 0.5s !important;
  }

  .sydney-welcome .ring:nth-child(3) {
    animation-delay: 1s !important;
  }

  @keyframes sydney-ringpulse {
    0% {
      opacity: 0.55;
      transform: scale(0.75);
    }
    100% {
      opacity: 0;
      transform: scale(1.7);
    }
  }

  .sydney-welcome .mic {
    position: relative;
    width: 118px;
    height: 118px;
    margin: 16px;
    border-radius: 50%;
    border: 1px solid var(--glass-border);
    background: radial-gradient(circle at 35% 30%, rgba(255,255,255,0.09), rgba(18,18,26,0.5));
    backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: transform 0.25s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    box-shadow: 0 0 0px var(--state-color, var(--c-ready));
  }

  .sydney-welcome .mic:hover {
    transform: scale(1.03);
  }

  .sydney-welcome .mic.state-connecting {
    box-shadow: 0 0 30px color-mix(in srgb, var(--c-connecting) 60%, transparent);
  }

  .sydney-welcome .mic.state-listening {
    box-shadow: 0 0 34px color-mix(in srgb, var(--c-listening) 60%, transparent);
  }

  .sydney-welcome .mic.state-speaking {
    box-shadow: 0 0 34px color-mix(in srgb, var(--c-speaking) 60%, transparent);
  }

  .sydney-welcome .mic svg {
    width: 28px;
    height: 28px;
    opacity: 0.92;
  }

  .sydney-welcome .mic .spinner {
    position: absolute;
    inset: -1px;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: var(--c-connecting);
    display: none;
  }

  .sydney-welcome .mic.state-connecting .spinner {
    display: block;
    animation: sydney-spin 0.9s linear infinite;
  }

  .sydney-welcome .mic.state-connecting svg {
    opacity: 0.4;
  }

  @keyframes sydney-spin {
    to {
      transform: rotate(360deg);
    }
  }

  .sydney-welcome .bars {
    display: none;
    align-items: flex-end;
    gap: 3px;
    height: 22px;
  }

  .sydney-welcome .mic.state-speaking .bars {
    display: flex;
  }

  .sydney-welcome .mic.state-speaking svg {
    display: none;
  }

  .sydney-welcome .bars span {
    width: 3px;
    background: var(--ink);
    border-radius: 2px;
    animation: sydney-barbounce 0.9s ease-in-out infinite;
  }

  .sydney-welcome .bars span:nth-child(1) {
    height: 10px;
    animation-delay: 0s;
  }

  .sydney-welcome .bars span:nth-child(2) {
    height: 20px;
    animation-delay: 0.15s;
  }

  .sydney-welcome .bars span:nth-child(3) {
    height: 14px;
    animation-delay: 0.3s;
  }

  .sydney-welcome .bars span:nth-child(4) {
    height: 22px;
    animation-delay: 0.45s;
  }

  .sydney-welcome .bars span:nth-child(5) {
    height: 12px;
    animation-delay: 0.6s;
  }

  @keyframes sydney-barbounce {
    0%, 100% {
      transform: scaleY(0.4);
    }
    50% {
      transform: scaleY(1);
    }
  }

  .sydney-welcome .primary-btn {
    margin-top: 22px;
    font-size: 0.95rem;
    color: var(--ink);
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    padding: 10px 24px;
    border-radius: 999px;
    cursor: pointer;
    backdrop-filter: blur(8px);
    transition: border-color 0.25s;
  }

  .sydney-welcome .primary-btn:hover {
    border-color: var(--state-color, var(--c-ready));
  }

  .sydney-welcome .primary-btn.ghost {
    background: transparent;
  }

  .sydney-welcome .langs {
    margin-top: 16px;
    display: flex;
    gap: 10px;
    font-size: 0.8rem;
    color: var(--ink-faint);
  }

  .sydney-welcome .langs span:not(:last-child)::after {
    content: '·';
    margin-left: 10px;
    opacity: 0.5;
  }

  .sydney-welcome .bubble {
    margin-top: 28px;
    width: min(560px, 92vw);
    border: 1px solid var(--glass-border);
    background: var(--glass-bg);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 18px 22px;
    text-align: left;
  }

  .sydney-welcome .bubble .tag {
    font-size: 0.66rem;
    letter-spacing: 1.5px;
    color: var(--ink-faint);
    font-weight: 700;
  }

  .sydney-welcome .bubble .line {
    margin-top: 8px;
    font-size: 1rem;
    font-weight: 500;
    line-height: 1.5;
  }

  .sydney-welcome .mode {
    margin-top: 20px;
    font-size: 0.76rem;
    color: var(--ink-faint);
    border: 1px solid var(--glass-border);
    border-radius: 999px;
    padding: 6px 16px;
    background: rgba(255, 255, 255, 0.02);
  }

  .sydney-welcome .mic-error {
    display: none;
    margin-top: 22px;
    width: min(520px, 92vw);
    border: 1px solid rgba(255, 120, 120, 0.35);
    background: rgba(60, 20, 20, 0.35);
    border-radius: 14px;
    padding: 16px 20px;
    text-align: left;
    font-size: 0.88rem;
    color: var(--ink-dim);
    line-height: 1.55;
  }

  .sydney-welcome .mic-error.visible {
    display: block;
  }

  .sydney-welcome .mic-error strong {
    color: #ffb3b3;
    display: block;
    margin-bottom: 4px;
    font-size: 0.9rem;
  }

  .sydney-welcome footer.hint {
    position: relative;
    z-index: 5;
    padding: 16px;
    text-align: center;
    font-size: 0.72rem;
    color: var(--ink-faint);
  }

  @media (prefers-reduced-motion: reduce) {
    .sydney-welcome .ring,
    .sydney-welcome .status-dot.pulse,
    .sydney-welcome .bars span,
    .sydney-welcome .mic .spinner {
      animation: none !important;
    }
  }

  body:has(.sydney-welcome) header {
    display: none !important;
  }
`;

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  wasConnected = false,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [state, setState] = useState<'ready' | 'connecting' | 'ended'>(
    wasConnected ? 'ended' : 'ready'
  );
  const [micBlocked, setMicBlocked] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  useEffect(() => {
    if (wasConnected) {
      setState('ended');
    }
  }, [wasConnected]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let w = (canvas.width = window.innerWidth);
    let h = (canvas.height = window.innerHeight);
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // streams & bokeh definitions
    let streams: Stream[] = [];
    const buildStreams = () => {
      streams = [];
      const COUNT = 30;
      for (let i = 0; i < COUNT; i++) {
        const startY = -0.1 + Math.random() * 0.5;
        const hue = Math.random() * 360;
        const sx = -0.15 + Math.random() * 0.3;
        const sy = startY;
        const ex = 0.75 + Math.random() * 0.5;
        const ey = startY + 0.35 + Math.random() * 0.5;
        const c1x = sx + 0.3 + Math.random() * 0.2;
        const c1y = sy + (Math.random() - 0.3) * 0.25;
        const c2x = ex - 0.3 - Math.random() * 0.2;
        const c2y = ey + (Math.random() - 0.5) * 0.2;

        const particles: Particle[] = [];
        const pcount = 16 + Math.floor(Math.random() * 8);
        for (let p = 0; p < pcount; p++) {
          particles.push({
            t: p / pcount + Math.random() * 0.03,
            jitter: (Math.random() - 0.5) * 0.02,
            size: Math.random() < 0.15 ? 1.6 + Math.random() * 1.8 : 0.5 + Math.random() * 1,
            phase: Math.random() * Math.PI * 2,
            twinkleSpeed: 0.6 + Math.random() * 1.8,
          });
        }
        streams.push({
          sx,
          sy,
          c1x,
          c1y,
          c2x,
          c2y,
          ex,
          ey,
          hue,
          particles,
          width: 0.5 + Math.random() * 1,
        });
      }
    };

    let bokeh: BokehCircle[] = [];
    const buildBokeh = () => {
      bokeh = [];
      const COUNT = 22;
      for (let i = 0; i < COUNT; i++) {
        bokeh.push({
          x: Math.random(),
          y: Math.random() * 0.85,
          r: 20 + Math.random() * 70,
          hue: Math.random() * 360,
          phase: Math.random() * Math.PI * 2,
          speed: 0.2 + Math.random() * 0.4,
        });
      }
    };

    const resize = () => {
      if (!canvas) return;
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      buildStreams();
      buildBokeh();
    };

    window.addEventListener('resize', resize);
    resize();

    let flowT = 0;
    let lastTime = 0;
    let animationId: number;

    function bezierPoint(t: number, p0: number, c1: number, c2: number, p1: number) {
      const mt = 1 - t;
      return mt * mt * mt * p0 + 3 * mt * mt * t * c1 + 3 * mt * t * t * c2 + t * t * t * p1;
    }

    function draw(t: number) {
      if (!ctx) return;
      const dt = lastTime ? t - lastTime : 16;
      lastTime = t;
      const stateVal = stateRef.current;
      const mod = STATE_MOD[stateVal] || STATE_MOD.ready;
      if (!reduceMotion) flowT += dt * 0.00035 * mod.speed;
      const time = t * 0.001;

      ctx.fillStyle = 'rgba(2,2,4,1)';
      ctx.fillRect(0, 0, w, h);

      // soft bokeh, drawn first (behind streams)
      ctx.globalCompositeOperation = 'lighter';
      bokeh.forEach((b) => {
        const pulse = reduceMotion
          ? 0.5
          : 0.35 + ((Math.sin(time * b.speed + b.phase) + 1) / 2) * 0.4;
        const bx = b.x * w,
          by = b.y * h;

        // wide soft outer halo
        const outer = ctx.createRadialGradient(bx, by, 0, bx, by, b.r * 1.8);
        outer.addColorStop(0, `hsla(${b.hue},90%,68%,${pulse * 0.22 * mod.glow})`);
        outer.addColorStop(1, `hsla(${b.hue},90%,68%,0)`);
        ctx.fillStyle = outer;
        ctx.beginPath();
        ctx.arc(bx, by, b.r * 1.8, 0, Math.PI * 2);
        ctx.fill();

        // tighter bright core
        const core = ctx.createRadialGradient(bx, by, 0, bx, by, b.r * 0.6);
        core.addColorStop(0, `hsla(${b.hue},95%,78%,${pulse * 0.4 * mod.glow})`);
        core.addColorStop(1, `hsla(${b.hue},95%,78%,0)`);
        ctx.fillStyle = core;
        ctx.beginPath();
        ctx.arc(bx, by, b.r * 0.6, 0, Math.PI * 2);
        ctx.fill();
      });

      // flowing streams
      streams.forEach((s) => {
        const sx = s.sx * w,
          sy = s.sy * h,
          c1x = s.c1x * w,
          c1y = s.c1y * h,
          c2x = s.c2x * w,
          c2y = s.c2y * h,
          ex = s.ex * w,
          ey = s.ey * h;

        // glowing guide line
        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.bezierCurveTo(c1x, c1y, c2x, c2y, ex, ey);
        ctx.strokeStyle = `hsla(${s.hue},85%,68%,${0.16 * mod.glow})`;
        ctx.lineWidth = s.width * 4;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.bezierCurveTo(c1x, c1y, c2x, c2y, ex, ey);
        ctx.strokeStyle = `hsla(${s.hue},95%,78%,${0.22 * mod.glow})`;
        ctx.lineWidth = s.width;
        ctx.stroke();

        // particles
        s.particles.forEach((p) => {
          const tt = (((p.t + flowT) % 1) + 1) % 1;
          const px = bezierPoint(tt, sx, c1x, c2x, ex) + p.jitter * w;
          const py = bezierPoint(tt, sy, c1y, c2y, ey) + p.jitter * h * 0.6;
          const tw = reduceMotion
            ? 0.7
            : 0.4 + ((Math.sin(time * p.twinkleSpeed + p.phase) + 1) / 2) * 0.6;
          const fadeEdge = Math.sin(tt * Math.PI);
          const alpha = tw * fadeEdge * mod.glow;

          ctx.beginPath();
          ctx.arc(px, py, p.size * 5.5, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${s.hue},90%,72%,${alpha * 0.22})`;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(px, py, p.size, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${s.hue},95%,80%,${alpha})`;
          ctx.fill();

          if (p.size > 1.6) {
            ctx.beginPath();
            ctx.arc(px, py, p.size * 8, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${s.hue},90%,75%,${alpha * 0.14})`;
            ctx.fill();
          }
        });
      });
      ctx.globalCompositeOperation = 'source-over';

      if (!reduceMotion) {
        animationId = requestAnimationFrame(draw);
      }
    }

    if (!reduceMotion) {
      animationId = requestAnimationFrame(draw);
    } else {
      draw(0);
    }

    return () => {
      window.removeEventListener('resize', resize);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, []);

  const handleStart = async () => {
    setMicBlocked(false);
    setState('connecting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
    } catch (err: any) {
      setState('ready');
      setMicBlocked(true);
      console.error('Mic permission error:', err.name, err.message);
      return;
    }

    if (onStartCall) {
      onStartCall();
    }
  };

  return (
    <div
      ref={ref}
      className="sydney-welcome"
      style={{ '--state-color': `var(--c-${state})` } as React.CSSProperties}
    >
      <style dangerouslySetInnerHTML={{ __html: SYDNEY_STYLES }} />
      <canvas id="field" ref={canvasRef}></canvas>
      <div className="vignette"></div>

      <nav>
        <div className="brand">
          <span className="mark"></span> Murf AI
        </div>
        <div className="navlinks">
          <a href="#">Concepts</a>
          <a href="#">How it works</a>
          <a href="#">Practice</a>
        </div>
        <div className="navright">
          <span className="text-foreground/80 font-mono text-xs font-bold tracking-wider uppercase">
            Built with{' '}
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://docs.livekit.io/agents"
              className="font-bold underline underline-offset-4"
            >
              LiveKit Agents
            </a>
          </span>
        </div>
      </nav>

      <main>
        <h1>
          ML tabhi seekhi jaati hai, jab wo <em>samjhaayi</em> jaaye.
        </h1>
        <p className="sub">
          Sydney: your Hinglish AI/ML mentor. RAG, backprop, embeddings, agent loops, sab kuch
          baat-cheet karke samjho, ek concept ek waqt mein.
        </p>

        <div className="greet">
          <div className="hi">Hey Suyash.</div>
          <div className="status-line">
            <span
              className={`status-dot ${STATUS_COPY[state].dotPulse ? 'pulse' : ''}`}
              id="statusDot"
            ></span>
            <span id="statusText">{STATUS_COPY[state].status}</span>
          </div>
        </div>

        <div
          className={`orb-wrap ${state === 'connecting' ? 'active-connecting' : ''}`}
          id="orbWrap"
        >
          <div className="ring"></div>
          <div className="ring"></div>
          <div className="ring"></div>
          <div className={`mic state-${state}`} id="micBtn" onClick={handleStart}>
            <div className="spinner"></div>
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
              <rect x="9" y="2" width="6" height="12" rx="3"></rect>
              <path d="M5 10a7 7 0 0 0 14 0"></path>
              <line x1="12" y1="17" x2="12" y2="22"></line>
              <line x1="8" y1="22" x2="16" y2="22"></line>
            </svg>
            <div className="bars">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        {state !== 'connecting' && (
          <button className="primary-btn" id="actionBtn" onClick={handleStart}>
            {state === 'ended' ? 'Start again' : 'Start conversation'}
          </button>
        )}

        <div className="langs">
          <span>English</span>
          <span>हिन्दी</span>
          <span>Hinglish</span>
        </div>

        <div className="bubble" id="bubble">
          <div className="tag">SYDNEY</div>
          <div className="line" id="bubbleLine">
            "Hi! Main Sydney hoon. Kaunsa topic explore karna chahoge: RAG, backprop, ya kuch aur?"
          </div>
        </div>

        <div className="mode" id="modeTag">
          Concept Mode · Beginner-friendly
        </div>

        <div className={`mic-error ${micBlocked ? 'visible' : ''}`} id="micError">
          <strong>Microphone access blocked</strong>
          <span>
            Sydney needs mic access to hear you. Click the lock/site-info icon next to the address
            bar, set Microphone to "Allow," then reload this page and tap the mic again.
          </span>
        </div>

        <div className="transcript" id="transcript"></div>
      </main>

      <footer className="hint">Tap the mic to start · works best with headphones</footer>
    </div>
  );
};
