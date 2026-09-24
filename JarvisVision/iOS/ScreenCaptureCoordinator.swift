import Foundation
import ScreenCaptureKit
import CoreMedia

@MainActor
final class ScreenCaptureCoordinator: NSObject, ObservableObject {
    @Published var isRunning = false
    @Published var status = "Ready"
    private var stream: SCStream?
    private let output = FrameOutput()

    func start() async {
        do {
            // Production UI should use SCContentSharingPicker so the user explicitly
            // selects the screen/app/window to share.
            status = "Choose what to share"
            SCContentSharingPicker.shared.isActive = true
            // Stream creation is completed from the picker observer callback.
        } catch {
            status = "Capture error: \(error.localizedDescription)"
        }
    }

    func attach(filter: SCContentFilter) async throws {
        let config = SCStreamConfiguration()
        config.width = 1280
        config.height = 720
        config.minimumFrameInterval = CMTime(value: 1, timescale: 2)
        config.queueDepth = 3
        let stream = SCStream(filter: filter, configuration: config, delegate: nil)
        try stream.addStreamOutput(output, type: .screen, sampleHandlerQueue: output.queue)
        try await stream.startCapture()
        self.stream = stream
        isRunning = true
        status = "Jarvis can see this share"
    }

    func stop() {
        let current = stream
        stream = nil
        isRunning = false
        status = "Stopped"
        Task { try? await current?.stopCapture() }
    }
}
