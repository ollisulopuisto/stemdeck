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

pub fn write_atomic(path: &Path, contents: impl AsRef<[u8]>) -> std::io::Result<()> {
    let name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("file");
    let temp = path.with_file_name(format!(".{name}.{}.tmp", std::process::id()));
    let result = (|| {
        let mut file = fs::File::create(&temp)?;
        file.write_all(contents.as_ref())?;
        file.sync_all()?;
        drop(file);
        fs::rename(&temp, path)
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temp);
    }
    result
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
}
