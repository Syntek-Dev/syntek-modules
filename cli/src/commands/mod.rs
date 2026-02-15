//! CLI commands

pub mod init;
pub mod install;
pub mod verify;

pub use init::{execute as init, InitArgs};
pub use install::{execute as install, InstallArgs};
pub use verify::{execute as verify, VerifyArgs};
