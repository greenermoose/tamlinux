//! Explicit capture-key setup for the owned desktop. Normal annotation startup
//! never installs wrappers or rewrites compositor configuration.
use std::path::PathBuf;
use anyhow::{Context, Result, bail};

pub(crate) fn is_tamlinux() -> bool {
    std::env::var("TAMLINUX_SESSION").as_deref() == Ok("1")
}

fn lua_escape(value: &str) -> String {
    value.replace('\\', "\\\\").replace('"', "\\\"")
        .replace('\n', "\\n").replace('\r', "\\r")
}

fn contents(key: &str, executable: &str) -> String {
    let command = format!("'{}' --capture", executable.replace('\'', "'\\''"));
    format!("-- Managed by Tensaku: explicit capture-key selection.\n\
             hl.unbind(\"{}\")\n\
             hl.bind(\"{}\", hl.dsp.exec_cmd(\"{}\"), {{description = \"Tensaku capture\"}})\n",
            lua_escape(key), lua_escape(key), lua_escape(&command))
}

pub fn wire_capture_key(key: &str) -> Result<()> {
    if key.is_empty() || key.len() > 128 || key.chars().any(char::is_control) {
        bail!("Invalid capture key");
    }
    if !is_tamlinux() {
        bail!("Capture-key persistence requires an owned Tamlinux session");
    }
    let base = std::env::var_os("XDG_STATE_HOME").filter(|v| !v.is_empty())
        .map(PathBuf::from).or_else(|| std::env::var_os("HOME")
        .map(|home| PathBuf::from(home).join(".local/state")))
        .context("HOME or XDG_STATE_HOME is required")?;
    let directory = base.join("tamlinux/toggles/hypr");
    std::fs::create_dir_all(&directory)?;
    let target = directory.join("tensaku-capture.lua");
    // Existing user files and symlinks are conflicts, not writable defaults.
    let mut previous = None;
    if let Ok(metadata) = std::fs::symlink_metadata(&target) {
        if !metadata.is_file() || metadata.file_type().is_symlink()
            || !std::fs::read_to_string(&target)?.starts_with("-- Managed by Tensaku: explicit capture-key selection.\n") {
            bail!("Existing capture-key file is not managed by Tensaku");
        }
        previous = Some(std::fs::read(&target)?);
    }
    let executable = std::env::current_exe()?;
    let temporary = directory.join(format!(".tensaku-capture-{}.lua", std::process::id()));
    let mut file = std::fs::OpenOptions::new().write(true).create_new(true).open(&temporary)?;
    use std::io::Write;
    file.write_all(contents(key, &executable.to_string_lossy()).as_bytes())?;
    file.sync_all()?;
    if let Some(bytes) = previous {
        let backup = directory.join(format!("tensaku-capture.lua.bak.{}", std::process::id()));
        let mut saved = std::fs::OpenOptions::new().write(true).create_new(true).open(&backup)?;
        saved.write_all(&bytes)?;
        saved.sync_all()?;
    }
    std::fs::rename(&temporary, &target)?;
    println!("Saved {}. Reload Hyprland to apply the capture key.", target.display());
    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn capture_dropin_quotes_both_lua_and_shell() {
        let lua = super::contents("SUPER + S", "/path with spaces/tensaku");
        assert!(lua.contains("hl.unbind(\"SUPER + S\")"));
        assert!(lua.contains("hl.dsp.exec_cmd(\"'/path with spaces/tensaku' --capture\")"));
        assert!(!lua.contains("o.bind"));
        assert!(!lua.contains("default.hypr"));
    }
}
