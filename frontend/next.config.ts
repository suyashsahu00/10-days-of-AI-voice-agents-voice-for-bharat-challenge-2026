import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  eslint: {
    // These warnings come from upstream LiveKit/AI UI components, not our code.
    ignoreDuringBuilds: true,
  },
  transpilePackages: ['@livekit/components-react', '@livekit/components-core'],
};

export default nextConfig;
