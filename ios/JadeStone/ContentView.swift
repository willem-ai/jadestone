import SwiftUI

// MARK: - App Root

struct ContentView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            EvaluateTab()
                .tabItem {
                    Label("评估", systemImage: "camera.viewfinder")
                }
                .tag(0)

            NavigationStack {
                CaseListView()
            }
            .tabItem {
                Label("案例", systemImage: "archivebox")
            }
            .tag(1)

            NavigationStack {
                AboutView()
            }
            .tabItem {
                Label("关于", systemImage: "info.circle")
            }
            .tag(2)
        }
    }
}

// MARK: - Evaluate Tab

struct EvaluateTab: View {
    @State private var photos: [PhotoCategory: [UIImage]] = [
        .natural: [], .lamp: [], .macro: []
    ]
    @State private var currentCategory: PhotoCategory = .natural
    @State private var weightText = ""
    @State private var mineText = ""
    @State private var askPriceText = ""
    @State private var isEvaluating = false
    @State private var result: EvaluationResponse?
    @State private var errorMessage: String?
    @State private var showResult = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    categoryPicker
                    instructionsBanner
                    photoGrid
                    Divider().padding(.horizontal)
                    optionalFields
                    evaluateButton
                    if let error = errorMessage {
                        errorBanner(error)
                    }
                    disclaimerText
                }
                .padding(.vertical)
            }
            .navigationTitle("翡翠原石评估")
            .navigationDestination(isPresented: $showResult) {
                if let result = result {
                    ResultView(response: result)
                }
            }
        }
    }

    // MARK: - Subviews

    private var categoryPicker: some View {
        Picker("照片类型", selection: $currentCategory) {
            ForEach(PhotoCategory.allCases) { cat in
                Text("\(cat.icon) \(cat.rawValue) (\(photos[cat]?.count ?? 0)/\(cat.maxCount))")
                    .tag(cat)
            }
        }
        .pickerStyle(.segmented)
        .padding(.horizontal)
    }

    private var instructionsBanner: some View {
        HStack(spacing: 8) {
            Image(systemName: "info.circle.fill")
                .foregroundStyle(.blue)
            Text(currentCategory.instructions)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.horizontal)
    }

    private var photoGrid: some View {
        let catPhotos = photos[currentCategory] ?? []
        return LazyVGrid(columns: [GridItem(.adaptive(minimum: 100))], spacing: 8) {
            ForEach(Array(catPhotos.enumerated()), id: \.offset) { index, image in
                ZStack(alignment: .topTrailing) {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 100, height: 100)
                        .clipShape(RoundedRectangle(cornerRadius: 8))

                    Button {
                        removePhoto(at: index, category: currentCategory)
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.white)
                            .background(Circle().fill(.red))
                    }
                    .offset(x: 6, y: -6)
                }
            }

            if catPhotos.count < currentCategory.maxCount {
                PhotoPickerButton(category: currentCategory) { image in
                    addPhoto(image, category: currentCategory)
                }
            }
        }
        .padding(.horizontal)
    }

    private var optionalFields: some View {
        VStack(spacing: 12) {
            HStack {
                Text("重量 (克):")
                    .frame(width: 80, alignment: .leading)
                TextField("可选", text: $weightText)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
            }
            HStack {
                Text("场口:")
                    .frame(width: 80, alignment: .leading)
                TextField("可选, 如: 木那/莫西沙", text: $mineText)
                    .textFieldStyle(.roundedBorder)
            }
            HStack {
                Text("报价 (元):")
                    .frame(width: 80, alignment: .leading)
                TextField("可选", text: $askPriceText)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
            }
        }
        .padding(.horizontal)
    }

    private var evaluateButton: some View {
        Button {
            Task { await runEvaluation() }
        } label: {
            HStack {
                if isEvaluating {
                    ProgressView()
                        .tint(.white)
                    Text("评估中...")
                } else {
                    Image(systemName: "sparkle.magnifyingglass")
                    Text("开始评估")
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(canEvaluate ? Color.blue : Color.gray)
            .foregroundStyle(.white)
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
        .disabled(!canEvaluate || isEvaluating)
        .padding(.horizontal)
    }

    private func errorBanner(_ error: String) -> some View {
        Text(error)
            .foregroundStyle(.red)
            .font(.caption)
            .padding(.horizontal)
            .padding(8)
            .background(.red.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .padding(.horizontal)
    }

    private var disclaimerText: some View {
        Text("MVP阶段仅支持无开窗评估。基于皮壳+打灯做概率性推断, 每项推断标注置信度和依据。赌石有风险, 请理性决策。")
            .font(.caption2)
            .foregroundStyle(.secondary)
            .padding(.horizontal)
    }

    // MARK: - Logic

    private var canEvaluate: Bool {
        let totalPhotos = photos.values.flatMap { $0 }.count
        return totalPhotos >= 2 && !isEvaluating
    }

    private func addPhoto(_ image: UIImage, category: PhotoCategory) {
        var arr = photos[category] ?? []
        guard arr.count < category.maxCount else { return }
        arr.append(image)
        photos[category] = arr
    }

    private func removePhoto(at index: Int, category: PhotoCategory) {
        var arr = photos[category] ?? []
        guard index < arr.count else { return }
        arr.remove(at: index)
        photos[category] = arr
    }

    private func runEvaluation() async {
        isEvaluating = true
        errorMessage = nil

        let naturals = (photos[.natural] ?? []).compactMap {
            $0.jpegData(compressionQuality: 0.8)
        }
        let lamps = (photos[.lamp] ?? []).compactMap {
            $0.jpegData(compressionQuality: 0.8)
        }
        let macros = (photos[.macro] ?? []).compactMap {
            $0.jpegData(compressionQuality: 0.8)
        }

        let request = EvaluationRequest(
            imagesNatural: naturals,
            imagesLamp: lamps,
            imagesMacro: macros,
            weightGrams: Double(weightText),
            mine: mineText.isEmpty ? nil : mineText,
            askPrice: Double(askPriceText)
        )

        do {
            let response = try await APIClient.shared.evaluate(request)
            await MainActor.run {
                isEvaluating = false
                self.result = response
                self.showResult = true
            }
        } catch {
            await MainActor.run {
                isEvaluating = false
                errorMessage = error.localizedDescription
            }
        }
    }
}

// MARK: - Photo Picker

struct PhotoPickerButton: View {
    let category: PhotoCategory
    let onImagePicked: (UIImage) -> Void

    @State private var showCamera = false
    @State private var showLibrary = false

    var body: some View {
        Menu {
            Button { showCamera = true } label: {
                Label("拍照", systemImage: "camera")
            }
            Button { showLibrary = true } label: {
                Label("从相册选择", systemImage: "photo.on.rectangle")
            }
        } label: {
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(style: StrokeStyle(lineWidth: 2, dash: [6]))
                .foregroundStyle(.blue.opacity(0.5))
                .frame(width: 100, height: 100)
                .overlay {
                    VStack(spacing: 4) {
                        Image(systemName: "plus")
                            .font(.title2)
                        Text(category.icon)
                            .font(.caption2)
                    }
                    .foregroundStyle(.blue)
                }
        }
        .fullScreenCover(isPresented: $showCamera) {
            ImagePicker(source: .camera) { image in
                onImagePicked(image)
            }
        }
        .sheet(isPresented: $showLibrary) {
            ImagePicker(source: .photoLibrary) { image in
                onImagePicked(image)
            }
        }
    }
}

// MARK: - Image Picker (UIKit bridge)

struct ImagePicker: UIViewControllerRepresentable {
    let source: UIImagePickerController.SourceType
    let onImagePicked: (UIImage) -> Void

    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.sourceType = source
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: ImagePicker
        init(_ parent: ImagePicker) { self.parent = parent }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            if let image = info[.originalImage] as? UIImage {
                parent.onImagePicked(image)
            }
            parent.dismiss()
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}

// MARK: - Placeholder Views

struct CaseListView: View {
    var body: some View {
        List {
            Section("案例库") {
                Text("案例库将在后续版本开放")
                    .foregroundStyle(.secondary)
                Text("目前后端已有 12 个种子案例, 评估时会自动检索匹配")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("案例库")
    }
}

struct AboutView: View {
    var body: some View {
        Form {
            Section("版本") {
                Text("JadeStone MVP v4.0")
                Text("国产最强模型栈: 千问 + DeepSeek")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Section("模型") {
                LabeledContent("视觉识别", "通义千问 3.6 Plus")
                LabeledContent("概率推理", "DeepSeek V4 Pro")
                LabeledContent("案例检索", "Chinese-CLIP")
            }
            Section("免责声明") {
                Text("本App基于AI概率推断, 所有内部品质判断未经开窗验证。置信度<100%表示存在不确定性。赌石有风险, 请理性决策。本报告不构成投资建议。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("关于")
    }
}
