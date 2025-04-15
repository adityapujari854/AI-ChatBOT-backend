import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  reactStrictMode: true,

  webpack(config, _options) {
    // Adds support for importing from root
    config.resolve.modules.push(path.resolve('./'));
    return config;
  },

  images: {
    domains: ['your-image-cdn.com'], // Replace with your actual image domain
    deviceSizes: [320, 420, 768, 1024, 1200],
    imageSizes: [16, 32, 48, 64, 96, 128, 256],
  },

  experimental: {
    optimizeCss: true, // Enables CSS optimization
  },

  typescript: {
    ignoreBuildErrors: true, // Allows builds to continue despite TS errors (use carefully)
  },
};

export default nextConfig;
