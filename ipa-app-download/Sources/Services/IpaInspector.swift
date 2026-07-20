import Foundation
import UIKit
import ZIPFoundation

enum IpaInspectorError: LocalizedError {
    case cannotOpenArchive
    case noAppBundle
    case noInfoPlist
    case malformedInfoPlist

    var errorDescription: String? {
        switch self {
        case .cannotOpenArchive: return "Не удалось открыть .ipa как архив."
        case .noAppBundle:       return "Внутри .ipa нет папки Payload/*.app."
        case .noInfoPlist:       return "В .app не найден Info.plist."
        case .malformedInfoPlist:return "Info.plist повреждён или в неизвестном формате."
        }
    }
}

/// Разбирает `.ipa` (это обычный zip) и достаёт метаданные и иконку.
///
/// Структура: `Payload/<Name>.app/Info.plist` + файлы иконок в том же `.app`.
struct IpaInspector {

    func inspect(url: URL) throws -> (metadata: IpaMetadata, icon: UIImage?) {
        guard let archive = Archive(url: url, accessMode: .read) else {
            throw IpaInspectorError.cannotOpenArchive
        }

        guard let appDirPath = appBundlePath(in: archive) else {
            throw IpaInspectorError.noAppBundle
        }

        let infoPlistPath = appDirPath + "Info.plist"
        guard let plistEntry = archive[infoPlistPath] else {
            throw IpaInspectorError.noInfoPlist
        }

        let plistData = try readEntry(plistEntry, from: archive)
        guard let plist = try PropertyListSerialization
            .propertyList(from: plistData, options: [], format: nil) as? [String: Any]
        else {
            throw IpaInspectorError.malformedInfoPlist
        }

        let iconFileName = primaryIconFileName(from: plist)
        let metadata = IpaMetadata(
            displayName: (plist["CFBundleDisplayName"] as? String)
                ?? (plist["CFBundleName"] as? String)
                ?? bundleName(fromAppPath: appDirPath),
            bundleIdentifier: plist["CFBundleIdentifier"] as? String ?? "—",
            version: plist["CFBundleShortVersionString"] as? String ?? "—",
            build: plist["CFBundleVersion"] as? String ?? "—",
            minimumOSVersion: plist["MinimumOSVersion"] as? String ?? "—",
            executableName: plist["CFBundleExecutable"] as? String ?? "—",
            primaryIconFileName: iconFileName
        )

        let icon = iconFileName.flatMap { name in
            loadIcon(named: name, appDirPath: appDirPath, archive: archive)
        }

        return (metadata, icon)
    }

    // MARK: - Внутреннее

    /// Находит путь `Payload/<Name>.app/` внутри архива.
    private func appBundlePath(in archive: Archive) -> String? {
        for entry in archive {
            let path = entry.path
            guard path.hasPrefix("Payload/") else { continue }
            if let range = path.range(of: ".app/") {
                return String(path[..<range.upperBound])
            }
        }
        return nil
    }

    private func readEntry(_ entry: Entry, from archive: Archive) throws -> Data {
        var data = Data()
        _ = try archive.extract(entry) { chunk in
            data.append(chunk)
        }
        return data
    }

    private func bundleName(fromAppPath path: String) -> String {
        // "Payload/Foo.app/" -> "Foo"
        let components = path.split(separator: "/")
        guard let appComponent = components.last(where: { $0.hasSuffix(".app") }) else {
            return "Приложение"
        }
        return String(appComponent.dropLast(4))
    }

    /// Достаёт имя основного файла иконки из CFBundleIcons (берём самый крупный).
    private func primaryIconFileName(from plist: [String: Any]) -> String? {
        if let icons = plist["CFBundleIcons"] as? [String: Any],
           let primary = icons["CFBundlePrimaryIcon"] as? [String: Any],
           let files = primary["CFBundleIconFiles"] as? [String],
           let last = files.last {
            return last
        }
        if let files = plist["CFBundleIconFiles"] as? [String], let last = files.last {
            return last
        }
        if let name = plist["CFBundleIconFile"] as? String {
            return name
        }
        return nil
    }

    /// Файлы иконок хранятся как `<name>.png`, `<name>@2x.png`, `<name>@3x.png`.
    /// Пробуем найти наиболее подходящий вариант в архиве.
    private func loadIcon(named baseName: String, appDirPath: String, archive: Archive) -> UIImage? {
        let candidates = [
            "\(baseName)@3x.png",
            "\(baseName)@2x.png",
            "\(baseName).png",
            baseName // на случай, если имя уже содержит расширение
        ]
        for candidate in candidates {
            let fullPath = appDirPath + candidate
            if let entry = archive[fullPath],
               let data = try? readEntry(entry, from: archive) {
                // Иконки .ipa часто CgBI-оптимизированы Apple; UIImage их читает.
                if let image = UIImage(data: data) {
                    return image
                }
            }
        }
        return nil
    }
}
