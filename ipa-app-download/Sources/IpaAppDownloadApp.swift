import SwiftUI

@main
struct IpaAppDownloadApp: App {
    @StateObject private var library = IpaLibrary()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(library)
        }
    }
}
