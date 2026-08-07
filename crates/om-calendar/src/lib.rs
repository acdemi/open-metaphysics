//! om-calendar -- Deterministic luni-solar calendar primitives.
//!
//! Phase 6.8: Repository Bootstrap placeholder.
//! Business logic will be implemented in Phase 7+ per Phase 6.6 architecture.
//! See: docs/engineering/14_polyglot_architecture.md (Rust Layer)

#![deny(unsafe_code)]

/// Crate version string.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(test)]
mod tests {
    #[test]
    fn version_is_set() {
        assert!(!super::VERSION.is_empty());
    }
}
