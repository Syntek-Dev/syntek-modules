/**
 * graphql-codegen configuration — @syntek/graphql (US004).
 *
 * Reads the backend GraphQL schema and generates typed TypeScript + React Query
 * hooks from every .graphql file under src/operations/.
 *
 * Run:      pnpm --filter @syntek/graphql codegen
 * CI check: pnpm --filter @syntek/graphql codegen:check  (fails if output differs)
 *
 * IMPORTANT: The schema URL below targets the local Django dev server.
 * In CI, override via the GRAPHQL_SCHEMA_URL environment variable.
 */
import type { CodegenConfig } from '@graphql-codegen/cli'

// Use the local SDL file by default so codegen works without a running server.
// Override with a live introspection URL in CI or when iterating against the backend.
const schema = process.env['GRAPHQL_SCHEMA_URL'] || './schema.graphql'

const config: CodegenConfig = {
  schema,
  documents: ['src/operations/**/*.graphql'],
  generates: {
    'src/generated/graphql.ts': {
      plugins: ['typescript', 'typescript-operations', 'typescript-react-query'],
      config: {
        reactQueryVersion: 5,
        addInfiniteQuery: false,
        exposeFetcher: true,
        exposeQueryKeys: true,
        fetcher: '../lib/fetcher#fetcher',
      },
    },
  },
  hooks: {
    afterAllFileWrite: ['prettier --write'],
  },
}

export default config
