import Foundation

actor VisionRelayClient {
    private let endpoint = URL(string: ProcessInfo.processInfo.environment["JARVIS_VISION_RELAY"] ?? "https://YOUR-RELAY.example.com/api/frame")!
    private let token = ProcessInfo.processInfo.environment["JARVIS_VISION_TOKEN"] ?? ""

    func send(frame: Data) async throws {
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("image/jpeg", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.httpBody = frame
        let (_, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 204 else { throw URLError(.badServerResponse) }
    }
}
