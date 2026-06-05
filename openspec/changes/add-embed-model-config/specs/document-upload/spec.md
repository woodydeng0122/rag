## MODIFIED Requirements

### Requirement: Upload single file
系统 SHALL 提供上传单个文件的 API 端点，仅接受 `.md`、`.txt`、`.pdf` 格式。上传时不再传递 embedder_model 参数，模型信息从项目继承。

#### Scenario: Upload a valid single file
- **WHEN** 用户通过 `POST /api/projects/{project_id}/documents` 上传一个 `.pdf` 文件
- **THEN** 系统将文件保存到 `docs/{upload_id}/` 目录，并在 document 表中创建一条记录，status 为 `uploaded`，不包含 embedder_model 字段

#### Scenario: Upload unsupported file type
- **WHEN** 用户上传一个 `.docx` 文件
- **THEN** 系统返回 400 错误，提示不支持的文件类型

### Requirement: Upload zip file
系统 SHALL 支持上传 zip 文件，自动解压到 `docs/{upload_id}/` 目录并保持目录结构。

#### Scenario: Upload a valid zip containing multiple files
- **WHEN** 用户上传一个 zip 文件，内含 `dir/a.md`、`b.txt`、`c.pdf`
- **THEN** 系统解压到 `docs/{upload_id}/dir/a.md`、`docs/{upload_id}/b.txt`、`docs/{upload_id}/c.pdf`，每个文件在 document 表中创建独立记录，status 均为 `uploaded`

#### Scenario: Upload zip with unsupported file types mixed in
- **WHEN** 用户上传的 zip 内含 `.md` 和 `.xlsx` 文件
- **THEN** 系统仅处理 `.md`、`.txt`、`.pdf` 文件，跳过不支持的文件类型，跳过的文件不创建 document 记录

## REMOVED Requirements

### Requirement: Upload with embedder_model parameter
**Reason**: 嵌入模型从项目继承，不再由上传时指定
**Migration**: 上传接口移除 `embedder_model` Form 参数，模型信息通过 `project.embed_model_id` 获取
