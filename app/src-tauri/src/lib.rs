//! Narrative Workbench application layer.
//!
//! This crate is the application layer of the layered architecture (SRS §7.1):
//! it coordinates commands, checks authority, drives the proposal lifecycle,
//! and performs the atomic commit to the repository. It depends only on the
//! engine contract (mirrored here with `serde`, SRS REQ-161) and is free of any
//! GUI dependency so it builds and is covered headlessly. The Tauri binary
//! links these modules on the desktop target.
//!
//! Modules:
//! - [`contract`] — serde mirror of the engine's Pydantic contract.
//! - [`authority`] — role × action authority decisions (SRS §2.3).
//! - [`proposal`] — the proposal lifecycle state machine (SRS §3.8).
//! - [`repository`] — append-only commit/branch port (SRS §3.9).
//! - [`provenance`] — provenance record construction (SRS REQ-097).
//! - [`engine_client`] — request/response envelope over the JSON contract.
//! - [`commands`] — intention-revealing commands with idempotency keys.

pub mod authority;
pub mod commands;
pub mod contract;
pub mod engine_client;
pub mod proposal;
pub mod provenance;
pub mod repository;
