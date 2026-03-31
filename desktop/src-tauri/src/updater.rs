use tauri::{AppHandle, Manager, UpdaterEvent};
use tauri::updater::UpdateBuilder;
use log::{info, error};

pub async fn check_for_updates(app: AppHandle) {
    match UpdateBuilder::new(&app).check().await {
        Ok(update) => {
            if update.is_update_available() {
                info!("Update available: {:?}", update.latest_version());
                
                if let Some(window) = app.get_window("main") {
                    let _ = window.emit("update-available", update.latest_version());
                }
                
                let _ = update.download_and_install(|_, _| {}, || {}).await;
            }
        }
        Err(e) => {
            error!("Failed to check for updates: {}", e);
        }
    }
}

pub async fn check_for_updates_manual(app: AppHandle) {
    match UpdateBuilder::new(&app).check().await {
        Ok(update) => {
            if update.is_update_available() {
                if let Some(window) = app.get_window("main") {
                    let _ = window.emit("update-available-manual", serde_json::json!({
                        "version": update.latest_version(),
                        "date": update.current_version(),
                        "notes": update.body()
                    }));
                }
            } else {
                if let Some(window) = app.get_window("main") {
                    let _ = window.emit("no-update-available", true);
                }
            }
        }
        Err(e) => {
            error!("Failed to check for updates: {}", e);
            if let Some(window) = app.get_window("main") {
                let _ = window.emit("update-check-error", e.to_string());
            }
        }
    }
}

pub async fn download_and_install_update(app: AppHandle) -> Result<(), String> {
    match UpdateBuilder::new(&app).check().await {
        Ok(update) => {
            if update.is_update_available() {
                update
                    .download_and_install(
                        |chunk_length, total| {
                            if let Some(window) = app.get_window("main") {
                                let progress = if total > 0 {
                                    (chunk_length as f64 / total as f64 * 100.0) as u32
                                } else {
                                    0
                                };
                                let _ = window.emit("update-progress", progress);
                            }
                        },
                        || {
                            if let Some(window) = app.get_window("main") {
                                let _ = window.emit("update-downloaded", true);
                            }
                        },
                    )
                    .await
                    .map_err(|e| format!("Failed to install update: {}", e))?;
                
                Ok(())
            } else {
                Err("No update available".to_string())
            }
        }
        Err(e) => Err(format!("Failed to check for updates: {}", e)),
    }
}

pub fn setup_updater_events(app: &AppHandle) {
    app.listen_global("tauri://update-available", |event| {
        info!("Update available event: {:?}", event.payload());
    });
    
    app.listen_global("tauri://update-install", |_event| {
        info!("Installing update...");
    });
    
    app.listen_global("tauri://update-downloaded", |_event| {
        info!("Update downloaded successfully");
    });
}
