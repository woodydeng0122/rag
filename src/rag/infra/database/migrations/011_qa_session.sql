-- 011: 问答会话与消息表

CREATE TABLE IF NOT EXISTS qa_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    title VARCHAR(512) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS qa_message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES qa_session(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,  -- 'user' | 'assistant'
    content TEXT NOT NULL DEFAULT '',
    chunks JSONB NOT NULL DEFAULT '[]',  -- 引用的检索结果
    latency_ms INT DEFAULT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_qa_session_project_id ON qa_session(project_id);
CREATE INDEX IF NOT EXISTS idx_qa_session_updated_at ON qa_session(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_qa_message_session_id ON qa_message(session_id);
