---
name: "clean-architecture"
description: "Guides Clean Architecture design for Python projects: layering, dependency rules, directory structure, and anti-patterns. Invoke when designing project structure, refactoring to clean architecture, or checking dependency direction."
---

# Clean Architecture 技能

帮助你在 Python 项目中正确应用 Clean Architecture 原则，从目录结构到依赖规则，确保架构边界清晰。

## 触发条件

当用户提到以下场景时激活本技能：
- 设计新项目结构 / 重构现有项目结构
- 讨论 Clean Architecture / 六边形架构 / 洋葱架构
- 检查依赖方向是否正确
- 拆分"胖服务"或"上帝用例"
- 需要端口（Port）与适配器（Adapter）设计指导
- 询问业务逻辑与基础设施如何解耦

## 核心原则：依赖规则

> **源代码依赖只能指向更内层的圆。**

1. **内层不知道外层**：内层代码不能引用外层定义的类、函数、变量名
2. **数据格式隔离**：外层数据格式（JSON、SQL 结果）不应被内层使用
3. **接口定义在内层**：外层依赖内层定义的接口，而非相反

## 四层结构

```
┌─────────────────────────────────────────────┐
│  Frameworks & Drivers (最外层)              │
│  (UI, Database, Web, External Services)     │
├─────────────────────────────────────────────┤
│  Interface Adapters                         │
│  (Controllers, Presenters, Repositories)    │
├─────────────────────────────────────────────┤
│  Use Cases                                  │
│  (Application Business Rules)               │
├─────────────────────────────────────────────┤
│  Entities (最内层)                          │
│  (Enterprise Business Rules)                │
└─────────────────────────────────────────────┘
        所有依赖指向中心 →
```

| 层级 | 职责 | 允许依赖 | 禁止事项 |
|------|------|----------|----------|
| **Entities** | 企业级业务规则 | 无（最内层） | 依赖任何外层 |
| **Use Cases** | 应用级业务规则 | Entities | 直接访问 DB/外部服务 |
| **Interface Adapters** | 数据转换、控制器、展示器 | Use Cases, Entities | 包含核心业务逻辑 |
| **Frameworks & Drivers** | 框架、数据库、UI | 所有内层 | 定义业务规则 |

## 推荐目录结构

```
src/
├── __main__.py              # 启动入口
├── bootstrap/               # 组合根
│   ├── settings.py          # 配置定义
│   ├── runtime.py           # 配置加载
│   └── container.py         # 依赖组装
├── api/                     # 接口适配器层
│   ├── routes/              # HTTP 路由
│   ├── middleware/          # 中间件
│   └── schemas/             # DTO 定义
├── application/             # 应用层
│   ├── usecases/            # 用例实现
│   ├── commands/            # 命令对象
│   └── results/             # 结果对象
├── domain/                  # 领域层
│   ├── entities/            # 实体定义
│   ├── services/            # 领域服务
│   ├── ports/               # 端口定义
│   └── events/              # 领域事件
├── infra/                   # 基础设施层
│   ├── repositories/        # 仓储实现
│   ├── external/            # 外部服务封装
│   └── db/                  # 数据库配置
└── shared/                  # 共享工具
    └── utils/               # 纯工具函数
```

## 依赖倒置实现模式

```python
# 在内层定义接口（端口）
class UserRepositoryPort(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]: ...

# 外层实现接口（适配器）
class PostgresUserRepository(UserRepositoryPort):
    async def find_by_email(self, email: str) -> Optional[User]:
        # 具体实现
        ...

# 用例依赖抽象接口，不依赖具体实现
class LoginUseCase:
    def __init__(self, user_repo: UserRepositoryPort):
        self.user_repo = user_repo
```

## 组合根模式

```python
# bootstrap/container.py — 唯一知道具体实现的地方
def build_container(settings: Settings) -> Container:
    db = PostgresDB(settings.db_url)
    user_repo = PostgresUserRepository(db)
    token_generator = JWTTokenGenerator(settings.secret_key)

    login_usecase = LoginUseCase(
        user_repo=user_repo,
        token_generator=token_generator
    )

    return Container(login_usecase=login_usecase)
```

## 反模式对照表

| 反模式 | 症状 | 解决方案 |
|--------|------|----------|
| **Fat Service** | 服务类超 500 行，混合业务逻辑和 DB 操作 | 拆分为领域服务 + 仓储 |
| **God Use Case** | 一个用例处理多个不相关步骤 | 拆分为多个用例 |
| **Leaky Abstraction** | 领域层依赖外部 SDK 类型 | 定义自己的领域类型 |
| **Shared as Dumping Ground** | 共享层包含业务逻辑 | 移到对应的领域层 |
| **Infra in Domain Test** | 单元测试需要真实数据库 | Mock 端口实现 |

## 适用性判断

- **适用**：中大型业务系统、长期维护产品、需高可测试性、多团队协作
- **不适用**：小型 CRUD 应用（过度设计）、短期原型、团队经验不足

## 执行步骤

当用户请求架构设计或重构时，按以下步骤操作：

1. **判断适用性**：先确认项目规模和生命周期是否适合 Clean Architecture
2. **识别核心实体**：从业务需求中提炼 Entities
3. **定义端口接口**：在 domain/ports/ 中定义抽象接口
4. **实现用例**：在 application/usecases/ 中编排业务流程
5. **构建适配器**：在 api/ 和 infra/ 中实现具体适配
6. **组装依赖**：在 bootstrap/container.py 中完成组合根
7. **验证依赖方向**：确保没有外层被内层引用

## 自检规则

完成架构设计后，逐项检查：

- [ ] 内层代码是否引用了外层的类或模块？→ 必须修复
- [ ] Use Case 是否直接 import 了 infra 的模块？→ 必须通过端口解耦
- [ ] Entity 是否包含外部 SDK 的类型？→ 必须定义领域类型
- [ ] 组合根是否是唯一知道具体实现的地方？→ 必须集中
- [ ] 单元测试是否不需要真实数据库即可运行？→ 必须可 Mock
