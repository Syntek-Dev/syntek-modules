Feature: Shared GraphQL Operations Package
  As a frontend developer
  I want pre-generated, typed GraphQL operations
  So that all packages query the backend consistently with full TypeScript inference

  Scenario: Query hook imports resolve with correct types
    Given the shared/graphql package is built
    When I import useCurrentUserQuery in a web package
    Then TypeScript infers the correct response type for CurrentUserQuery
    And TypeScript infers the correct variables type for CurrentUserQueryVariables

  Scenario: Codegen generates typed hooks from .graphql files
    Given a query is defined in src/operations/auth.graphql
    When I run pnpm codegen
    Then src/generated/graphql.ts is produced
    And useLoginMutation is exported with LoginMutationVariables and LoginMutation types
    And useCurrentUserQuery is exported with CurrentUserQueryVariables and CurrentUserQuery types
    And useCurrentTenantQuery is exported with CurrentTenantQueryVariables and CurrentTenantQuery types

  Scenario: Schema drift surfaces breaking type changes
    Given the backend GraphQL schema changes a field type
    When I run pnpm codegen
    Then the generated types in src/generated/graphql.ts are updated
    And tsc --noEmit fails in any consuming package that used the old field type
    And the developer must fix the consuming code to restore green

  Scenario: CI fails when generated files are out of date
    Given codegen runs in CI via pnpm codegen:check
    When the output differs from the committed src/generated/graphql.ts
    Then the CI pipeline exits with a non-zero code
    And the developer must run pnpm codegen locally and commit the updated file
