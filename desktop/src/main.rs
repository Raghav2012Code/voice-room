#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::fs::File;
use std::net::{TcpStream, ToSocketAddrs};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use serde::Deserialize;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

const DEFAULT_PORT: u16 = 8766;
const STARTUP_TIMEOUT: Duration = Duration::from_secs(20);
const POLL_INTERVAL: Duration = Duration::from_millis(250);

#[derive(Debug, Deserialize)]
#[serde(default)]
struct ServerConfig {
    command: Vec<String>,
    cwd: Option<String>,
    port: u16,
    log: Option<String>,
}

impl Default for ServerConfig {
    fn default() -> Self {
        Self {
            command: vec!["python".to_string(), "-m".to_string(), "server.server".to_string()],
            cwd: None,
            port: DEFAULT_PORT,
            log: None,
        }
    }
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
struct Config {
    server: ServerConfig,
}

struct ServerProcess(Mutex<Option<Child>>);

fn config_candidates() -> Vec<PathBuf> {
    let mut paths = Vec::new();
    if let Some(value) = env::var_os("VOICE_ROOM_CONFIG") {
        let path = PathBuf::from(value);
        if !path.as_os_str().is_empty() {
            paths.push(path);
        }
    }
    if let Ok(cwd) = env::current_dir() {
        paths.push(cwd.join("config.json"));
    }
    if let Ok(exe) = env::current_exe() {
        if let Some(parent) = exe.parent() {
            paths.push(parent.join("config.json"));
        }
    }
    paths
}

fn load_config() -> Result<Config, String> {
    for path in config_candidates() {
        if !path.is_file() {
            continue;
        }
        let text = std::fs::read_to_string(&path)
            .map_err(|e| format!("cannot read config {}: {}", path.display(), e))?;
        let config: Config = serde_json::from_str(&text)
            .map_err(|e| format!("invalid config {}: {}", path.display(), e))?;
        if config.server.command.is_empty() {
            return Err(format!(
                "invalid config {}: server.command must not be empty",
                path.display()
            ));
        }
        return Ok(config);
    }
    Ok(Config::default())
}

fn server_addr(port: u16) -> String {
    format!("127.0.0.1:{}", port)
}

fn port_open(addr: &str) -> bool {
    addr.to_socket_addrs()
        .ok()
        .and_then(|mut addrs| addrs.next())
        .and_then(|socket| {
            TcpStream::connect_timeout(&socket, Duration::from_millis(250)).ok()
        })
        .is_some()
}

fn start_server(config: &ServerConfig, addr: &str) -> Result<Option<Child>, String> {
    if port_open(addr) {
        return Ok(None);
    }

    let mut parts = config.command.iter();
    let program = parts
        .next()
        .ok_or_else(|| "server.command must not be empty".to_string())?;
    let args: Vec<&String> = parts.collect();

    let mut command = Command::new(program);
    command.args(args).stdin(Stdio::null());
    if let Some(dir) = config.cwd.as_deref() {
        if !dir.is_empty() {
            command.current_dir(dir);
        }
    }
    match config.log.as_deref() {
        Some(log) if !log.is_empty() => {
            let file = File::create(log)
                .map_err(|e| format!("cannot open server log '{}': {}", log, e))?;
            let out = file
                .try_clone()
                .map_err(|e| format!("cannot clone server log '{}': {}", log, e))?;
            command.stdout(Stdio::from(out)).stderr(Stdio::from(file));
        }
        _ => {
            command.stdout(Stdio::null()).stderr(Stdio::null());
        }
    }

    let child = command
        .spawn()
        .map_err(|e| format!("cannot start '{}': {}", program, e))?;
    Ok(Some(child))
}

fn wait_for_port(addr: &str) {
    let deadline = Instant::now() + STARTUP_TIMEOUT;
    while Instant::now() < deadline {
        if port_open(addr) {
            return;
        }
        std::thread::sleep(POLL_INTERVAL);
    }
    eprintln!("server at {} did not become ready within 20s", addr);
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let config = load_config()?;
            let addr = server_addr(config.server.port);
            let child = start_server(&config.server, &addr)?;
            let spawned = child.is_some();
            app.manage(ServerProcess(Mutex::new(child)));
            if spawned {
                wait_for_port(&addr);
            }
            let url = format!("http://{}/", addr)
                .parse()
                .map_err(|e| format!("invalid server URL: {}", e))?;
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url))
                .title("Voice Room")
                .inner_size(1240.0, 840.0)
                .center()
                .build()?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Some(state) = window.app_handle().try_state::<ServerProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(mut child) = guard.take() {
                            let _ = child.kill();
                            let _ = child.wait();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Voice Room");
}
