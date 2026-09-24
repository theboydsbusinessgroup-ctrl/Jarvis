import Foundation
import ScreenCaptureKit
import CoreImage
import CoreMedia
import ImageIO
import UniformTypeIdentifiers

final class FrameOutput: NSObject, SCStreamOutput {
    let queue = DispatchQueue(label: "jarvis.vision.frames")
    private let context = CIContext()
    private let relay = VisionRelayClient()
    private var lastSent = Date.distantPast

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        guard type == .screen, sampleBuffer.isValid,
              Date().timeIntervalSince(lastSent) >= 0.5,
              let pixelBuffer = sampleBuffer.imageBuffer else { return }
        lastSent = Date()
        let image = CIImage(cvPixelBuffer: pixelBuffer)
        guard let data = context.jpegRepresentation(of: image, colorSpace: CGColorSpaceCreateDeviceRGB(), options: [:]) else { return }
        Task { try? await relay.send(frame: data) }
    }
}
