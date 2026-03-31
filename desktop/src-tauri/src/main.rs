#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::Manager;
use std::sync::Arc;
use tokio::sync::Mutex;

mod commands;
mod tray;
mod updater;

pub struct AppState {
    pub backend_url: String,
    pub is_connected: Arc<Mutex<bool>>,
    pub notification_count: Arc<Mutex<u32>>,
    pub is_background_mode: Arc<Mutex<bool>>,
}

fn main() {
    let state = AppState {
        backend_url: "http://localhost:8000".to_string(),
        is_connected: Arc::new(Mutex::new(false)),
        notification_count: Arc::new(Mutex::new(0)),
        is_background_mode: Arc::new(Mutex::new(false)),
    };

    tauri::Builder::default()
        .manage(state)
        .setup(|app| {
            let handle = app.handle();
            
            tray::setup_tray(handle)?;
            
            let app_handle = app.handle();
            tauri::async_runtime::spawn(async move {
                updater::check_for_updates(app_handle).await;
            });
            
            let app_handle = app.handle();
            tauri::async_runtime::spawn(async move {
                loop {
                    tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
                    let client = reqwest::Client::new();
                    let is_connected = client
                        .get("http://localhost:8000/health")
                        .timeout(std::time::Duration::from_secs(5))
                        .send()
                        .await
                        .map(|r| r.status().is_success())
                        .unwrap_or(false);
                    
                    {
                        let state = app_handle.state::<AppState>();
                        let mut connected = state.is_connected.lock().await;
                        *connected = is_connected;
                    }
                    
                    tray::update_tray_status(&app_handle, is_connected);
                }
            });
            
            if let Some(window) = app.get_window("main") {
                let app_handle = app.handle();
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        
                        let app_handle_clone = app_handle.clone();
                        tauri::async_runtime::spawn(async move {
                            if let Some(win) = app_handle_clone.get_window("main") {
                                let _ = win.hide();
                                
                                let state = app_handle_clone.state::<AppState>();
                                let mut bg_mode = state.is_background_mode.lock().await;
                                *bg_mode = true;
                                
                                let _ = tray::send_notification(
                                    &app_handle_clone,
                                    "AgentForge Running",
                                    "Application is running in the background",
                                );
                            }
                        });
                    }
                });
            }
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::check_backend_connection,
            commands::get_system_info,
            commands::open_external,
            commands::show_notification,
            commands::get_clipboard,
            commands::set_clipboard,
            commands::read_file,
            commands::write_file,
            commands::select_file,
            commands::select_folder,
            commands::save_file,
            commands::send_notification,
            commands::send_order_notification,
            commands::send_task_notification,
            commands::hide_window,
            commands::show_window,
            commands::toggle_window,
            commands::is_background_mode,
            commands::get_notification_count,
            commands::increment_notification_count,
            commands::clear_notification_count,
            commands::enable_auto_launch,
            commands::disable_auto_launch,
            commands::is_auto_launch_enabled,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
