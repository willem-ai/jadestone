# JadeStone iOS App

翡翠原石AI评估 — iPhone 客户端

## 环境要求

- macOS 13+ with Xcode 15+
- iOS 16+ 设备 (iPhone)
- Apple ID (免费账号即可, 用于代码签名)

## 在 iPhone 上安装运行

### 1. 创建 Xcode 项目

打开 Xcode → File → New → Project → iOS → App → 填写:

| 字段 | 值 |
|------|-----|
| Product Name | JadeStone |
| Team | 你的 Apple ID |
| Organization Identifier | com.yourname |
| Interface | SwiftUI |
| Language | Swift |
| Minimum Deployment | iOS 16.0 |

保存到任意目录。

### 2. 导入源码

将以下文件拖入 Xcode 项目 (勾选 "Copy items if needed"):

```
JadeStone/
├── JadeStoneApp.swift          → 替换模板生成的同名文件
├── ContentView.swift            → 替换同名文件
├── Info.plist                   → 拖入项目
├── Models/
│   └── AssessmentModels.swift   → 拖入 Models group
├── Services/
│   └── APIClient.swift          → 拖入 Services group
└── Views/
    └── ResultView.swift         → 拖入 Views group
```

### 3. 配置

在 Xcode 中:
1. 点击项目 → Targets → JadeStone → Signing & Capabilities
2. Team 选择你的 Apple ID
3. Bundle Identifier 改成唯一值 (如 `com.yourname.jadestone`)

### 4. 修改 API 地址

编辑 `Services/APIClient.swift` 第 8 行, 将 `baseURL` 改为你后端服务器的地址:

```swift
private let baseURL = "http://你的服务器IP:8000"
```

### 5. 连接 iPhone 运行

1. USB 连接 iPhone
2. Xcode 顶部选择你的 iPhone
3. 点击 ▶️ (Run)
4. 首次运行需要在 iPhone 上: 设置 → 通用 → VPN与设备管理 → 信任开发者

## 注意事项

- 后端服务器必须在同一局域网或公网可访问
- 拍照权限: 首次使用会弹出提示, 选择"允许"
- MVP 仅支持无开窗评估
- 至少拍 2 张照片才能开始评估
