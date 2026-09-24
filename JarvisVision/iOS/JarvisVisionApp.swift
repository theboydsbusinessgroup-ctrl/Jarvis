import SwiftUI

@main
struct JarvisVisionApp: App {
    @StateObject private var capture = ScreenCaptureCoordinator()

    var body: some Scene {
        WindowGroup {
            ContentView().environmentObject(capture)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var capture: ScreenCaptureCoordinator
    var body: some View {
        VStack(spacing: 20) {
            Text("Jarvis Vision").font(.largeTitle)
            Text(capture.status)
            Button(capture.isRunning ? "Stop Vision" : "Start Vision") {
                Task { capture.isRunning ? capture.stop() : await capture.start() }
            }
        }.padding()
    }
}
