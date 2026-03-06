import { useMutation, useQuery, UseMutationOptions, UseQueryOptions } from "@tanstack/react-query";
import { fetcher } from "../lib/fetcher";
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = {
  [_ in K]?: never;
};
export type Incremental<T> =
  | T
  | { [P in keyof T]?: P extends " $fragmentName" | "__typename" ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string };
  String: { input: string; output: string };
  Boolean: { input: boolean; output: boolean };
  Int: { input: number; output: number };
  Float: { input: number; output: number };
};

export type LoginPayload = {
  __typename?: "LoginPayload";
  token: Scalars["String"]["output"];
  user: User;
};

export type Mutation = {
  __typename?: "Mutation";
  login?: Maybe<LoginPayload>;
};

export type MutationLoginArgs = {
  email: Scalars["String"]["input"];
  password: Scalars["String"]["input"];
};

/**
 * Syntek backend GraphQL schema — SDL for local codegen.
 *
 * This file mirrors the Strawberry schema exposed by the Django backend.
 * Used as the codegen schema source when GRAPHQL_SCHEMA_URL is not set.
 * Keep in sync with the backend schema; drift will be surfaced by `pnpm codegen:check` in CI.
 */
export type Permission = {
  __typename?: "Permission";
  name: Scalars["String"]["output"];
  scope: Scalars["String"]["output"];
};

export type Query = {
  __typename?: "Query";
  currentTenant?: Maybe<Tenant>;
  me?: Maybe<User>;
};

export type Role = {
  __typename?: "Role";
  id: Scalars["ID"]["output"];
  name: Scalars["String"]["output"];
  permissions: Array<Permission>;
};

export type Tenant = {
  __typename?: "Tenant";
  id: Scalars["ID"]["output"];
  name: Scalars["String"]["output"];
  slug: Scalars["String"]["output"];
};

export type User = {
  __typename?: "User";
  createdAt: Scalars["String"]["output"];
  email: Scalars["String"]["output"];
  id: Scalars["ID"]["output"];
  roles: Array<Role>;
};

export type LoginMutationVariables = Exact<{
  email: Scalars["String"]["input"];
  password: Scalars["String"]["input"];
}>;

export type LoginMutation = {
  __typename?: "Mutation";
  login?: {
    __typename?: "LoginPayload";
    token: string;
    user: {
      __typename?: "User";
      id: string;
      email: string;
      createdAt: string;
      roles: Array<{
        __typename?: "Role";
        id: string;
        name: string;
        permissions: Array<{ __typename?: "Permission"; name: string; scope: string }>;
      }>;
    };
  } | null;
};

export type CurrentUserQueryVariables = Exact<{ [key: string]: never }>;

export type CurrentUserQuery = {
  __typename?: "Query";
  me?: {
    __typename?: "User";
    id: string;
    email: string;
    createdAt: string;
    roles: Array<{
      __typename?: "Role";
      id: string;
      name: string;
      permissions: Array<{ __typename?: "Permission"; name: string; scope: string }>;
    }>;
  } | null;
};

export type CurrentTenantQueryVariables = Exact<{ [key: string]: never }>;

export type CurrentTenantQuery = {
  __typename?: "Query";
  currentTenant?: { __typename?: "Tenant"; id: string; slug: string; name: string } | null;
};

export const LoginDocument = `
    mutation Login($email: String!, $password: String!) {
  login(email: $email, password: $password) {
    token
    user {
      id
      email
      createdAt
      roles {
        id
        name
        permissions {
          name
          scope
        }
      }
    }
  }
}
    `;

export const useLoginMutation = <TError = unknown, TContext = unknown>(
  options?: UseMutationOptions<LoginMutation, TError, LoginMutationVariables, TContext>,
) => {
  return useMutation<LoginMutation, TError, LoginMutationVariables, TContext>({
    mutationKey: ["Login"],
    mutationFn: (variables?: LoginMutationVariables) =>
      fetcher<LoginMutation, LoginMutationVariables>(LoginDocument, variables)(),
    ...options,
  });
};

useLoginMutation.fetcher = (variables: LoginMutationVariables, options?: RequestInit["headers"]) =>
  fetcher<LoginMutation, LoginMutationVariables>(LoginDocument, variables, options);

export const CurrentUserDocument = `
    query CurrentUser {
  me {
    id
    email
    createdAt
    roles {
      id
      name
      permissions {
        name
        scope
      }
    }
  }
}
    `;

export const useCurrentUserQuery = <TData = CurrentUserQuery, TError = unknown>(
  variables?: CurrentUserQueryVariables,
  options?: Omit<UseQueryOptions<CurrentUserQuery, TError, TData>, "queryKey"> & {
    queryKey?: UseQueryOptions<CurrentUserQuery, TError, TData>["queryKey"];
  },
) => {
  return useQuery<CurrentUserQuery, TError, TData>({
    queryKey: variables === undefined ? ["CurrentUser"] : ["CurrentUser", variables],
    queryFn: fetcher<CurrentUserQuery, CurrentUserQueryVariables>(CurrentUserDocument, variables),
    ...options,
  });
};

useCurrentUserQuery.getKey = (variables?: CurrentUserQueryVariables) =>
  variables === undefined ? ["CurrentUser"] : ["CurrentUser", variables];

useCurrentUserQuery.fetcher = (
  variables?: CurrentUserQueryVariables,
  options?: RequestInit["headers"],
) => fetcher<CurrentUserQuery, CurrentUserQueryVariables>(CurrentUserDocument, variables, options);

export const CurrentTenantDocument = `
    query CurrentTenant {
  currentTenant {
    id
    slug
    name
  }
}
    `;

export const useCurrentTenantQuery = <TData = CurrentTenantQuery, TError = unknown>(
  variables?: CurrentTenantQueryVariables,
  options?: Omit<UseQueryOptions<CurrentTenantQuery, TError, TData>, "queryKey"> & {
    queryKey?: UseQueryOptions<CurrentTenantQuery, TError, TData>["queryKey"];
  },
) => {
  return useQuery<CurrentTenantQuery, TError, TData>({
    queryKey: variables === undefined ? ["CurrentTenant"] : ["CurrentTenant", variables],
    queryFn: fetcher<CurrentTenantQuery, CurrentTenantQueryVariables>(
      CurrentTenantDocument,
      variables,
    ),
    ...options,
  });
};

useCurrentTenantQuery.getKey = (variables?: CurrentTenantQueryVariables) =>
  variables === undefined ? ["CurrentTenant"] : ["CurrentTenant", variables];

useCurrentTenantQuery.fetcher = (
  variables?: CurrentTenantQueryVariables,
  options?: RequestInit["headers"],
) =>
  fetcher<CurrentTenantQuery, CurrentTenantQueryVariables>(
    CurrentTenantDocument,
    variables,
    options,
  );
