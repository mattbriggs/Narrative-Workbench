//! Append-only commit/branch repository port (SRS §3.9).
//!
//! The application layer performs the atomic commit here after the engine
//! validates and the human accepts (SRS REQ-076/077). This in-memory adapter
//! sits behind a port; a SQLite/object-store adapter replaces it without
//! changing callers (SRS REQ-171). Commits are never rewritten; rewind moves a
//! pointer and deletes nothing (SRS REQ-096).

use std::collections::HashMap;

/// A commit error surfaced to the UI as a visible reason.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RepoError {
    /// The branch head moved since the caller accepted (SRS REQ-078).
    ParentChanged { expected: Option<String>, actual: Option<String> },
    /// The branch or commit is unknown.
    Unknown(String),
}

/// An immutable commit record.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Commit {
    pub id: String,
    pub parent_id: Option<String>,
    pub branch_id: String,
    pub message: String,
}

/// In-memory append-only repository.
#[derive(Default)]
pub struct Repository {
    commits: HashMap<String, Commit>,
    heads: HashMap<String, Option<String>>,
    seq: usize,
}

impl Repository {
    /// Create an empty repository.
    pub fn new() -> Self {
        Repository::default()
    }

    /// Create the root commit of a branch.
    pub fn create_root(&mut self, branch_id: &str, message: &str) -> Result<Commit, RepoError> {
        if self.heads.contains_key(branch_id) {
            return Err(RepoError::Unknown(format!("branch {branch_id} exists")));
        }
        let commit = self.new_commit(branch_id, None, message);
        self.heads.insert(branch_id.to_string(), Some(commit.id.clone()));
        Ok(commit)
    }

    /// Commit a validated delta, refusing a stale parent (SRS REQ-078).
    pub fn commit(
        &mut self,
        branch_id: &str,
        expected_parent: Option<&str>,
        message: &str,
    ) -> Result<Commit, RepoError> {
        let head = self
            .heads
            .get(branch_id)
            .ok_or_else(|| RepoError::Unknown(format!("branch {branch_id}")))?
            .clone();
        let expected = expected_parent.map(|s| s.to_string());
        if head != expected {
            return Err(RepoError::ParentChanged { expected, actual: head });
        }
        let commit = self.new_commit(branch_id, head, message);
        self.heads.insert(branch_id.to_string(), Some(commit.id.clone()));
        Ok(commit)
    }

    /// Return the head commit id of a branch.
    pub fn head(&self, branch_id: &str) -> Option<String> {
        self.heads.get(branch_id).cloned().flatten()
    }

    /// Move a branch pointer to an earlier commit without deleting history.
    pub fn rewind(&mut self, branch_id: &str, to_commit: &str) -> Result<(), RepoError> {
        if !self.commits.contains_key(to_commit) {
            return Err(RepoError::Unknown(format!("commit {to_commit}")));
        }
        self.heads.insert(branch_id.to_string(), Some(to_commit.to_string()));
        Ok(())
    }

    /// Return whether a commit still exists (rewind must not delete it).
    pub fn has_commit(&self, id: &str) -> bool {
        self.commits.contains_key(id)
    }

    fn new_commit(&mut self, branch_id: &str, parent: Option<String>, message: &str) -> Commit {
        self.seq += 1;
        let commit = Commit {
            id: format!("c{:04}", self.seq),
            parent_id: parent,
            branch_id: branch_id.to_string(),
            message: message.to_string(),
        };
        self.commits.insert(commit.id.clone(), commit.clone());
        commit
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn append_only_and_parent_guard() {
        let mut r = Repository::new();
        let root = r.create_root("main", "root").unwrap();
        let c1 = r.commit("main", Some(&root.id), "one").unwrap();
        assert_eq!(r.head("main"), Some(c1.id.clone()));
        // Committing again against the old parent is refused.
        assert_eq!(
            r.commit("main", Some(&root.id), "stale"),
            Err(RepoError::ParentChanged { expected: Some(root.id.clone()), actual: Some(c1.id.clone()) })
        );
    }

    #[test]
    fn rewind_preserves_history() {
        let mut r = Repository::new();
        let root = r.create_root("main", "root").unwrap();
        let c1 = r.commit("main", Some(&root.id), "one").unwrap();
        r.rewind("main", &root.id).unwrap();
        assert_eq!(r.head("main"), Some(root.id));
        assert!(r.has_commit(&c1.id)); // not deleted
    }

    #[test]
    fn rewind_unknown_commit_errors() {
        let mut r = Repository::new();
        r.create_root("main", "root").unwrap();
        assert!(matches!(r.rewind("main", "nope"), Err(RepoError::Unknown(_))));
    }

    #[test]
    fn commit_unknown_branch_errors() {
        let mut r = Repository::new();
        assert!(matches!(r.commit("nobranch", None, "x"), Err(RepoError::Unknown(_))));
    }

    #[test]
    fn duplicate_root_errors() {
        let mut r = Repository::new();
        r.create_root("main", "root").unwrap();
        assert!(matches!(r.create_root("main", "again"), Err(RepoError::Unknown(_))));
    }
}
