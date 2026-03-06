Feature: Shared TypeScript Types Package
  As a frontend developer
  I want a shared TypeScript types package
  So that all web and mobile packages use consistent type definitions without duplication

  Scenario: Types import and resolve without errors
    Given the @syntek/types package is installed in a workspace package
    When I import ID, User, Tenant, and Notification types
    Then TypeScript compiles without errors
    And all type assertions pass

  Scenario: Breaking type change causes compilation failure
    Given User has a required id field of type ID
    When I attempt to assign an empty object to User
    Then TypeScript reports a type error
    And the @ts-expect-error directive is satisfied

  Scenario: Build produces declaration files for all modules
    Given the source files are compiled with tsc
    When I check the dist output directory
    Then index.d.ts is present
    And base.d.ts is present
    And auth.d.ts is present
    And tenant.d.ts is present
    And notifications.d.ts is present
