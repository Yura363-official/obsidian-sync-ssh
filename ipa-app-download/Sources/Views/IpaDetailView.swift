import SwiftUI

struct IpaDetailView: View {
    @EnvironmentObject private var library: IpaLibrary
    let entry: IpaEntry

    @State private var icon: UIImage?
    @State private var showingShare = false

    var body: some View {
        List {
            Section {
                HStack(spacing: 16) {
                    iconView
                    VStack(alignment: .leading, spacing: 4) {
                        Text(entry.metadata.displayName)
                            .font(.title3.weight(.bold))
                        Text(entry.metadata.bundleIdentifier)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.vertical, 6)
            }

            Section("Метаданные") {
                infoRow("Версия", entry.metadata.version)
                infoRow("Сборка", entry.metadata.build)
                infoRow("Минимальная iOS", entry.metadata.minimumOSVersion)
                infoRow("Исполняемый файл", entry.metadata.executableName)
                infoRow("Размер", ByteCountFormatter.string(fromByteCount: entry.fileSizeBytes, countStyle: .file))
                infoRow("Оригинальное имя", entry.originalFileName)
            }

            Section("Установка через Sideloadly") {
                Button {
                    showingShare = true
                } label: {
                    Label("Поделиться .ipa (в Sideloadly / AltStore)", systemImage: "square.and.arrow.up")
                }
                Text("Отправь файл на компьютер с Sideloadly или в AltStore на этом же устройстве, затем подпиши своим Apple ID и установи.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle(entry.metadata.displayName)
        .navigationBarTitleDisplayMode(.inline)
        .task { icon = library.icon(for: entry) }
        .sheet(isPresented: $showingShare) {
            ShareSheet(items: [library.fileURL(for: entry)])
        }
    }

    private func infoRow(_ title: String, _ value: String) -> some View {
        HStack {
            Text(title).foregroundStyle(.secondary)
            Spacer()
            Text(value).multilineTextAlignment(.trailing)
        }
        .font(.subheadline)
    }

    @ViewBuilder private var iconView: some View {
        if let icon {
            Image(uiImage: icon)
                .resizable()
                .frame(width: 64, height: 64)
                .clipShape(RoundedRectangle(cornerRadius: 14))
        } else {
            RoundedRectangle(cornerRadius: 14)
                .fill(.quaternary)
                .frame(width: 64, height: 64)
                .overlay(Image(systemName: "app.dashed").foregroundStyle(.secondary))
        }
    }
}

/// Обёртка над UIActivityViewController для SwiftUI.
struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]

    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }

    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}
