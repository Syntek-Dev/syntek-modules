import { defineConfig } from 'tsup'

export default defineConfig({
  // Entry points
  entry: ['src/index.ts'],

  // Output formats
  format: ['cjs', 'esm'],

  // Generate declaration files
  dts: true,

  // Minify output
  minify: true,

  // Clean output directory before build
  clean: true,

  // Split output into chunks
  splitting: true,

  // Generate sourcemaps
  sourcemap: true,

  // Tree-shaking
  treeshake: true,

  // Target environment
  target: 'es2022',

  // External dependencies (don't bundle)
  external: [
    'react',
    'react-dom',
    'react-native',
    'next',
  ],

  // Output directory
  outDir: 'dist',

  // Enable watch mode in development
  watch: process.env.NODE_ENV === 'development',
})
