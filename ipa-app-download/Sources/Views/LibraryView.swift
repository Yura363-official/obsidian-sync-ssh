import SwiftUI
import UniformTypeIdentifiers

struct LibraryView: View {
    @EnvironmentObject private var library: IpaLibrary
    @State private var showingImporter = false

    /// UTType для .ipa. Системного типа нет, поэтому берём как zip-архив/данные.
    private var ipaTypes: [UTType] {
        var types: [UTType] = [.data, .zip]
        if let ipa = UTType(filenameExtension: "ipa") {
            types.insert(ipa, at: 0)
        }
        return types
    }

    var body: some View {
        Group {
            if library.entries.isEmpty {
                emptyState
            } else {
                list
            }
        }
        .navigationTitle("IPA Download")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showingImporter = true
                } label: {
                    Label("Импорт .ipa", systemImage: "square.and.arrow.down")
                }
            }
        }
        .fileImporter(
            isPresented: $showingImporter,
            allowedContentTypes: ipaTypes,
            allowsMultipleSelection: false
        ) { result in
            if case let .success(urls) = result, let url = urls.first {
                library.importIpa(from: url)
            }
        }
        .alert("Ошибка", isPresented: Binding(
            get: { library.lastError != nil },
            set: { if !$0 { library.lastError = nil } }
        )) {
            Button("OK", role: .cancel) { library.lastError = nil }
        } message: {
            Text(library.lastError ?? "")
        }
    }

    private var list: some View {
        List {
            ForEach(library.entries) { entry in
                NavigationLink(value: entry) {
                    IpaRow(entry: entry)
                }
            }
            .onDelete { indexSet in
                indexSet.map { library.entries[$0] }.forEach(library.delete)
            }
        }
        .navigationDestination(for: IpaEntry.self) { entry in
            IpaDetailView(entry: entry)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "shippingbox")
                .font(.system(size: 56))
                .foregroundStyle(.secondary)
            Text("Каталог пуст")
                .font(.headline)
            Text("Нажми «Импорт .ipa» и выбери файл из «Файлов».\nПриложение разберёт его и покажет метаданные.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
    }
}

struct IpaRow: View {
    @EnvironmentObject private var library: IpaLibrary
    let entry: IpaEntry
    @State private var icon: UIImage?

    var body: some View {
        HStack(spacing: 12) {
            iconView
            VStack(alignment: .leading, spacing: 2) {
                Text(entry.metadata.displayName)
                    .font(.body.weight(.semibold))
                Text(entry.metadata.bundleIdentifier)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                Text("v\(entry.metadata.version) · \(ByteCountFormatter.string(fromByteCount: entry.fileSizeBytes, countStyle: .file))")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
        .task {
            if icon == nil { icon = library.icon(for: entry) }
        }
    }

    @ViewBuilder private var iconView: some View {
        if let icon {
            Image(uiImage: icon)
                .resizable()
                .frame(width: 44, height: 44)
                .clipShape(RoundedRectangle(cornerRadius: 10))
        } else {
            RoundedRectangle(cornerRadius: 10)
                .fill(.quaternary)
                .frame(width: 44, height: 44)
                .overlay(Image(systemName: "app.dashed").foregroundStyle(.secondary))
        }
    }
}
