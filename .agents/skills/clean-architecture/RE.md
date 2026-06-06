用分层来归位：

```
┌─────────────────────────────────────────────┐
│              Application 层                  │
│                                             │
│   ApplicationService / Use Case             │
│   · 流程编排                                 │
│   · 调用 Repository、Domain Service         │
│   · 发布领域事件                             │
└─────────────────┬───────────────────────────┘
                  │ 依赖
┌─────────────────▼───────────────────────────┐
│                Domain 层                     │
│                                             │
│   Entity          Value Object              │
│   · 有 id         · 无 id，不可变            │
│   · User          · Money, Address          │
│                                             │
│   Aggregate Root（聚合根）                   │
│   · 聚合的唯一入口                           │
│   · 收集领域事件                             │
│                                             │
│   Domain Service                            │
│   · 跨 Entity 的业务规则                    │
│   · 不知道 Repository                       │
│                                             │
│   Port（接口）                               │
│   · IRepository                             │
│   · IEmailService                           │
└─────────────────────────────────────────────┘
                  ▲ 实现
┌─────────────────┴───────────────────────────┐
│             Infrastructure 层                │
│                                             │
│   Adapter（Port 的具体实现）                 │
│   · RepositoryImpl → DB                     │
│   · SendGridEmailService → SendGrid         │
└─────────────────────────────────────────────┘
```

**依赖方向**：Application → Domain ← Infrastructure

Domain 层是核心，不依赖任何人，所有人依赖它。
