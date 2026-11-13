# wwlibrary 鸣潮队伍代码库

> 鸣潮自动化队伍代码的静态索引平台，按 **队伍 / 场景 / 难度** 多维分类。与 OK-WW（ok-wuthering-waves）生态的「代码获取 (code-fetch)」插件原生打通，支持游戏内一键检索、下载与导入。

[![validate-submission](https://github.com/EEEEEEEEdison/wwlibrary/actions/workflows/validate-submission.yml/badge.svg)](https://github.com/EEEEEEEEdison/wwlibrary/actions/workflows/validate-submission.yml)
[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)

- 🌐 **在线静态索引页**：[https://eeeeeeeedison.github.io/wwlibrary/](https://eeeeeeeedison.github.io/wwlibrary/)
- 📦 **插件聚合数据源 (JSON)**：[https://eeeeeeeedison.github.io/wwlibrary/teams.json](https://eeeeeeeedison.github.io/wwlibrary/teams.json)
- 💾 **代码分发存储**：GitHub Release 资产（纯静态分发，无中心服务器、不收费、不设广告）

---

## 目录
- [客户端搭配与使用](#客户端搭配与使用)
- [核心分类口径速查](#核心分类口径速查)
- [如何投稿（30 秒极速指南）](#如何投稿30-秒极速指南)
- [硬性审查与 CI 门禁规则](#硬性审查与-ci-门禁规则)
- [常用角色英文名速查表](#常用角色英文名速查表)
- [作者权益与版权声明](#作者权益与版权声明)

---

## 客户端搭配与使用

本仓库作为上游公共代码库，供 OK-WW 工具链直接抓取与下载：

1. **安装插件**：在 OK-WW 插件目录安装 `code-fetch` 插件。
2. **默认接入**：插件默认已指向本库（`https://eeeeeeeedison.github.io/wwlibrary`）。
3. **筛选下载**：在客户端的「代码获取」标签页，按角色、场景、难度筛选心仪队伍，点击「下载」。
4. **一键导入**：在「角色代码」管理页中直接导入下载的 zip 包即可使用。

---

## 核心分类口径速查

> ⚠️ **重要**：客户端插件内建有严格的场景与难度白名单，**非白名单分类会被客户端自动丢弃或归为未分类**。投稿时请严格遵守以下标准：

### 1. 适用场景（`scenes`，只能从以下 6 项中选择）
| 场景标签 | 适用范围与说明 |
| :--- | :--- |
| **`日常`** | 日常任务 / 体力清理等通用循环 |
| **`矩阵`** | 矩阵玩法专用轴（按副本机制特化） |
| **`深塔`** | 深塔攻坚 / 竞速循环轴 |
| **`海墟上半`** | 海墟上半层专用轴 |
| **`海墟下半`** | 海墟下半层专用轴 |
| **`刷4c`** | 大世界 4C 声骸速刷 / 定点讨伐 |

### 2. 操作难度（`difficulty`，只能 3 选 1）
| 难度标签 | 定位与特征 |
| :--- | :--- |
| **`高容错`** | 容错率高、站位与闪避要求宽松、不易脱轴 |
| **`低容错`** | 追求极限效率 / 压榨伤害，对卡刀、充能与练度要求严苛 |
| **`椰果`** | 低配逃课、整活或特定机制对策玩法 |

---

## 如何投稿（30 秒极速指南）

**无需安装 Git，无需命令行，用 GitHub 网页端即可在 1 分钟内完成投稿！**

### 提交流程四步走：
1. **Fork 仓库**：点击页面右上角的 `Fork` 按钮，将本仓库克隆到你自己的 GitHub 账号下。
2. **新建投稿目录**：
   - 回到你 Fork 仓库的**根目录**（不要先进入 `submissions/`）。
   - 点击右上角 `Add file` → `Create new file`。
   - 在文件名栏输入完整路径：`submissions/<队伍Slug>/<版本号>-<你的GitHub用户名>/meta.json`。
     > *例如*：`submissions/Buling_Hsin_Rover/1.0.0-alice/meta.json`（输入斜杠会自动生成多级目录）。
     > 如果你当前已经在 `submissions/` 目录里，则只输入 `<队伍Slug>/<版本号>-<用户名>/meta.json`，不要再带 `submissions/` 前缀。
   - 将下方的 [`meta.json` 模板](#metajson-填写规范) 粘贴进去，按实际配置修改后提交。
3. **上传代码包**：
   - 切换到刚创建好的目录下，点击 `Add file` → `Upload files`。
   - 将游戏导出的队伍代码压缩包上传，重命名为 **`code.zip`**（根目录必须包含 `team.json`）。
4. **发起 Pull Request (PR)**：
   - 回到原仓库（`EEEEEEEEdison/wwlibrary`），点击 **New pull request**，点击 **Create pull request**。
   - CI 自动化机器人会在 10 秒内检查格式。如果出现红叉 ❌，点进详情按报错修改即可；绿灯 ✅ 后等待维护者合入！

---

## `meta.json` 填写规范

```json
{
  "schemaVersion": 1,
  "name": "心卜雷25秒速刷",
  "team": ["Buling", "Hsin", "Rover"],
  "author": "亦",
  "version": "1.0.0",
  "scenes": ["刷4c"],
  "difficulty": "高容错",
  "description": "【说明】\n1. 25 秒速刷轮椅轴，雷主带镜影套，切雷主先手；\n2. 刚需心 120% / 雷主 142% / 卜灵 186% 充能；\n3. 适合稳定挂机刷声骸。",
  "tested": "实机跑通 24 小时，01 心 / 21 雷主 / 60 卜灵，无脱轴卡死。",
  "video": "https://www.bilibili.com/video/BVxxxxxx",
  "contact": "QQ: 12345678",
  "license": "CC-BY-NC-SA-4.0"
}
```

### 字段说明：
- `team`：角色英文名数组（3~4人），**顺序即为游戏内站位顺序**（[速查表见下文](#常用角色英文名速查表)）。
- `version`：语义化版本（如 `1.0.0`），同一作者同一队伍再次提交时，版本号必须递增（如 `1.0.1`）。
- `description`：20~4000 字，必须包含轴顺序、起手要求、循环要点。**请勿只写一两句话**，插件端有字数展示要求。
- `tested`：10~1000 字，必须陈述实机测试配置（练度、共鸣链、武器）。

---

## 硬性审查与 CI 门禁规则

为了防止提交冲突并保证插件端正常运作，本仓库部署了自动化硬性拦截：

- 🛡️ **严格目录隔离**：
  - 每个 PR **只能在 `submissions/` 下新增一个投稿目录**。
  - **严禁修改主索引 `teams.json`、页面 `index.html` 或修改/删除他人历史代码**。凡是触碰既有文件的 PR 会被 CI 立即阻断。
- 🛡️ **数据格式校验**：
  - 自动核对 `scenes` 与 `difficulty` 是否在白名单内。
  - 自动核对 `code.zip` 内部 `team.json` 与外层 `meta.json` 的名称、作者、队伍名是否完全一致。
  - 自动校验 zip 是否包含 macOS 垃圾文件（`.DS_Store`, `__MACOSX`）或越界非法字符。
- 🛡️ **分支保护强拦截**：
  - CI 检查未全部通过的 PR，合并按钮将被锁定，无法合入主分支。

---

## 常用角色英文名速查表

> 目录 Slug 与 `team` 数组必须使用标准英文名（大小写敏感）。插件按这些名字显示中文，写错不会出现在角色筛选里。

| 中文 | 英文 | 中文 | 英文 | 中文 | 英文 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 爱弥斯 | `Aemeath` | 奥古斯塔 | `Augusta` | 白芷 | `Baizhi` |
| 布兰特 | `Brant` | 卜灵 | `Buling` | 卡卡罗 | `Calcharo` |
| 椿 | `Camellya` | 坎特蕾拉 | `Cantarella` | 珂莱塔 | `Carlotta` |
| 卡提希娅 | `Cartethyia` | 长离 | `Changli` | 千咲 | `Chisa` |
| 炽霞 | `Chixia` | 夏空 | `Ciaccona` | 达妮娅 | `Denia` |
| 嘉贝莉娜 | `Galbrena` | 绯雪 | `Hiyuki` | 心 | `Hsin` |
| 尤诺 | `Iuno` | 景燃 | `JingRan` | 今汐 | `Jinhsi` |
| 忌炎 | `Jiyan` | 洛瑟菈 | `Lucilla` | 露西 | `Lucy` |
| 露帕 | `Lupa` | 琳奈 | `Lynae` | 莫宁 | `Mornye` |
| 莫特斐 | `Mortefi` | 菲比 | `Phoebe` | 弗洛洛 | `Phrolova` |
| 清宵 | `Qingxiao` | 仇远 | `Qiuyuan` | 丽贝卡 | `Rebecca` |
| 漂泊者（主角） | `Rover` | 散华 | `Sanhua` | 守岸人 | `Shorekeeper` |
| 西格莉卡 | `Sigrika` | 穗穗 | `Suisui` | 锁冥 | `Suoming` |
| 维里奈 | `Verina` | 秧秧·玄翎 | `Yangyang: Xuanling` | 釉瑚 | `Youhu` |
| 赞妮 | `Zani` | 折枝 | `Zhezhi` | | |

> ⚠️ `Yangyang: Xuanling` 是**一个**角色（秧秧·玄翎），数组里必须写成一项，不要拆成 `Yangyang` 和 `Xuanling`。
> 完整白名单（含校验枚举）见 [`.github/submission-schema.json`](.github/submission-schema.json)。新角色上线时先开 Issue 由维护者加入白名单，不要自己在 PR 里改 schema。

---

## 作者权益与版权声明

1. **作者署名与权益保障**：
   - 静态索引页与插件展示端将**永久保留原作者署名**与更新日志。
   - 官方自动统计并同步 Release 下载量，绝不擦除作者劳动成果。
2. **开源分发协议**：
   - 仓库所有代码包遵循 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)（署名-非商业性使用-相同方式共享）协议分发。
   - 严禁将本仓库整理或收录的代码打包用于任何商业牟利行为。
3. **侵权与下架反馈**：
   - 如果本仓库收录的代码存在未经授权搬运、侵犯您的权益或作者本人要求下架，请直接在 Issue 中提出或联系维护者，我们将在核实后第一时间删除并清理 Release 资产。
