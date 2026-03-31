use tauri::{State, Manager};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tauri::api::dialog;
use tauri::api::clipboard;

use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemInfo {
    pub os: String,
    pub version: String,
    pub arch: String,
    pub hostname: String,
}

#[tauri::command]
pub async fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to AgentForge.", name)
}

#[tauri::command]
pub async fn check_backend_connection(
    state: State<'_, AppState>,
) -> Result<bool, String> {
    let client = reqwest::Client::new();
    
    match client
        .get(format!("{}/health", state.backend_url))
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await
    {
        Ok(response) => {
            let connected = response.status().is_success();
            let mut is_connected = state.is_connected.lock().await;
            *is_connected = connected;
            Ok(connected)
        }
        Err(e) => {
            let mut is_connected = state.is_connected.lock().await;
            *is_connected = false;
            Err(format!("Connection failed: {}", e))
        }
    }
}

#[tauri::command]
pub async fn get_system_info() -> SystemInfo {
    SystemInfo {
        os: std::env::consts::OS.to_string(),
        version: sys_info::os_version().unwrap_or_else(|_| "Unknown".to_string()),
        arch: std::env::consts::ARCH.to_string(),
        hostname: sys_info::hostname().unwrap_or_else(|_| "Unknown".to_string()),
    }
}

#[tauri::command]
pub async fn open_external(url: String) -> Result<(), String> {
    match tauri::api::shell::open(&url, None) {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to open URL: {}", e)),
    }
}

#[tauri::command]
pub async fn show_notification(
    title: String,
    body: String,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    let notification = tauri::api::notification::Notification::new(
        "com.agentforge.app",
    )
    .title(title)
    .body(body);
    
    match notification.show() {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to show notification: {}", e)),
    }
}

#[tauri::command]
pub async fn get_clipboard() -> Result<String, String> {
    match clipboard::read_text() {
        Some(text) => Ok(text),
        None => Err("Failed to read clipboard".to_string()),
    }
}

#[tauri::command]
pub async fn set_clipboard(text: String) -> Result<(), String> {
    match clipboard::write_text(text) {
        true => Ok(()),
        false => Err("Failed to write to clipboard".to_string()),
    }
}

#[tauri::command]
pub async fn read_file(path: String) -> Result<String, String> {
    match std::fs::read_to_string(&path) {
        Ok(content) => Ok(content),
        Err(e) => Err(format!("Failed to read file: {}", e)),
    }
}

#[tauri::command]
pub async fn write_file(path: String, content: String) -> Result<(), String> {
    match std::fs::write(&path, content) {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to write file: {}", e)),
    }
}

#[tauri::command]
pub async fn select_file(
    title: Option<String>,
    filters: Option<Vec<(String, Vec<String>)>>,
) -> Result<Option<String>, String> {
    let mut dialog_builder = dialog::FileDialogBuilder::new();
    
    if let Some(t) = title {
        dialog_builder = dialog_builder.set_title(&t);
    }
    
    if let Some(f) = filters {
        for (name, extensions) in f {
            dialog_builder = dialog_builder.add_filter(name, &extensions);
        }
    }
    
    let (tx, rx) = std::sync::mpsc::channel();
    
    dialog_builder.pick_file(move |path| {
        let _ = tx.send(path.map(|p| p.to_string_lossy().to_string()));
    });
    
    rx.recv()
        .map_err(|e| format!("Failed to receive file path: {}", e))
}

#[tauri::command]
pub async fn select_folder(title: Option<String>) -> Result<Option<String>, String> {
    let mut dialog_builder = dialog::FileDialogBuilder::new();
    
    if let Some(t) = title {
        dialog_builder = dialog_builder.set_title(&t);
    }
    
    let (tx, rx) = std::sync::mpsc::channel();
    
    dialog_builder.pick_folder(move |path| {
        let _ = tx.send(path.map(|p| p.to_string_lossy().to_string()));
    });
    
    rx.recv()
        .map_err(|e| format!("Failed to receive folder path: {}", e))
}

#[tauri::command]
pub async fn save_file(
    title: Option<String>,
    default_name: Option<String>,
    filters: Option<Vec<(String, Vec<String>)>>,
) -> Result<Option<String>, String> {
    let mut dialog_builder = dialog::FileDialogBuilder::new();
    
    if let Some(t) = title {
        dialog_builder = dialog_builder.set_title(&t);
    }
    
    if let Some(name) = default_name {
        dialog_builder = dialog_builder.set_file_name(&name);
    }
    
    if let Some(f) = filters {
        for (name, extensions) in f {
            dialog_builder = dialog_builder.add_filter(name, &extensions);
        }
    }
    
    let (tx, rx) = std::sync::mpsc::channel();
    
    dialog_builder.save_file(move |path| {
        let _ = tx.send(path.map(|p| p.to_string_lossy().to_string()));
    });
    
    rx.recv()
        .map_err(|e| format!("Failed to receive save path: {}", e))
}

#[tauri::command]
pub async fn send_notification(
    title: String,
    body: String,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    crate::tray::send_notification(&app_handle, &title, &body)
}

#[tauri::command]
pub async fn send_order_notification(
    order_id: String,
    customer: String,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    crate::tray::send_order_notification(&app_handle, &order_id, &customer)
}

#[tauri::command]
pub async fn send_task_notification(
    task_name: String,
    status: String,
    app_handle: tauri::AppHandle,
) -> Result<(), String> {
    crate::tray::send_task_notification(&app_handle, &task_name, &status)
}

#[tauri::command]
pub async fn hide_window(app_handle: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app_handle.get_window("main") {
        window.hide().map_err(|e| format!("Failed to hide window: {}", e))?;
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub async fn show_window(app_handle: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app_handle.get_window("main") {
        window.show().map_err(|e| format!("Failed to show window: {}", e))?;
        window.set_focus().map_err(|e| format!("Failed to focus window: {}", e))?;
        Ok(())
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub async fn toggle_window(app_handle: tauri::AppHandle) -> Result<bool, String> {
    if let Some(window) = app_handle.get_window("main") {
        let is_visible = window.is_visible().unwrap_or(false);
        if is_visible {
            window.hide().map_err(|e| format!("Failed to hide window: {}", e))?;
            Ok(false)
        } else {
            window.show().map_err(|e| format!("Failed to show window: {}", e))?;
            window.set_focus().map_err(|e| format!("Failed to focus window: {}", e))?;
            Ok(true)
        }
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub async fn is_background_mode(app_handle: tauri::AppHandle) -> Result<bool, String> {
    if let Some(window) = app_handle.get_window("main") {
        Ok(!window.is_visible().unwrap_or(true))
    } else {
        Err("Main window not found".to_string())
    }
}

#[tauri::command]
pub async fn get_notification_count(app_handle: tauri::AppHandle) -> Result<u32, String> {
    let state = app_handle.state::<AppState>();
    let count = state.notification_count.lock().await;
    Ok(*count)
}

#[tauri::command]
pub async fn increment_notification_count(app_handle: tauri::AppHandle) -> Result<u32, String> {
    let state = app_handle.state::<AppState>();
    let mut count = state.notification_count.lock().await;
    *count += 1;
    
    crate::tray::update_tray_notification_badge(&app_handle, *count > 0);
    
    Ok(*count)
}

#[tauri::command]
pub async fn clear_notification_count(app_handle: tauri::AppHandle) -> Result<(), String> {
    let state = app_handle.state::<AppState>();
    let mut count = state.notification_count.lock().await;
    *count = 0;
    
    crate::tray::update_tray_notification_badge(&app_handle, false);
    
    Ok(())
}

#[tauri::command]
pub async fn enable_auto_launch() -> Result<(), String> {
    #[cfg(not(target_os = "linux"))]
    {
        use auto_launch::{AutoLaunch, AutoLaunchBuilder};
        
        let app_name = "AgentForge";
        let app_path = std::env::current_exe()
            .map_err(|e| format!("Failed to get app path: {}", e))?
            .to_string_lossy()
            .to_string();
        
        let auto_launch: AutoLaunch = AutoLaunchBuilder::new()
            .set_app_name(app_name)
            .set_app_path(&app_path)
            .build()
            .map_err(|e| format!("Failed to build auto launch: {}", e))?;
        
        auto_launch.enable()
            .map_err(|e| format!("Failed to enable auto launch: {}", e))?;
        
        Ok(())
    }
    
    #[cfg(target_os = "linux")]
    {
        Err("Auto launch not supported on Linux".to_string())
    }
}

#[tauri::command]
pub async fn disable_auto_launch() -> Result<(), String> {
    #[cfg(not(target_os = "linux"))]
    {
        use auto_launch::{AutoLaunch, AutoLaunchBuilder};
        
        let app_name = "AgentForge";
        let app_path = std::env::current_exe()
            .map_err(|e| format!("Failed to get app path: {}", e))?
            .to_string_lossy()
            .to_string();
        
        let auto_launch: AutoLaunch = AutoLaunchBuilder::new()
            .set_app_name(app_name)
            .set_app_path(&app_path)
            .build()
            .map_err(|e| format!("Failed to build auto launch: {}", e))?;
        
        auto_launch.disable()
            .map_err(|e| format!("Failed to disable auto launch: {}", e))?;
        
        Ok(())
    }
    
    #[cfg(target_os = "linux")]
    {
        Err("Auto launch not supported on Linux".to_string())
    }
}

#[tauri::command]
pub async fn is_auto_launch_enabled() -> Result<bool, String> {
    #[cfg(not(target_os = "linux"))]
    {
        use auto_launch::{AutoLaunch, AutoLaunchBuilder};
        
        let app_name = "AgentForge";
        let app_path = std::env::current_exe()
            .map_err(|e| format!("Failed to get app path: {}", e))?
            .to_string_lossy()
            .to_string();
        
        let auto_launch: AutoLaunch = AutoLaunchBuilder::new()
            .set_app_name(app_name)
            .set_app_path(&app_path)
            .build()
            .map_err(|e| format!("Failed to build auto launch: {}", e))?;
        
        auto_launch.is_enabled()
            .map_err(|e| format!("Failed to check auto launch: {}", e))
    }
    
    #[cfg(target_os = "linux")]
    {
        Ok(false)
    }
}
