## ADDED Requirements

### Requirement: Document management page
系统 SHALL 在 rag-web 前端提供文档管理页面，包含项目选择、文件上传、文档列表和处理操作。

#### Scenario: Access document management page
- **WHEN** 用户导航到文档管理页面
- **THEN** 页面显示项目列表，可选择或创建项目

### Requirement: File upload component
系统 SHALL 提供文件上传组件，支持拖拽上传单文件或 zip。

#### Scenario: Upload file via drag and drop
- **WHEN** 用户拖拽一个 `.pdf` 文件到上传区域
- **THEN** 文件上传到当前选中的项目，上传成功后文档列表刷新

#### Scenario: Upload zip file
- **WHEN** 用户上传一个 zip 文件
- **THEN** zip 解压后每个支持的文件在列表中显示为独立文档

#### Scenario: Upload rejected for unsupported type
- **WHEN** 用户尝试上传 `.xlsx` 文件
- **THEN** 上传组件提示不支持的文件类型，仅接受 `.md`、`.txt`、`.pdf`、`.zip`

### Requirement: Document list display
系统 SHALL 显示当前项目下的所有文档，包含文件名、类型、大小、状态、创建时间。

#### Scenario: View document list
- **WHEN** 用户选择一个项目
- **THEN** 列表显示该项目下所有文档的 filename、file_type、file_size、status、created_at

#### Scenario: Status displayed with visual indicator
- **WHEN** 文档处于不同状态
- **THEN** uploaded 显示灰色、processing（chunking/embedding）显示蓝色动画、ready 显示绿色、error 显示红色

### Requirement: Process button
系统 SHALL 为每个 status 为 `uploaded` 的文档提供"处理"按钮。

#### Scenario: Click process button
- **WHEN** 用户点击文档的"处理"按钮
- **THEN** 系统调用 `POST /api/documents/{id}/process`，按钮变为 loading 状态，文档状态实时更新

#### Scenario: Process button disabled for non-uploaded documents
- **WHEN** 文档 status 为 `ready` 或 `error`
- **THEN** "处理"按钮不可点击（error 状态可显示"重试"按钮）

### Requirement: Project creation dialog
系统 SHALL 提供创建项目的对话框。

#### Scenario: Create project
- **WHEN** 用户点击"新建项目"按钮并填写名称和描述
- **THEN** 系统调用 `POST /api/projects` 创建项目，项目列表刷新
