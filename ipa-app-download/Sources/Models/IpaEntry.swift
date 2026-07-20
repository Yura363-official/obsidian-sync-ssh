import Foundation

/// Метаданные одного `.ipa`, извлечённые из `Payload/*.app/Info.plist`.
struct IpaMetadata: Codable, Equatable {
    var displayName: String
    var bundleIdentifier: String
    var version: String            // CFBundleShortVersionString
    var build: String              // CFBundleVersion
    var minimumOSVersion: String
    var executableName: String

    /// Имя файла иконки внутри .app (если удалось определить).
    var primaryIconFileName: String?
}

/// Элемент каталога: импортированный `.ipa`, лежащий в песочнице приложения.
struct IpaEntry: Identifiable, Codable, Equatable {
    let id: UUID
    /// Имя файла на диске внутри каталога приложения (например `<uuid>.ipa`).
    var storedFileName: String
    /// Оригинальное имя файла, как его назвал пользователь.
    var originalFileName: String
    var fileSizeBytes: Int64
    var importedAt: Date
    var metadata: IpaMetadata

    init(id: UUID = UUID(),
         storedFileName: String,
         originalFileName: String,
         fileSizeBytes: Int64,
         importedAt: Date = Date(),
         metadata: IpaMetadata) {
        self.id = id
        self.storedFileName = storedFileName
        self.originalFileName = originalFileName
        self.fileSizeBytes = fileSizeBytes
        self.importedAt = importedAt
        self.metadata = metadata
    }
}
