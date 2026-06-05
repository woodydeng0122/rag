---
name: design-principles
description: >
  软件设计原则参考指南，适用于 Python 项目代码审查、模块设计、接口设计、重构决策。
  当用户讨论模块暴露、依赖关系、类设计、接口抽象、代码耦合等问题时触发。
---

# 软件设计原则

## 原则层次结构

```
设计原则  （Why：为什么这样设计）
    ↓
设计模式  （What：具体解决方案）
    ↓
代码实现  （How：怎么写）
```

***

## SOLID 原则

### S — 单一职责原则 SRP

> 一个模块只负责一件事，只有一个理由被修改。

```python
# ❌ 违反：一个类既生成内容又保存数据库
class SummaryService:
    def generate(self, content): ...
    def save_to_db(self, summary): ...

# ✅ 遵守：拆分职责
class SummaryGenerator:
    def generate(self, content): ...

class SummaryRepository:
    def save(self, summary): ...
```

**触发信号**：一个文件/类改动的原因超过一个。

***

### O — 开闭原则 OCP

> 对扩展开放，对修改关闭。新增功能不应该修改已有代码。

```python
# ❌ 违反：每加一种类型就改 if-else
def generate(type: str):
    if type == "summary": ...
    elif type == "outline": ...   # 每次都要改这里

# ✅ 遵守：注册表模式，新增不修改旧代码
registry.register("summary", SummaryGenerator())
registry.register("outline", OutlineGenerator())  # 只加这一行

gen = registry.get(type)
gen.generate(context)
```

**触发信号**：加新功能时需要修改核心逻辑文件。

***

### L — 里氏替换原则 LSP

> 子类必须能替换父类，且行为一致。

```python
# ❌ 违反：子类改变了父类的行为契约
class BaseGenerator:
    def generate(self, context) -> str: ...

class ExamGenerator(BaseGenerator):
    def generate(self, context) -> list:  # 返回类型变了！
        ...

# ✅ 遵守：子类保持相同契约
class ExamGenerator(BaseGenerator):
    def generate(self, context) -> str:   # 返回相同类型
        ...
```

**触发信号**：子类覆盖父类方法时改变了参数类型或返回类型。

***

### I — 接口隔离原则 ISP

> 不应强迫实现者依赖它不需要的方法。拆小接口，不要一个大而全的接口。

```python
# ❌ 违反：实现类被迫实现不需要的方法
class IGenerator:
    def generate(self): ...
    def stream_generate(self): ...   # 不是所有生成器都需要流式
    def cache(self): ...             # 不是所有生成器都需要缓存

# ✅ 遵守：拆分小接口
class IGenerator:
    def generate(self): ...

class IStreamable:
    def stream_generate(self): ...

class SummaryGenerator(IGenerator, IStreamable): ...  # 按需组合
class SimpleGenerator(IGenerator): ...               # 只需要基本接口
```

**触发信号**：实现类里出现 `raise NotImplementedError` 或空方法。

***

### D — 依赖倒置原则 DIP

> 高层模块不依赖低层模块，两者都依赖抽象。

```python
# ❌ 违反：高层直接依赖具体实现
class SummaryService:
    def __init__(self):
        self.llm = ChatOpenAI(...)   # 直接依赖具体类

# ✅ 遵守：依赖抽象，外部注入
class SummaryService:
    def __init__(self, llm: BaseChatModel):  # 依赖抽象
        self.llm = llm

# 调用方决定用哪个实现
service = SummaryService(llm=ChatOpenAI(...))
service = SummaryService(llm=MockLLM(...))    # 测试时注入 mock
```

**触发信号**：类内部 `import` 并直接实例化具体依赖。

***

## 其他重要原则

### 最少知识原则 LoD（迪米特法则）

> 一个模块只和它直接需要的东西打交道，不了解内部实现细节。

```python
# ❌ 违反：调用方知道太多内部结构
from llm.generators import SummaryGenerator, BaseGenerator, GeneratorRegistry
gen = SummaryGenerator()

# ✅ 遵守：调用方只知道最少接口
from llm.generators import registry, GenerationContext
gen = registry.get("summary")
```

**在** **`__init__.py`** **中的体现**：只暴露调用方"需要知道的"，其余是实现细节。

| 暴露                    | 不暴露                     |
| --------------------- | ----------------------- |
| 对外数据类（Context、Result） | 基类（BaseGenerator）       |
| 统一入口（registry）        | 具体实现类（SummaryGenerator） |
| 类型注解需要的类              | 内部工具函数                  |

***

### DRY — 不要重复自己

> 同一逻辑只在一个地方存在，修改时只改一处。

```python
# ❌ 违反：每个 Generator 都重复写参数校验
class SummaryGenerator:
    def generate(self, context):
        if not context.content: raise ValueError(...)

class OutlineGenerator:
    def generate(self, context):
        if not context.content: raise ValueError(...)  # 重复！

# ✅ 遵守：提到基类
class BaseGenerator:
    def generate(self, context):
        self._validate(context)          # 统一校验
        return self._do_generate(context)

    def _validate(self, context): ...    # 只写一次
    def _do_generate(self, context): ... # 子类实现
```

***

### YAGNI — 你不会需要它

> 不要提前设计"将来可能用到"的功能，只实现当前需要的。

```python
# ❌ 违反：过度设计
class LLMClient:
    def generate(self): ...
    def generate_with_retry(self): ...      # 现在用不到
    def generate_with_fallback(self): ...   # 现在用不到
    def generate_distributed(self): ...     # 现在用不到

# ✅ 遵守：只实现当前需要的
class LLMClient:
    def generate(self): ...
    def stream_generate(self): ...
```

***

## 原则 vs 模式 对照表

| 原则       | 对应的常见设计模式       |
| -------- | --------------- |
| OCP 开闭原则 | 注册表模式、策略模式、工厂模式 |
| DIP 依赖倒置 | 依赖注入、抽象工厂       |
| SRP 单一职责 | 门面模式、命令模式       |
| LoD 最少知识 | 门面模式、中介者模式      |
| LSP 里氏替换 | 模板方法模式          |

***

## 代码审查自检

审查代码时逐项检查：

```
□ 这个文件/类只做一件事吗？                    → SRP
□ 加新功能需要修改已有代码吗？                  → OCP
□ __init__.py 暴露了内部实现细节吗？            → LoD
□ 类内部直接 new 了具体依赖？                   → DIP
□ 有重复逻辑可以提取吗？                        → DRY
□ 有"以后可能用到"的代码吗？                    → YAGNI
□ 子类改变了父类的返回类型或行为契约？           → LSP
□ 接口方法是否有被迫空实现或 NotImplemented？   → ISP
```

***

## 本项目（ai-reading-ai）实践案例

| 代码位置                                  | 用到的原则     | 说明                          |
| ------------------------------------- | --------- | --------------------------- |
| `llm/generators/__init__.py` 精简暴露     | LoD       | 只暴露 registry、Context、Result |
| `registry.get("summary")` 替代直接 import | OCP + DIP | 扩展不修改调用方                    |
| `BaseGenerator._validate()`           | SRP + DRY | 校验逻辑集中在基类                   |
| `get_llm()` 接收 api\_key 参数            | DIP       | 不在内部硬编码，外部注入                |
| `OtelCallbackHandler` 独立文件            | SRP       | 监控逻辑不混入业务逻辑                 |

