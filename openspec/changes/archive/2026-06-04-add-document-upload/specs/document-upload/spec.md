## ADDED Requirements

### Requirement: Upload single file
系统 SHALL 提供上传单个文件的 API 端点，仅接受 `.md`、`.txt`、`.pdf` 格式。

#### Scenario: Upload a valid single file
- **WHEN** 用户通过 `POST /api/projects/{project_id}/documents` 上传一个 `.pdf` 文件
- **THEN** 系统将文件保存到 `docs/{upload_id}/` 目录，并在 document 表中创建一条记录，status 为 `uploaded`

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

### Requirement: File integrity check
系统 SHALL 对上传的文件计算 SHA256 校验和，存储到 document 表的 checksum 字段。

#### Scenario: File checksum stored
- **WHEN** 用户上传一个文件
- **THEN** 系统计算文件 SHA256 并存入 document.checksum 字段

### Requirement: File metadata stored
系统 SHALL 将文件的原始文件名、相对路径、文件大小、文件类型存入 document 表。

#### Scenario: Metadata recorded on upload
- **WHEN** 用户上传文件 `report.pdf`（大小 1024 bytes）
- **THEN** document 记录的 filename 为 `report.pdf`，file_size 为 1024，file_type 为 `pdf`，file_path 为 `docs/{upload_id}/report.pdf`
