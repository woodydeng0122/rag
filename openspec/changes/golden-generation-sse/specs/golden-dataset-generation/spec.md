## MODIFIED Requirements

### Requirement: GenerationTask entity
GenerationTask 实体 SHALL 包含 `paused` 和 `cancelled` 状态。

原定义:
```python
status: str = "running"  # running / completed / failed
```

修改为:
```python
status: str = "running"  # running / paused / cancelled / completed / failed
```

#### Scenario: 任务暂停
- **WHEN** 用户暂停运行中的任务
- **THEN** 任务 status 变为 paused

#### Scenario: 任务取消
- **WHEN** 用户取消运行中或暂停的任务
- **THEN** 任务 status 变为 cancelled

### Requirement: GenerateGoldenUseCase
GenerateGoldenUseCase SHALL 重构为事件驱动的 GenerationTaskRunner，通过异步生成器 yield 事件字典，支持流式 LLM 调用和暂停/取消控制。

原流程:
```
asyncio.create_task(self._run_generation(...))
```

修改为:
```
runner = GenerationTaskRunner(llm, golden_repo, chunk_repo, task_repo)
task_manager.register(task.id, runner)
asyncio.create_task(runner.run(...))
```

Runner.run() 为异步生成器，每步 yield 事件字典:
```python
async def run(self, ...) -> AsyncGenerator[dict, None]:
    yield {"type": "progress", "completed": 0, "total": N, "failed": 0}
    ...
    yield {"type": "phase_start", "phase": "question_gen", ...}
    async for token in self.llm.astream(prompt):
        yield {"type": "llm_token", "content": token}
    ...
```

#### Scenario: Runner 生成事件
- **WHEN** Runner 执行生成流程
- **THEN** 每步 yield 包含 type 字段的事件字典

#### Scenario: Runner 暂停检查
- **WHEN** 一条问题处理完毕
- **THEN** Runner 检查 pause_event，若被 clear 则 await wait() 阻塞

#### Scenario: Runner 取消检查
- **WHEN** 一条问题处理完毕
- **THEN** Runner 检查 cancel_flag，若被 set 则退出循环并 yield task_cancelled 事件

## ADDED Requirements

### Requirement: Failed items tracking
GenerationTaskRunner SHALL 记录失败项的上下文信息（prompt、chunk 信息），以支持重试。

#### Scenario: 记录失败项
- **WHEN** 一条问题处理失败
- **THEN** 将失败项的 prompt、chunk_ids 等上下文保存到 Runner 的 failed_items 列表

#### Scenario: 重试失败项
- **WHEN** 调用 retry_failed 方法
- **THEN** 遍历 failed_items，重新调用 LLM 处理，yield 事件
