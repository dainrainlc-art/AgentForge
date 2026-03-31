use tauri::{
    AppHandle, CustomMenuItem, Manager, SystemTray, SystemTrayEvent, SystemTrayMenu,
    SystemTrayMenuItem, SystemTraySubmenu,
};

pub fn create_tray_menu(connected: bool, has_notifications: bool) -> SystemTrayMenu {
    let quit = CustomMenuItem::new("quit".to_string(), "Quit AgentForge");
    let show = CustomMenuItem::new("show".to_string(), "Show Window");
    let hide = CustomMenuItem::new("hide".to_string(), "Hide Window");
    let settings = CustomMenuItem::new("settings".to_string(), "Settings...");
    let check_updates = CustomMenuItem::new("check_updates".to_string(), "Check for Updates");
    let restart_backend = CustomMenuItem::new("restart_backend".to_string(), "Restart Backend");
    
    let status_text = if connected {
        "● Connected"
    } else {
        "○ Disconnected"
    };
    let status_item = CustomMenuItem::new("status".to_string(), status_text);
    
    let notification_badge = if has_notifications {
        "🔔 Notifications (New)"
    } else {
        "🔔 Notifications"
    };
    let notification_item = CustomMenuItem::new("notifications".to_string(), notification_badge);
    
    let quick_action_dashboard = CustomMenuItem::new("quick_dashboard".to_string(), "📊 Dashboard");
    let quick_action_chat = CustomMenuItem::new("quick_chat".to_string(), "💬 Chat");
    let quick_action_tasks = CustomMenuItem::new("quick_tasks".to_string(), "✅ Tasks");
    let quick_action_analytics = CustomMenuItem::new("quick_analytics".to_string(), "📈 Analytics");
    
    let quick_actions_submenu = SystemTraySubmenu::new(
        "⚡ Quick Actions",
        SystemTrayMenu::new()
            .add_item(quick_action_dashboard)
            .add_item(quick_action_chat)
            .add_item(quick_action_tasks)
            .add_item(quick_action_analytics),
    );
    
    let tools_docs = CustomMenuItem::new("tools_docs".to_string(), "📚 Documentation");
    let tools_logs = CustomMenuItem::new("tools_logs".to_string(), "📋 View Logs");
    let tools_cache = CustomMenuItem::new("tools_cache".to_string(), "🗑️ Clear Cache");
    
    let tools_submenu = SystemTraySubmenu::new(
        "🛠️ Tools",
        SystemTrayMenu::new()
            .add_item(tools_docs)
            .add_item(tools_logs)
            .add_item(tools_cache),
    );
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(status_item)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(notification_item)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_submenu(quick_actions_submenu)
        .add_submenu(tools_submenu)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(show)
        .add_item(hide)
        .add_item(restart_backend)
        .add_item(settings)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(check_updates)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);
    
    tray_menu
}

pub fn setup_tray(app: &AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let tray_menu = create_tray_menu(true, false);
    let system_tray = SystemTray::new().with_menu(tray_menu);
    
    system_tray.build(app)?;
    
    Ok(())
}

pub fn handle_tray_event(app: &AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::LeftClick { .. } => {
            if let Some(window) = app.get_window("main") {
                if window.is_visible().unwrap_or(false) {
                    let _ = window.hide();
                } else {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
        }
        SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
            "quit" => {
                std::process::exit(0);
            }
            "show" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                }
            }
            "hide" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.hide();
                }
            }
            "settings" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/settings");
                }
            }
            "check_updates" => {
                let app_handle = app.clone();
                tauri::async_runtime::spawn(async move {
                    crate::updater::check_for_updates_manual(app_handle).await;
                });
            }
            "restart_backend" => {
                let app_handle = app.clone();
                tauri::async_runtime::spawn(async move {
                    if let Err(e) = restart_backend_service(app_handle).await {
                        eprintln!("Failed to restart backend: {}", e);
                    }
                });
            }
            "notifications" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/notifications");
                }
            }
            "quick_dashboard" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/dashboard");
                }
            }
            "quick_chat" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/chat");
                }
            }
            "quick_tasks" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/tasks");
                }
            }
            "quick_analytics" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/analytics");
                }
            }
            "tools_docs" => {
                let _ = tauri::api::shell::open("https://agentforge.readme.io", None);
            }
            "tools_logs" => {
                if let Some(window) = app.get_window("main") {
                    let _ = window.show();
                    let _ = window.set_focus();
                    let _ = window.emit("navigate", "/logs");
                }
            }
            "tools_cache" => {
                let app_handle = app.clone();
                tauri::async_runtime::spawn(async move {
                    if let Err(e) = clear_cache_service(app_handle).await {
                        eprintln!("Failed to clear cache: {}", e);
                    }
                });
            }
            _ => {}
        },
        _ => {}
    }
}

async fn restart_backend_service(app: AppHandle) -> Result<(), String> {
    use std::process::Command;
    
    #[cfg(target_os = "windows")]
    let output = Command::new("docker")
        .args(&["restart", "agentforge-backend"])
        .output();
    
    #[cfg(not(target_os = "windows"))]
    let output = Command::new("docker")
        .args(&["restart", "agentforge-backend"])
        .output();
    
    match output {
        Ok(result) => {
            if result.status.success() {
                if let Some(window) = app.get_window("main") {
                    let _ = window.emit("backend-restarted", true);
                }
                
                let _ = send_notification(
                    &app,
                    "Backend Restarted",
                    "Backend service has been restarted successfully",
                );
                
                Ok(())
            } else {
                Err(String::from_utf8_lossy(&result.stderr).to_string())
            }
        }
        Err(e) => Err(format!("Failed to execute restart command: {}", e)),
    }
}

async fn clear_cache_service(app: AppHandle) -> Result<(), String> {
    use std::fs;
    
    let cache_dir = app.path_resolver().app_cache_dir()
        .ok_or("Failed to get cache directory")?;
    
    if cache_dir.exists() {
        for entry in fs::read_dir(&cache_dir).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.is_file() {
                fs::remove_file(&path).map_err(|e| e.to_string())?;
            }
        }
    }
    
    if let Some(window) = app.get_window("main") {
        let _ = window.emit("cache-cleared", true);
    }
    
    let _ = send_notification(
        &app,
        "Cache Cleared",
        "Application cache has been cleared successfully",
    );
    
    Ok(())
}

pub fn update_tray_status(app: &AppHandle, connected: bool) {
    if let Some(tray) = app.tray_handle_by_id("main") {
        let status_text = if connected {
            "● Connected"
        } else {
            "○ Disconnected"
        };
        
        let _ = tray.set_title(status_text);
        
        let tooltip = if connected {
            "AgentForge - Connected"
        } else {
            "AgentForge - Disconnected"
        };
        
        let _ = tray.set_tooltip(tooltip);
    }
}

pub fn update_tray_notification_badge(app: &AppHandle, has_notifications: bool) {
    if let Some(tray) = app.tray_handle_by_id("main") {
        let badge_text = if has_notifications {
            "🔔 (New)"
        } else {
            "🔔"
        };
        
        let _ = tray.set_title(badge_text);
    }
}

pub fn send_notification(app: &AppHandle, title: &str, body: &str) -> Result<(), String> {
    use tauri::api::notification::Notification;
    
    let notification = Notification::new("com.agentforge.app")
        .title(title)
        .body(body)
        .icon("icon.png");
    
    match notification.show() {
        Ok(_) => {
            if let Some(window) = app.get_window("main") {
                let _ = window.emit("notification-sent", serde_json::json!({
                    "title": title,
                    "body": body,
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }));
            }
            Ok(())
        }
        Err(e) => Err(format!("Failed to show notification: {}", e)),
    }
}

pub fn send_order_notification(app: &AppHandle, order_id: &str, customer: &str) -> Result<(), String> {
    let title = format!("🛒 New Order: {}", order_id);
    let body = format!("Customer: {}", customer);
    send_notification(app, &title, &body)
}

pub fn send_task_notification(app: &AppHandle, task_name: &str, status: &str) -> Result<(), String> {
    let emoji = match status {
        "completed" => "✅",
        "failed" => "❌",
        "warning" => "⚠️",
        _ => "📋",
    };
    
    let title = format!("{} Task Update", emoji);
    let body = format!("{}: {}", task_name, status);
    send_notification(app, &title, &body)
}

pub fn send_system_notification(app: &AppHandle, event_type: &str, message: &str) -> Result<(), String> {
    let emoji = match event_type {
        "error" => "🚨",
        "warning" => "⚠️",
        "info" => "ℹ️",
        "success" => "✅",
        _ => "📢",
    };
    
    let title = format!("{} System {}", emoji, event_type.to_uppercase());
    send_notification(app, &title, message)
}
