import Foundation

actor APIClient {
    static let shared = APIClient()

    #if DEBUG
    // For simulator, use localhost; for real device, use your Mac's IP
    private let baseURL = "http://localhost:8000"
    #else
    private let baseURL = "https://your-server.com"  // TODO: configure
    #endif

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 180
        config.timeoutIntervalForResource = 300
        return URLSession(configuration: config)
    }()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .useDefaultKeys
        return d
    }()

    func evaluate(_ request: EvaluationRequest) async throws -> EvaluationResponse {
        let url = URL(string: "\(baseURL)/api/evaluate")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        urlRequest.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        let body = buildMultipartBody(request, boundary: boundary)
        urlRequest.httpBody = body

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode == 200 {
            return try decoder.decode(EvaluationResponse.self, from: data)
        } else {
            let errorMsg = String(data: data, encoding: .utf8) ?? "Unknown error"
            throw APIError.serverError(httpResponse.statusCode, errorMsg)
        }
    }

    private func buildMultipartBody(_ request: EvaluationRequest, boundary: String) -> Data {
        var body = Data()

        // Append images
        for (index, imageData) in request.imagesNatural.enumerated() {
            appendFile(&body, fieldName: "images_natural", fileName: "natural_\(index).jpg",
                       data: imageData, boundary: boundary)
        }
        for (index, imageData) in request.imagesLamp.enumerated() {
            appendFile(&body, fieldName: "images_lamp", fileName: "lamp_\(index).jpg",
                       data: imageData, boundary: boundary)
        }
        for (index, imageData) in request.imagesMacro.enumerated() {
            appendFile(&body, fieldName: "images_macro", fileName: "macro_\(index).jpg",
                       data: imageData, boundary: boundary)
        }

        // Append optional fields
        if let weight = request.weightGrams {
            appendField(&body, name: "weight_g", value: String(format: "%.1f", weight), boundary: boundary)
        }
        if let mine = request.mine {
            appendField(&body, name: "mine", value: mine, boundary: boundary)
        }
        if let askPrice = request.askPrice {
            appendField(&body, name: "ask_price", value: String(format: "%.0f", askPrice), boundary: boundary)
        }

        // Closing boundary
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        return body
    }

    private func appendFile(_ body: inout Data, fieldName: String, fileName: String,
                             data: Data, boundary: String) {
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n".data(using: .utf8)!)
    }

    private func appendField(_ body: inout Data, name: String, value: String, boundary: String) {
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(value)\r\n".data(using: .utf8)!)
    }

    func healthCheck() async throws -> Bool {
        let url = URL(string: "\(baseURL)/health")!
        let (data, response) = try await session.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            return false
        }
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            return json["status"] as? String == "ok"
        }
        return false
    }
}

enum APIError: LocalizedError {
    case invalidResponse
    case serverError(Int, String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "服务器无响应"
        case .serverError(let code, let msg):
            return "服务器错误 (\(code)): \(msg)"
        }
    }
}
