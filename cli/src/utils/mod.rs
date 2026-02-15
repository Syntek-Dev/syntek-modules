//! Utility modules for Syntek CLI

pub mod error;
pub mod exec;
pub mod fs;
pub mod path;

pub use error::{CliError, Result, Warning};
