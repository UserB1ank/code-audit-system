# Rust 漏洞指南

Rust 应用程序中常见的安全漏洞类型，包含对应的危险模式、审计方法和实际案例。

## 如何使用

审计 Rust 代码时查阅本指南。将发现的漏洞与这些模式进行匹配，追踪 Source → Sink 链。

## 核心认知：Rust 安全性的真实边界

Rust 最大的安全承诺是真实的：在 safe Rust 代码中，可以避免 C/C++ 中仍占主导地位的大量内存错误类型。但"内存安全"不等于"安全"。实战经验表明，Rust 代码中最值得关注的漏洞发生在四个层面：

1. **Unsafe 契约** — 某些不变量在代码演化中悄悄漂移，最终进入未定义行为
2. **边界代码** — 接受攻击者可控输入的解析层（反序列化、协议解析）
3. **并发路径** — 在负载下死锁或饥饿的异步并发路径
4. **供应链/打包缺口** — 审计的代码与最终发布的代码不一致

**最关键的理念**：审计 unsafe 代码不是检查"有没有 unsafe 块"，而是验证"unsafe 块中声称的那些不变量在运行时是否真的成立"。如 `std::slice::from_raw_parts` 的安全契约要求指针非空、正确对齐、指针覆盖的字节范围有效，违反任何一项都是未定义行为。

---

## 审计工具链

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| `cargo-audit` | 依赖已知漏洞扫描 | `cargo install cargo-audit` |
| `cargo-geiger` | 统计 unsafe 代码位置 | `cargo install cargo-geiger` |
| `cargo-fuzz` | 模糊测试 | `cargo install cargo-fuzz` |
| `cargo-scan` | 副作用分析 | `cargo +nightly scan`（需 nightly Rust） |
| `cargo-tarpaulin` | 覆盖率分析 | `cargo install cargo-tarpaulin` |
| `cargo-bloat` | 二进制膨胀分析 | `cargo install cargo-bloat` |
| `Miri` | 检测 UB（解释执行） | `rustup component add miri` |
| `Clippy` | 静态 lint | 随 Rust 工具链自带 |
| `Siderophile` | unsafe 危险系数排序 | 按 GitHub 说明安装 |

### 审计环境快速配置

```bash
# 获取项目源码并检查工具链版本
rustup show
cargo --version

# 启用最高编译器警告级别
export RUSTFLAGS="-W warnings -D warnings"

# 首轮快速扫描
cargo audit
cargo clippy -- -W clippy::pedantic -W clippy::nursery
cargo geiger
```

---

## 1. Unsoundness（健全性漏洞）

**严重程度**: 严重 (CVSS 7.0–10.0) | **可利用**: 是

Unsafe Rust 的核心风险在于：它在 safe 代码中暴露了不安全 API。如果安全函数的签名允许 safe 代码触发 undefined behavior（UB），就违反了 Rust 的安全保证。

### 类型一：API 暴露 unsafe 操作

**场景**：`capnp` crate 中 `Reader::get` 和 `StructSchema::new` 两个 safe API 内部调用了 `PointerReader::get_root_unchecked`，允许 safe 代码构造任意结构。

**常见模块**：序列化库（serde、protobuf、capnp）、任何封装了底层指针运算的 safe API。

#### 危险 API/模式

| API / 模式 | 风险 | 说明 |
|------------|------|------|
| safe 函数内部调用 `unsafe` 且未充分验证 | 🔴 严重 | 违反安全封装 |
| `from_raw_parts` / `from_raw_parts_mut` | 🔴 严重 | 指针有效性由调用者保证 |
| `std::ptr::read` / `std::ptr::write` | 🔴 严重 | 需确保有效对齐和非空 |
| `transmute` | 🔴 严重 | 类型 reinterpret，极易引发 UB |
| `std::mem::zeroed()` / `std::mem::uninitialized()` | 🟡 中等 | 零值/未初始化值可能违反类型不变量 |

#### 漏洞代码示例

```rust
// 漏洞：safe API 暴露 unsafe 行为
pub fn get_root_unchecked<T>(data: &[u8]) -> T {
    // safe 函数内部做 unsafe 操作但未充分验证
    unsafe {
        let ptr = data.as_ptr() as *const T;
        std::ptr::read(ptr)  // 如果 data 长度不足或对齐不对 → UB
    }
}

// 安全：显式标记 unsafe 并文档化不变量
/// # Safety
/// - data 长度必须 >= size_of::<T>()
/// - data 起始地址必须对齐 align_of::<T>()
pub unsafe fn get_root<T>(data: &[u8]) -> T {
    let ptr = data.as_ptr() as *const T;
    std::ptr::read(ptr)
}
```

#### 审计检查清单

- [ ] 搜索所有 `unsafe` 块，确认被 `unsafe fn` 或 `unsafe {}` 正确包裹
- [ ] 检查 safe 函数是否内部调用了 unsafe 操作且未充分验证
- [ ] 检查 API 文档是否清晰说明了安全不变量
- [ ] 使用 `cargo-geiger` 统计 unsafe 块分布，优先审查高频区域

---

### 类型二：型变（Variance）问题

**场景**：自定义 `MyCell<T>` 结构未正确处理型变（variance），导致 `set_cell` 中的局部变量被存入，函数返回后被释放，形成 use-after-free。

**常见模块**：自定义容器类型、智能指针构造。

#### 危险模式

| 模式 | 风险 | 说明 |
|------|------|------|
| 自定义容器未正确标注生命周期参数 | 🔴 严重 | 可能导致悬垂引用 |
| `Cell<T>` / `RefCell<T>` 自定义变体 | 🔴 严重 | 型变错误 → UAF |
| `PhantomData` 使用不当 | 🟡 中等 | 影响型变和 drop 检查 |

#### 漏洞代码示例

```rust
// 漏洞：MyCell 对 T 是 covariant，但允许写入
// 编译器认为短生命周期可以替换长生命周期 → UAF
struct MyCell<T> {
    value: UnsafeCell<T>,
}

impl<T> MyCell<T> {
    fn set(&self, val: T) {
        unsafe {
            *self.value.get() = val;  // 如果 T 的生命周期比预期短 → UAF
        }
    }
}

// 安全：使用 std::Cell<T>（对 T invariant）或 PhantomData 正确标注
struct SafeCell<T> {
    value: UnsafeCell<T>,
    _marker: PhantomData<fn(T) -> T>,  // 确保对 T invariant
}
```

#### 审计检查清单

- [ ] 审查涉及生命周期参数的自定义数据结构
- [ ] 检查 `UnsafeCell` / `Cell` 自定义实现是否正确处理型变
- [ ] 使用 Miri 检测运行期 UB：`cargo +nightly miri test`

---

### 类型三：并发 trait 的误实现

**场景**：crate 为包含 `!Send` 类型的数据无条件实现 `Send`/`Sync` trait，绕过 Rust 的线程安全保证。

**常见模块**：自定义容器、并发数据结构。

#### 危险 API/模式

| 模式 | 风险 | 说明 |
|------|------|------|
| `unsafe impl Send for T` | 🔴 严重 | 绕过线程安全检查 |
| `unsafe impl Sync for T` | 🔴 严重 | 允许跨线程共享不可变引用 |
| 为含 `Rc<T>` / `RefCell<T>` 的类型 impl Send | 🔴 严重 | 这些类型有意 !Send |

#### 漏洞代码示例

```rust
// 漏洞：无条件 impl Send，内部含 !Send 类型
struct SharedData {
    handle: Rc<RefCell<Vec<String>>>,  // Rc<T> 是 !Send
}

unsafe impl Send for SharedData {}  // 危险！允许跨线程传输

// 安全：使用 Arc 代替 Rc，自动实现 Send
struct SafeSharedData {
    handle: Arc<Mutex<Vec<String>>>,
}
// Arc<Mutex<T>> 自动 impl Send + Sync
```

#### 审计检查清单

- [ ] 搜索所有 `unsafe impl Send` 和 `unsafe impl Sync`
- [ ] 验证实现中每个字段是否真正线程安全
- [ ] 检查是否有 `Rc<T>`、`RefCell<T>` 等有意 !Send 的类型被"强制" Send

---

### 类型四：内联汇编约束错误

**场景**：`keccak` crate 的 ARMv8 汇编优化中，开发者使用 `asm!` 的 `in` 约束（只读）来描述被汇编代码实际修改的寄存器，导致编译器进行错误优化。

**参考 CVE**：GHSA-3288-…（keccak-asm）

#### 危险模式

| 模式 | 风险 | 说明 |
|------|------|------|
| `asm!` 的 `in` 约束用于实际被修改的寄存器 | 🔴 严重 | 编译器错误优化 |
| `asm!` 的 `out` / `inout` 约束遗漏 | 🔴 严重 | 寄存器 clobber 未声明 |
| `global_asm!` 中的符号引用错误 | 🟡 中等 | 链接期问题 |

#### 漏洞代码示例

```rust
// 漏洞：寄存器 q0 被汇编代码修改，但只声明为 in
unsafe {
    asm!(
        "eor v0.16b, v0.16b, v1.16b",  // 修改了 v0
        in("v0") a,   // 错误！应该是 inout
        in("v1") b,
    );
}

// 安全：正确标注 inout
unsafe {
    asm!(
        "eor v0.16b, v0.16b, v1.16b",
        inout("v0") a => a,  // 正确：声明了读取和写入
        in("v1") b,
    );
}
```

#### 审计检查清单

- [ ] 搜索所有 `asm!` 和 `global_asm!` 块
- [ ] 交叉比对约束声明与实际寄存器使用行为
- [ ] 特别关注 `in` 约束的寄存器是否被汇编代码实际修改

---

## 2. 逻辑漏洞

**严重程度**: 高 (CVSS 6.0–9.0) | **可利用**: 是

无论语言多安全，业务逻辑错误仍会导致漏洞。

### 典型场景

**场景**：RustFS 中通知端点仅验证身份未验证管理员权限，普通用户可以覆盖全局配置。

**参考 CVE**：CVE-2026-40937（RustFS）

**常见模块**：权限检查函数、认证中间件、Web 框架的中间件。

#### 危险模式

| 模式 | 风险 | 说明 |
|------|------|------|
| 多个权限检查函数存在细微差异 | 🔴 严重 | 开发者选错函数 → 绕过 |
| 公共端点遗漏权限检查 | 🔴 严重 | 直接访问受限资源 |
| 中间件跳过特定路由 | 🟡 中等 | 认证旁路 |

#### 漏洞代码示例

```rust
// 漏洞：admin_only 仅检查登录状态，未验证管理员角色
fn admin_only(user: &User) -> bool {
    user.is_authenticated()  // 只验证了登录，未验证角色
}

fn delete_config(req: &Request) -> Response {
    let user = get_user(req);
    if !admin_only(&user) {
        return Response::forbidden();
    }
    // 普通用户也能到达这里
    delete_global_config();
    Response::ok()
}

// 安全：同时验证身份和角色
fn admin_only(user: &User) -> bool {
    user.is_authenticated() && user.role() == Role::Admin
}
```

#### 审计检查清单

- [ ] 审查每一个需要权限的端点，确认调用了完整的权限验证函数
- [ ] 对比权限检查函数之间的差异（细微差异最危险）
- [ ] 检查中间件配置是否覆盖了所有需要保护的路由

---

## 3. 并发与竞态条件

**严重程度**: 高 (CVSS 6.0–9.0) | **可利用**: 视场景

### 典型场景

**场景**：Linux 内核 Binder 驱动中，多个线程并发访问"死亡通知列表"时未正确加锁，造成竞态条件后链表结构被破坏，导致内核崩溃。

**参考 CVE**：CVE-2025-68260（Linux Binder）

**常见模块**：跨线程共享的可变数据结构、`Arc<Mutex<T>>` 使用不当、锁粒度过大或过小。

#### 危险 API/模式

| 模式 | 风险 | 说明 |
|------|------|------|
| 共享可变状态无锁保护 | 🔴 严重 | 数据竞争 |
| 多个锁获取顺序不一致 | 🔴 严重 | 死锁风险 |
| `Arc<Mutex<T>>` 持有时间过长 | 🟡 中等 | 性能瓶颈 / 死锁 |
| 异步代码中无界任务生成 | 🟡 中等 | 资源耗尽 |

#### 漏洞代码示例

```rust
// 漏洞：多个线程无锁访问共享列表
static mut DEATH_NOTIFICATIONS: Vec<*mut Node> = Vec::new();

fn add_notification(node: *mut Node) {
    unsafe {
        DEATH_NOTIFICATIONS.push(node);  // 多线程并发 push → 数据竞争
    }
}

// 安全：使用 Mutex 保护
lazy_static! {
    static ref DEATH_NOTIFICATIONS: Mutex<Vec<*mut Node>> = Mutex::new(Vec::new());
}

fn add_notification(node: *mut Node) {
    DEATH_NOTIFICATIONS.lock().unwrap().push(node);
}
```

#### 审计检查清单

- [ ] 标注所有跨线程共享的可变状态
- [ ] 检查 `unsafe impl Send` / `unsafe impl Sync` 的安全性
- [ ] 审查锁的获取顺序，避免潜在死锁
- [ ] 使用 `loom` 测试并发边缘条件
- [ ] 使用 `ThreadSanitizer`（TSAN）运行时检测：`RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test`

---

## 4. 资源耗尽（OOM / DoS）

**严重程度**: 中高 (CVSS 5.0–8.0) | **可利用**: 是

### 典型场景

**场景 1**：Salvo Web 框架在处理 multipart form 时无大小限制，攻击者发送超大数据包导致 OOM 崩溃。

**参考 CVE**：CVE-2026-33241（Salvo）

**场景 2**：async-tar 解析错误导致提取嵌套 tar 夹带额外文件，触发供应链攻击。

**参考 CVE**：CVE-2025-62518（async-tar）

**常见模块**：文件/网络解析器、压缩库、反序列化器。

#### 危险 API/模式

| 模式 | 风险 | 说明 |
|------|------|------|
| 解析器无 payload 大小限制 | 🔴 严重 | OOM DoS |
| `Vec::with_capacity(user_input)` | 🔴 严重 | 攻击者控制分配大小 |
| 递归解压无深度限制 | 🔴 严重 | zip bomb / tar bomb |
| 异步任务无背压机制 | 🟡 中等 | 任务爆炸 |

#### 漏洞代码示例

```rust
// 漏洞：无大小限制的 multipart 解析
async fn handle_upload(req: &mut Request) -> Vec<u8> {
    let mut buf = Vec::new();
    req.body().read_to_end(&mut buf).await.unwrap();  // 无限制读取 → OOM
    buf
}

// 安全：限制 payload 大小
async fn handle_upload(req: &mut Request) -> Result<Vec<u8>, Error> {
    let max_size = 10 * 1024 * 1024;  // 10MB
    let mut buf = Vec::with_capacity(max_size);
    let mut limited = req.body().take(max_size as u64);
    limited.read_to_end(&mut buf).await?;
    if buf.len() as u64 == max_size as u64 {
        return Err(Error::PayloadTooLarge);
    }
    Ok(buf)
}
```

#### 审计检查清单

- [ ] 检查所有解析函数是否有大小限制
- [ ] 搜索 `Vec::with_capacity` / `String::with_capacity` 参数来源
- [ ] 审查递归解压的深度限制
- [ ] 检查异步循环中的任务生成逻辑和背压机制
- [ ] 使用 `cargo-fuzz` 对解析代码进行对抗性测试

---

## 5. 整数与缓冲区漏洞

**严重程度**: 中高 (CVSS 5.0–8.0) | **可利用**: 是

即使在 safe Rust 中，panic 安全性缺陷仍可能导致 UB（特别是迭代器优化中）。

### 典型场景

**场景**：标准库 `Zip` 迭代器在特定条件下多次调用 `__iterator_get_unchecked()`，违反 `TrustedRandomAccess` 的安全要求，导致内存安全问题。

**参考 CVE**：CVE-2021-28876 等（std::zip）

**常见模块**：迭代器实现（特别是 `TrustedRandomAccess` 优化）、unsafe 块中的指针算术。

#### 危险 API/模式

| 模式 | 风险 | 说明 |
|------|------|------|
| `TrustedRandomAccess` 实现不当 | 🔴 严重 | 可能导致 OOB |
| `get_unchecked()` / `get_unchecked_mut()` | 🔴 严重 | 跳过边界检查 |
| `unwrap()` / `expect()` 在不可恢复路径 | 🟡 中等 | panic → 潜在 UB |
| `vector[user_input]` 动态索引 | 🟡 中等 | 未做边界检查 |

#### 漏洞代码示例

```rust
// 漏洞：get_unchecked 跳过边界检查
fn get_element(v: &Vec<u8>, idx: usize) -> u8 {
    unsafe {
        *v.get_unchecked(idx)  // 如果 idx >= v.len() → UB
    }
}

// 漏洞：unwrap 在用户输入路径上
fn parse_length(data: &[u8]) -> usize {
    let len = data.get(0..4).unwrap();  // 畸形输入 → panic
    u32::from_be_bytes(len.try_into().unwrap()) as usize
}

// 安全：显式边界检查
fn get_element(v: &Vec<u8>, idx: usize) -> Option<u8> {
    if idx < v.len() {
        Some(v[idx])
    } else {
        None
    }
}

fn parse_length(data: &[u8]) -> Option<usize> {
    let len = data.get(0..4)?;
    Some(u32::from_be_bytes(len.try_into().ok()?) as usize)
}
```

#### 审计检查清单

- [ ] 搜索 `get_unchecked` / `get_unchecked_mut`，确认前置条件
- [ ] 搜索 `unwrap()` / `expect()`，评估 panic 安全性影响
- [ ] 审查自定义迭代器实现中的 `TrustedRandomAccess`
- [ ] 使用 `clippy::arithmetic_side_effects` 检测潜在整数溢出

---

## 6. 标准库 unsafe API 误用

**严重程度**: 严重 (CVSS 7.0–10.0) | **可利用**: 是

### 典型场景

**场景 1**：`std::slice::from_raw_parts` 从 `u8` 指针（align=1）转换为 `u64` 指针（align=8）导致不对齐访问 UB。

**场景 2**：标准库 `Path` API 在 Cygwin target 上对路径分隔符处理不当造成路径遍历。

**参考 CVE**：CVE-2025-11233（std::Path）

#### 危险 API/模式

| API | 风险 | 说明 |
|-----|------|------|
| `std::slice::from_raw_parts` | 🔴 严重 | 需确保非空、对齐、有效 |
| `std::slice::from_raw_parts_mut` | 🔴 严重 | 同上 + 独占访问 |
| `std::ptr::copy_nonoverlapping` | 🟡 中等 | 需确保有效内存范围 |
| `std::mem::transmute` | 🔴 严重 | 类型重解释极易出错 |
| `std::str::from_utf8_unchecked` | 🟡 中等 | 非 UTF-8 数据 → UB |

#### 漏洞代码示例

```rust
// 漏洞：u8 指针（align=1）转 u64（align=8）→ 不对齐 UB
fn read_u64(data: &[u8]) -> u64 {
    unsafe {
        let ptr = data.as_ptr() as *const u64;
        std::ptr::read(ptr)  // 如果 data 地址不是 8 字节对齐 → UB
    }
}

// 安全：使用对齐读取
fn read_u64(data: &[u8]) -> u64 {
    let mut buf = [0u8; 8];
    buf.copy_from_slice(&data[0..8]);
    u64::from_ne_bytes(buf)
}

// 漏洞：Cygwin 路径分隔符处理
fn serve_file(base: &Path, user_path: &str) -> std::io::Result<File> {
    let path = base.join(user_path);  // Cygwin 上可能被 .. 绕过
    File::open(path)
}

// 安全：验证规范化后的路径仍在 base 下
fn serve_file(base: &Path, user_path: &str) -> std::io::Result<File> {
    let path = base.join(user_path);
    let canonical = path.canonicalize()?;
    let base_canonical = base.canonicalize()?;
    if !canonical.starts_with(&base_canonical) {
        return Err(std::io::Error::new(std::io::ErrorKind::PermissionDenied, "path traversal"));
    }
    File::open(canonical)
}
```

#### 审计检查清单

- [ ] 搜索 `from_raw_parts` / `from_raw_parts_mut`，检查非空、对齐、有效范围
- [ ] 搜索 `transmute`，检查类型大小和对齐是否匹配
- [ ] 审查平台特定路径处理逻辑，测试路径遍历 payload
- [ ] 使用 Miri 检测对齐和有效性问题：`cargo +nightly miri test`

---

## 7. 依赖供应链漏洞

**严重程度**: 视场景 | **可利用**: 是

Rust 依赖生态（crates.io）是安全的关键环节。第三方依赖构成代码库的重要组成部分，同时引入潜在安全风险。

### 审计场景

| 场景 | 风险点 | 审计方法 |
|------|--------|----------|
| 未审计依赖 | 项目直接依赖数百个第三方 crate 而不做安全评估 | `cargo audit` 扫描 Cargo.lock 与 RustSec 数据库比对 |
| 依赖被投毒 | 攻击者通过 typosquatting 上架同名恶意包 | 检查 crates.io 包名相似性；`cargo vendor` 源码审计 |
| 废弃/无人维护 | 安全漏洞无人修复 | `cargo outdated` 检测过期；检查 GitHub 仓库活跃度 |
| 传递依赖后门 | 间接依赖未做安全评估 | `cargo tree` 分析依赖树；`cargo-scan` 链式审计 |
| `build.rs` 恶意代码 | 构建脚本下载恶意二进制或注入后门 | 审查所有 `build.rs` 文件；限制构建环境网络访问 |
| feature 引入隐患 | 某个 feature 拉取大量未经审计代码 | 对比不同 feature 组合下的代码路径 |

### 审计检查清单

- [ ] `cargo audit` 集成到 CI，每次提交自动运行
- [ ] `cargo tree` 分析完整依赖树，标记可疑传递依赖
- [ ] `cargo +nightly scan` 检测文件操作、网络调用、unsafe 等危险模式
- [ ] 审查所有 `build.rs` 文件
- [ ] 评估每个依赖的维护健康度（issue 响应速度、维护者数量、上次提交时间）

---

## 五阶段审计流程速查

### 第一阶段：依赖供应链审计
`cargo audit` → `cargo tree` → `cargo-scan` → `build.rs` 审查

### 第二阶段：代码静态分析
`cargo clippy -- -W clippy::pedantic` → `cargo geiger` → 手动审查 unsafe 块 → Siderophile 排序

### 第三阶段：边界和协议解析审计
识别外部输入接口 → 标记无大小限制的解析函数 → 标记不安全的反序列化 → Fuzz 测试

### 第四阶段：并发和资源安全审计
标注共享可变状态 → 检查 Send/Sync 正确性 → 审查锁获取顺序 → loom 并发测试

### 第五阶段：工具化验证
`cargo +nightly miri test` → ASAN/TSAN → `cargo-fuzz` 定向 fuzz

---

## 典型 CVE 案例总结

| 漏洞 | CVE 编号 | 类型 | 根本原因 | 影响模块 |
|------|----------|------|----------|----------|
| async-tar | CVE-2025-62518 | 逻辑漏洞 | 解析器 ustar/pax 头不一致 | 压缩解析模块 |
| Linux Binder | CVE-2025-68260 | 竞态条件 | 共享列表未加锁 | 并发/内核模块 |
| RustFS | CVE-2026-40937 | 权限绕过 | 认证函数调用遗漏 | Web 框架/权限模块 |
| Salvo | CVE-2026-33241 | 资源耗尽 | 无 payload 大小限制 | 解析模块 |
| keccak-asm | GHSA-3288-… | unsoundness | asm! 约束错误 | 内联汇编模块 |
| capnp | RUSTSEC-2025-0143 | unsoundness | safe API 调用 unsafe | 序列化模块 |
| std::zip | CVE-2021-28876 等 | panic 安全 | TrustedRandomAccess | 迭代器模块 |
| std::Path | CVE-2025-11233 | 路径遍历 | 平台特定路径分隔符 | 路径 API 模块 |
