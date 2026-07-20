import Foundation
import Combine
import UIKit

/// Каталог импортированных `.ipa`. Файлы копируются в песочницу приложения
/// (Documents/IpaLibrary), метаданные — в index.json рядом.
@MainActor
final class IpaLibrary: ObservableObject {
    @Published private(set) var entries: [IpaEntry] = []
    @Published var lastError: String?

    private let fileManager = FileManager.default
    private let inspector = IpaInspector()

    private var libraryDir: URL {
        let docs = fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let dir = docs.appendingPathComponent("IpaLibrary", isDirectory: true)
        if !fileManager.fileExists(atPath: dir.path) {
            try? fileManager.createDirectory(at: dir, withIntermediateDirectories: true)
        }
        return dir
    }

    private var indexURL: URL {
        libraryDir.appendingPathComponent("index.json")
    }

    init() {
        load()
    }

    func fileURL(for entry: IpaEntry) -> URL {
        libraryDir.appendingPathComponent(entry.storedFileName)
    }

    /// Импортирует .ipa: разбирает метаданные, копирует файл в каталог, сохраняет индекс.
    func importIpa(from sourceURL: URL) {
        // Файл из document picker требует security-scoped доступа.
        let needsStop = sourceURL.startAccessingSecurityScopedResource()
        defer { if needsStop { sourceURL.stopAccessingSecurityScopedResource() } }

        do {
            let (metadata, _) = try inspector.inspect(url: sourceURL)

            let storedName = "\(UUID().uuidString).ipa"
            let destination = libraryDir.appendingPathComponent(storedName)
            if fileManager.fileExists(atPath: destination.path) {
                try fileManager.removeItem(at: destination)
            }
            try fileManager.copyItem(at: sourceURL, to: destination)

            let size = (try? fileManager.attributesOfItem(atPath: destination.path)[.size] as? Int64) ?? nil

            let entry = IpaEntry(
                storedFileName: storedName,
                originalFileName: sourceURL.lastPathComponent,
                fileSizeBytes: size ?? 0,
                metadata: metadata
            )
            entries.insert(entry, at: 0)
            save()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func icon(for entry: IpaEntry) -> UIImage? {
        (try? inspector.inspect(url: fileURL(for: entry)))?.icon
    }

    func delete(_ entry: IpaEntry) {
        try? fileManager.removeItem(at: fileURL(for: entry))
        entries.removeAll { $0.id == entry.id }
        save()
    }

    // MARK: - Персистентность

    private func load() {
        guard let data = try? Data(contentsOf: indexURL),
              let decoded = try? JSONDecoder().decode([IpaEntry].self, from: data)
        else { return }
        entries = decoded
    }

    private func save() {
        do {
            let data = try JSONEncoder().encode(entries)
            try data.write(to: indexURL, options: .atomic)
        } catch {
            lastError = "Не удалось сохранить каталог: \(error.localizedDescription)"
        }
    }
}
