//! syntek-graphql-crypto — GraphQL middleware preventing plaintext resolver output
//!
//! Intercepts Strawberry GraphQL resolver output and ensures no sensitive field
//! is returned as plaintext. All encrypted values pass through syntek-crypto
//! before being serialised into the GraphQL response.

// Implementation stubs — filled in during us001/syntek-crypto sprint.
