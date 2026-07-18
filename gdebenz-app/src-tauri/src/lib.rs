use tauri::{WebviewUrl, WebviewWindowBuilder};

const TOGGLE_SCRIPT: &str = include_str!("../inject/toggle.js");

fn allowed_host(host: &str) -> bool {
    host == "gdebenz.ru"
        || host.ends_with(".gdebenz.ru")
        || host == "gdebenz.org"
        || host.ends_with(".gdebenz.org")
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let url: tauri::Url = "https://gdebenz.ru/".parse().unwrap();
            let builder = WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url))
                .initialization_script(TOGGLE_SCRIPT)
                .on_navigation(|url| match url.scheme() {
                    "https" | "http" => url.host_str().is_some_and(allowed_host),
                    // tauri:// / about:blank and similar internal schemes
                    _ => true,
                });

            #[cfg(desktop)]
            let builder = builder
                .title("GdeBenz")
                .inner_size(1200.0, 800.0)
                .center();

            builder.build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
