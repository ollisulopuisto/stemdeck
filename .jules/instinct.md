## 2026-11-07 - PR29 Tauri lock compatibility

The failed Linux Rust check compiles tauri2.11.1 against tauri-runtime2.12.2,
runtime-wry2.12.3 and macros/codegen2.7.4. Runtime monitor APIs changed shape
and new macros name an error variant absent from tauri2.11.1. Keep the requested
Tauri2.11.1 update but resolve its runtime/runtime-wry2.11.1 and macros/codegen
2.6.1 family to the versions its own manifest was written against. No app Rust
source changes, API workaround or lint suppression. Cargo lock resolution and
diff checks pass; native Rust platform CI must pass before approved merge.
