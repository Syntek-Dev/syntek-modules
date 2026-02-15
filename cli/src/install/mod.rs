//! Installation modules for Syntek packages

pub mod auth;
pub mod backend;
pub mod frontend;
pub mod graphql;
pub mod rust;

pub use auth::{AuthInstallOptions, AuthInstaller};
pub use backend::BackendInstaller;
pub use frontend::FrontendInstaller;
pub use graphql::GraphQLInstaller;
pub use rust::RustInstaller;
