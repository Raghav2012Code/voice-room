#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;
use std::fs::File;
use std::net::{TcpStream, ToSocketAddrs};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use serde::Deserialize;
use tauri::menu::{CheckMenuItemBuilder, MenuBuilder, MenuItemBuilder};
use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};
use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

const DEFAULT_PORT: u16 = 8766;
const STARTUP_TIMEOUT: Duration = Duration::from_secs(20);
const POLL_INTERVAL: Duration = Duration::from_millis(250);
const RUN_KEY: &str = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run";
const RUN_VALUE: &str = "Voice Room";
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

#[derive(Clone, Debug, Deserialize)]
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
            command: vec![
                "python".to_string(),
                "-m".to_string(),
                "server.server".to_string(),
            ],
            cwd: None,
            port: DEFAULT_PORT,
            log: None,
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(default)]
struct DesktopConfig {
    tray: bool,
}

impl Default for DesktopConfig {
    fn default() -> Self {
        Self { tray: true }
    }
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
struct Config {
    server: ServerConfig,
    desktop: DesktopConfig,
}

struct ShellState {
    server: Mutex<Option<Child>>,
    tray: AtomicBool,
    closing: AtomicBool,
}

impl ShellState {
    fn new(tray: bool) -> Self {
        Self {
            server: Mutex::new(None),
            tray: AtomicBool::new(tray),
            closing: AtomicBool::new(false),
        }
    }
}

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
        .and_then(|socket| TcpStream::connect_timeout(&socket, Duration::from_millis(250)).ok())
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

fn wait_for_port(addr: &str) -> bool {
    let deadline = Instant::now() + STARTUP_TIMEOUT;
    while Instant::now() < deadline {
        if port_open(addr) {
            return true;
        }
        std::thread::sleep(POLL_INTERVAL);
    }
    false
}

fn stop_server(app: &AppHandle) {
    if let Some(state) = app.try_state::<ShellState>() {
        state.closing.store(true, Ordering::Relaxed);
        if let Ok(mut guard) = state.server.lock() {
            if let Some(mut child) = guard.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

fn show_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        if let Err(error) = window.unminimize() {
            eprintln!("cannot unminimize the window: {}", error);
        }
        if let Err(error) = window.show() {
            eprintln!("cannot show the window: {}", error);
        }
        if let Err(error) = window.set_focus() {
            eprintln!("cannot focus the window: {}", error);
        }
    }
}

fn show_error(window: &WebviewWindow, message: &str) {
    let quoted = match serde_json::to_string(message) {
        Ok(value) => value,
        Err(error) => {
            eprintln!("cannot encode the startup error: {}", error);
            "\"The local engine did not start.\"".to_string()
        }
    };
    // The page can still be loading when the backend fails, so retry until showError exists.
    let script = format!(
        "(function () {{\n\
           var message = {};\n\
           var attempts = 0;\n\
           function show() {{\n\
             if (typeof showError === 'function') {{ showError(message); return; }}\n\
             if (attempts++ < 50) {{ setTimeout(show, 100); }}\n\
           }}\n\
           show();\n\
         }})();",
        quoted
    );
    if let Err(error) = window.eval(script) {
        eprintln!("cannot show the startup error: {}", error);
    }
}

fn navigate(app: &AppHandle, window: &WebviewWindow, addr: &str) {
    let target = format!("http://{}/", addr);
    let url = match tauri::Url::parse(&target) {
        Ok(url) => url,
        Err(error) => {
            show_error(
                window,
                &format!("Invalid server address {}: {}", target, error),
            );
            return;
        }
    };
    let window = window.clone();
    let label = target.clone();
    if let Err(error) = app.run_on_main_thread(move || {
        if let Err(error) = window.navigate(url) {
            eprintln!("cannot open {}: {}", label, error);
        }
    }) {
        eprintln!("cannot navigate the window to {}: {}", target, error);
    }
}

fn spawn_server(app: &AppHandle, window: &WebviewWindow, server: ServerConfig) {
    let app = app.clone();
    let window = window.clone();
    let result = std::thread::Builder::new()
        .name("voice-room-server".into())
        .spawn(move || {
            let addr = server_addr(server.port);
            let child = match start_server(&server, &addr) {
                Ok(child) => child,
                Err(message) => {
                    show_error(&window, &message);
                    return;
                }
            };
            let closing = match app.try_state::<ShellState>() {
                Some(state) => {
                    match state.server.lock() {
                        Ok(mut guard) => *guard = child,
                        Err(_) => eprintln!("the server process lock is poisoned"),
                    }
                    state.closing.load(Ordering::Relaxed)
                }
                None => false,
            };
            if closing {
                stop_server(&app);
                return;
            }
            if wait_for_port(&addr) {
                navigate(&app, &window, &addr);
            } else {
                show_error(
                    &window,
                    &format!(
                        "The local engine did not answer on {} within {} seconds.",
                        addr,
                        STARTUP_TIMEOUT.as_secs()
                    ),
                );
            }
        });
    if let Err(error) = result {
        eprintln!("cannot start the server thread: {}", error);
    }
}

#[cfg(windows)]
fn reg_command() -> Command {
    use std::os::windows::process::CommandExt;
    let mut command = Command::new("reg");
    command.creation_flags(CREATE_NO_WINDOW);
    command
}

#[cfg(windows)]
fn autostart_enabled() -> bool {
    reg_command()
        .args(["query", RUN_KEY, "/v", RUN_VALUE])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|status| status.success())
        .unwrap_or(false)
}

#[cfg(windows)]
fn set_autostart(enabled: bool) -> Result<(), String> {
    let mut command = reg_command();
    if enabled {
        let exe =
            env::current_exe().map_err(|e| format!("cannot find the application path: {}", e))?;
        let value = format!("\"{}\" --minimized", exe.display());
        command.args([
            "add", RUN_KEY, "/v", RUN_VALUE, "/t", "REG_SZ", "/d", &value, "/f",
        ]);
    } else {
        command.args(["delete", RUN_KEY, "/v", RUN_VALUE, "/f"]);
    }
    let status = command
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map_err(|e| format!("cannot run reg.exe: {}", e))?;
    if status.success() {
        Ok(())
    } else {
        Err(format!("reg.exe exited with {}", status))
    }
}

#[cfg(not(windows))]
fn autostart_enabled() -> bool {
    false
}

#[cfg(not(windows))]
fn set_autostart(_enabled: bool) -> Result<(), String> {
    Err("Start with Windows is only available on Windows.".to_string())
}

fn create_tray(app: &AppHandle) -> tauri::Result<()> {
    let Some(icon) = app.default_window_icon().cloned() else {
        return Err(tauri::Error::AssetNotFound("window icon".to_string()));
    };

    let open_item = MenuItemBuilder::with_id("open", "Open Voice Room").build(app)?;
    let start_item = CheckMenuItemBuilder::with_id("autostart", "Start with Windows")
        .checked(autostart_enabled())
        .build(app)?;
    let quit_item = MenuItemBuilder::with_id("quit", "Quit").build(app)?;
    let menu = MenuBuilder::new(app)
        .item(&open_item)
        .item(&start_item)
        .separator()
        .item(&quit_item)
        .build()?;

    let start_item_for_menu = start_item.clone();
    TrayIconBuilder::new()
        .tooltip("Voice Room")
        .icon(icon)
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(move |app, event| match event.id().as_ref() {
            "open" => show_main_window(app),
            "autostart" => {
                let enabled = !autostart_enabled();
                match set_autostart(enabled) {
                    Ok(()) => {
                        if let Err(error) = start_item_for_menu.set_checked(enabled) {
                            eprintln!("cannot update the Start with Windows item: {}", error);
                        }
                    }
                    Err(error) => eprintln!("cannot update Start with Windows: {}", error),
                }
            }
            "quit" => {
                stop_server(app);
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                show_main_window(tray.app_handle());
            }
        })
        .build(app)?;

    Ok(())
}

fn main() {
    let minimized = env::args().any(|arg| arg == "--minimized");

    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            show_main_window(app);
        }))
        .plugin(
            tauri_plugin_window_state::Builder::default()
                // Visibility is excluded so --minimized and close to tray survive a restore.
                .with_state_flags(
                    tauri_plugin_window_state::StateFlags::all()
                        & !tauri_plugin_window_state::StateFlags::VISIBLE,
                )
                .build(),
        )
        .setup(move |app| {
            let config = load_config()?;
            let tray_enabled = config.desktop.tray;
            app.manage(ShellState::new(tray_enabled));

            let first_run = app
                .path()
                .app_config_dir()
                .map(|dir| {
                    !dir.join(tauri_plugin_window_state::DEFAULT_FILENAME)
                        .is_file()
                })
                .unwrap_or(true);
            let mut window_builder =
                WebviewWindowBuilder::new(app, "main", WebviewUrl::App("index.html".into()))
                    .title("Voice Room")
                    .inner_size(1240.0, 840.0)
                    .visible(!minimized);
            if first_run {
                window_builder = window_builder.center();
            }
            let window = window_builder.build()?;

            if tray_enabled {
                if let Err(error) = create_tray(app.handle()) {
                    eprintln!("cannot create the tray icon: {}", error);
                    if let Some(state) = app.try_state::<ShellState>() {
                        state.tray.store(false, Ordering::Relaxed);
                    }
                    if let Err(error) = window.show() {
                        eprintln!("cannot show the window: {}", error);
                    }
                }
            }

            spawn_server(app.handle(), &window, config.server.clone());
            Ok(())
        })
        .on_window_event(|window, event| match event {
            tauri::WindowEvent::CloseRequested { api, .. } => {
                let tray = window
                    .app_handle()
                    .try_state::<ShellState>()
                    .map(|state| state.tray.load(Ordering::Relaxed))
                    .unwrap_or(false);
                if tray {
                    api.prevent_close();
                    if let Err(error) = window.hide() {
                        eprintln!("cannot hide the window: {}", error);
                    }
                }
            }
            tauri::WindowEvent::Destroyed => stop_server(window.app_handle()),
            _ => {}
        });

    if let Err(error) = app.run(tauri::generate_context!()) {
        eprintln!("error while running Voice Room: {}", error);
        std::process::exit(1);
    }
}
