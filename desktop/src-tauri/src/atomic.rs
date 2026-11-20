//! Replace a file without ever leaving a torn one behind.
//!
//! `fs::write` truncates the file and then writes it, so a crash, a full disk
//! or a power cut in between leaves an empty or half-written file where the
//! old one was. For the small state files the desktop shell keeps (the LAN
//! certificate and key, the version stamp, the runtime manifest, the update
//! checksum) that means a broken launch. This writes a temp file beside the
//! target, flushes it to disk, then renames it over the target, so a reader
//! sees the old file or the new one and never a mix.

use std::fs;
use std::io::Write;
use std::path::Path;

/// Replace `path` with `contents`. The file gets the default permissions.
pub fn write_atomic(path: &Path, contents: impl AsRef<[u8]>) -> std::io::Result<()> {
    write_inner(path, contents.as_ref(), false)
}

/// Same, for secrets: the temp file is created owner-only (0600 on Unix) from the first
/// byte, so there is no window in which another user could read it, and the renamed
/// file keeps those permissions.
pub fn write_atomic_private(path: &Path, contents: impl AsRef<[u8]>) -> std::io::Result<()> {
    write_inner(path, contents.as_ref(), true)
}

fn create_temp(temp: &Path, private: bool) -> std::io::Result<fs::File> {
    let mut options = fs::OpenOptions::new();
    options.write(true).create_new(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        if private {
            options.mode(0o600);
        }
    }
    #[cfg(not(unix))]
    let _ = private;
    options.open(temp)
}

/// Flush the rename itself. Without this the new directory entry can be lost on power
/// loss even though the file contents were synced. Best effort: Windows cannot open a
/// directory for syncing, and the file is already replaced either way.
fn sync_directory(dir: &Path) {
    #[cfg(unix)]
    {
        if let Ok(handle) = fs::File::open(dir) {
            let _ = handle.sync_all();
        }
    }
    #[cfg(not(unix))]
    let _ = dir;
}

fn write_inner(path: &Path, contents: &[u8], private: bool) -> std::io::Result<()> {
    let name = path.file_name().and_then(|n| n.to_str()).unwrap_or("file");
    let temp = path.with_file_name(format!(".{name}.{}.tmp", std::process::id()));
    // A leftover temp from a crashed earlier run would make create_new fail.
    let _ = fs::remove_file(&temp);
    let result = (|| {
        let mut file = create_temp(&temp, private)?;
        file.write_all(contents)?;
        file.sync_all()?;
        drop(file);
        fs::rename(&temp, path)
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temp);
        return result;
    }
    if let Some(dir) = path.parent() {
        sync_directory(dir);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_writes_a_new_file() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("state.json");
        write_atomic(&path, "{\"a\":1}").unwrap();
        assert_eq!(fs::read_to_string(&path).unwrap(), "{\"a\":1}");
    }

    #[test]
    fn it_replaces_an_existing_file_and_leaves_no_temp_file() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("state.json");
        fs::write(&path, "old").unwrap();
        write_atomic(&path, "new").unwrap();
        assert_eq!(fs::read_to_string(&path).unwrap(), "new");
        let names: Vec<_> = fs::read_dir(dir.path())
            .unwrap()
            .map(|e| e.unwrap().file_name())
            .collect();
        assert_eq!(names.len(), 1, "temp file left behind: {names:?}");
    }

    #[test]
    fn a_failed_write_cleans_up_its_temp_file() {
        let dir = tempfile::tempdir().unwrap();
        // A non-empty directory at the target makes the final rename fail,
        // after the temp file has already been written.
        let path = dir.path().join("state.json");
        fs::create_dir(&path).unwrap();
        fs::write(path.join("keep"), "x").unwrap();
        assert!(write_atomic(&path, "new").is_err());
        assert!(path.join("keep").exists());
        let names: Vec<_> = fs::read_dir(dir.path())
            .unwrap()
            .map(|e| e.unwrap().file_name())
            .collect();
        assert_eq!(names.len(), 1, "temp file left behind: {names:?}");
    }

    #[test]
    fn it_fails_when_the_directory_is_missing() {
        let dir = tempfile::tempdir().unwrap();
        assert!(write_atomic(&dir.path().join("nope/state.json"), "x").is_err());
    }

    #[cfg(unix)]
    #[test]
    fn a_private_write_is_owner_only() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("key.pem");
        write_atomic_private(&path, "secret").unwrap();
        assert_eq!(fs::read_to_string(&path).unwrap(), "secret");
        let mode = fs::metadata(&path).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o600);
    }

    #[cfg(unix)]
    #[test]
    fn a_private_replace_never_widens_permissions() {
        use std::os::unix::fs::PermissionsExt;
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("key.pem");
        write_atomic_private(&path, "one").unwrap();
        write_atomic_private(&path, "two").unwrap();
        let mode = fs::metadata(&path).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o600);
        assert_eq!(fs::read_to_string(&path).unwrap(), "two");
    }

    #[test]
    fn a_stale_temp_file_from_a_crashed_run_does_not_block_the_write() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("state.json");
        let stale = dir.path().join(format!(".state.json.{}.tmp", std::process::id()));
        fs::write(&stale, "junk").unwrap();
        write_atomic(&path, "fresh").unwrap();
        assert_eq!(fs::read_to_string(&path).unwrap(), "fresh");
        assert!(!stale.exists());
    }
}
