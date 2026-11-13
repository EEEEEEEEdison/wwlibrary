# 投稿指南

感谢愿意分享队伍代码。这个仓库只做一件事：**按队伍归档代码包，并让索引能按队伍 / 场景 / 难度分类**。所以投稿的格式必须统一，CI 会自动检查，格式不对的 PR 不会被合并。

## 30 秒流程（会用 GitHub 网页就行，不用命令行）

> GitHub 网页端**不需要手动建文件夹**：在新建文件名输入框里直接敲带斜杠的完整路径，提交时会自动创建整条目录链。

1. **Fork**：打开 [仓库主页](https://github.com/EEEEEEEEdison/wwlibrary)，点右上角 **Fork** → **Create fork**，fork 到自己账号。
2. **建 meta.json**：回到你 fork 仓库的**根目录** → **Add file** → **Create new file**，在文件名框里输入完整路径：
   ```
   submissions/<队伍Slug>/<版本号>-<你的GitHub用户名>/meta.json
   ```
   - 例：`submissions/Buling_Hsin_Rover/1.0.1-alice/meta.json`
   - 如果你已经在 `submissions/` 目录内，只输入 `<队伍Slug>/<版本号>-<用户名>/meta.json`，不要再带 `submissions/` 前缀（否则会套娃成 `submissions/submissions/...`）。
   - 内容照抄 [`submissions/_template/meta.json`](submissions/_template/meta.json)，按下一节说明改。填完点 **Commit changes**。
3. **传 code.zip**：再进入刚建好的 `submissions/<队伍Slug>/<版本号>-<用户名>/` 目录 → **Add file** → **Upload files**，把游戏内导出的队伍代码包拖进去，**文件名必须是 `code.zip`**（根目录必须带 `team.json`）。上传后 **Commit changes**。
4. **发起 PR**：回到原仓库 `EEEEEEEEdison/wwlibrary`，页面会提示 **Compare & pull request**；没有提示就点 **New pull request** → **compare across forks**，左边选原仓库 `main`，右边选你的 fork 和分支，点 **Create pull request**。PR 描述会自动带出模板，把自检清单勾完。
5. **等 CI**：`validate-submission` 会扫描你的改动。✅ 绿灯等维护者审核；❌ 红灯点 **Details** 看具体报错，按提示改完再提交，CI 会自动重跑。
6. **入库**：维护者合并后，代码包会转存到 Release，几分钟内出现在索引页和插件里。

> 一个 PR 只提交一个代码包。多个队伍请分开提，方便单独审核和回滚。

### 常见网页端错误

| 现象 | 原因 | 怎么改 |
| --- | --- | --- |
| CI 报 `投稿目录必须是 submissions/<Slug>/<版本>-<用户名>` | 目录层级少了或多了 | 检查路径正好是两层：队伍 Slug + 版本-用户名 |
| CI 报 `投稿 PR 只能新增文件` | 你在网页上直接改了 `teams.json` 或旧投稿 | 把该文件改回去，只留自己目录里的两个新文件 |
| CI 报 `角色 XX 不在白名单` | 英文名拼错或用了中文 | 对照下方白名单/速查表，注意大小写 |
| CI 报 `code.zip 根目录缺少 team.json` | 压缩时把文件夹也打进去了 | 选中 `team.json` 和角色脚本一起压缩，而不是压缩外层文件夹 |
| CI 报 `zip 内含系统垃圾文件` | macOS 压缩带出 `__MACOSX`/`.DS_Store` | 清掉垃圾文件重新打包（Windows 用资源管理器直接压缩即可） |

## 目录长这样

```
submissions/
└── Buling_Hsin_Rover/
    └── 1.0.1-alice/
        ├── meta.json
        └── code.zip
```

- **Slug**：队伍角色的英文名，按**游戏内站位顺序**用下划线连接，大小写必须和游戏一致。角色名里的空格和冒号会变成下划线，例如 `Yangyang: Xuanling` → `Yangyang_Xuanling`。
- **版本号**：`主版本.次版本.修订号`，例如 `1.0.0`。同一队伍同一作者的新提交必须大于已发布的最新版本。
- **用户名**：你的 GitHub 用户名或常用英文 ID，只用于避免目录冲突。

## meta.json 字段

```json
{
  "schemaVersion": 1,
  "name": "心卜雷",
  "team": ["Buling", "Hsin", "Rover"],
  "author": "亦",
  "version": "1.0.0",
  "scenes": ["刷4c"],
  "difficulty": "高容错",
  "description": "【说明】\n25 秒轮椅轴，雷主带镜影套，切雷主先手……",
  "tested": "已实机跑通，01 心 / 21 雷主 / 60 卜灵，心 120% 雷主 142% 卜灵 186%。",
  "video": "",
  "license": "CC-BY-NC-SA-4.0"
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schemaVersion` | 是 | 固定 `1` |
| `name` | 是 | 代码名，40 字以内 |
| `team` | 是 | 3–4 个角色英文名，**顺序就是站位顺序** |
| `author` | 是 | 署名，24 字以内，不能包含 `/ \ : * ? " < > \|` |
| `version` | 是 | `X.Y.Z`，且必须与目录名前缀一致 |
| `scenes` | 是 | 至少一个，只能从下方枚举里选 |
| `difficulty` | 是 | `椰果` / `高容错` / `低容错` |
| `description` | 是 | 20–4000 字，建议以 `【说明】` 开头；标题行下面必须另有正文，否则插件会显示“作者未填写详细说明” |
| `tested` | 是 | 10–1000 字，写实机测试情况；没实机跑过会被拒 |
| `video` | 否 | http(s) 链接，实机视频或截图 |
| `contact` | 否 | 联系方式，80 字以内 |
| `license` | 是 | 固定 `CC-BY-NC-SA-4.0` |

**场景枚举（只能选这些）**：`矩阵`、`深塔`、`海墟上半`、`海墟下半`、`刷4c`、`日常`

<details>
<summary>角色英文名白名单（45 个，点开）</summary>

`Aemeath` `Augusta` `Baizhi` `Brant` `Buling` `Calcharo` `Camellya` `Cantarella` `Carlotta` `Cartethyia` `Changli` `Chisa` `Chixia` `Ciaccona` `Denia` `Galbrena` `Hiyuki` `Hsin` `Iuno` `JingRan` `Jinhsi` `Jiyan` `Lily` `Lucilla` `Lucy` `Lupa` `Lynae` `Mornye` `Mortefi` `Phoebe` `Phrolova` `Qingxiao` `Qiuyuan` `Rebecca` `Rover` `Sanhua` `Shorekeeper` `Sigrika` `Suisui` `Suoming` `Verina` `Yangyang: Xuanling` `Youhu` `Zani` `Zhezhi`

> `Yangyang: Xuanling` 是**一个**角色（秧秧·玄翎），必须作为数组里的一项填写，不要拆成 `Yangyang` 和 `Xuanling`。

新角色不在名单里时，请先开 Issue，由维护者加入 `.github/submission-schema.json`；不要在 PR 里改这份文件。

</details>

## 硬性规则（CI 会拦，没有例外）

1. **只在 `submissions/` 下新增文件**。不要改 `teams.json`、`index.html`、`teams/`，也不要修改已有投稿（包括别人的和旧版本的）；索引由维护者统一生成。
2. **一个投稿目录只能有两个文件**：`meta.json` 和 `code.zip`，不能有子目录、截图或说明文件（图片请贴 PR 描述）。
3. **`meta.json` 必须通过 schema**：字段齐全、类型正确、没有未知字段。
4. **队伍 3–4 人**，必须是白名单里的英文名，不能重复；`Slug` 必须等于 `team` 按上面的转换规则用 `_` 连接。
5. **版本号必须是 `X.Y.Z`**，且大于该队伍该作者已发布的最新版本；重复版本会被拒。
6. **`code.zip` 不超过 5 MB、不超过 40 个文件、解压后不超过 20 MB**。
7. **zip 内只允许** `.py` `.json` `.txt` `.md` `.png` `.jpg` `.jpeg` `.webp`；禁止嵌套压缩包、可执行文件、隐藏文件、`__MACOSX` 和 `.DS_Store`。
8. **zip 根目录必须有 `team.json`**，且其中 `name` / `author` / `version` / `team` 必须与 `meta.json` 完全一致（这是游戏内显示和索引对得上的关键）。
9. **`license` 必须是 `CC-BY-NC-SA-4.0`**，提交即表示你同意以此协议分发。
10. **一个 PR 一个代码包**，禁止把多个队伍塞进一个 PR。

## 质量要求（人工审核，可能被打回）

- 必须**实机跑通**，并在 `tested` 里写清：角色配置、共鸣链、武器、共鸣效率、测试场景。
- 说明要能让陌生人复现：起手顺序、循环、什么时候开大、哪些角色需要手动。
- 搬运他人代码必须提供**原作者授权截图**；无法确认授权的直接关闭。
- 含网络请求、文件写入、`eval` / `exec`、`subprocess` 等调用的，需要额外说明用途，维护者有权拒绝。
- 代码里不要带账号、UID、本机绝对路径等隐私信息。

## 本地自检（可选，但推荐）

需要 Python 3.10+：

```bash
python .github/scripts/validate_submission.py --all
```

Windows 上如果 `python` 指向 Microsoft Store，改用 `py .github/scripts/validate_submission.py --all`。

## 提交即授权

你保留代码的著作权。提交 PR 即表示：

1. 你有权分发这份代码，或已获得原作者授权；
2. 同意该代码以 **CC BY-NC-SA 4.0**（署名—非商业性使用—相同方式共享）发布；
3. 允许仓库在索引页、Release 和 README 中展示代码名、作者名和下载量。

如果不同意，请不要提交。

## 维护者发布流程

字段如何写进 `teams.json`、插件读哪些字段，见 [docs/DATA-CONTRACT.md](docs/DATA-CONTRACT.md)。

1. PR 通过 `validate-submission` 后，人工检查 `tested` 和代码内容。
2. 合并到 `main`。
3. 将 `code.zip` 上传到 Release（tag `1`），资产名按现有规则生成。
4. 更新 `teams.json`（新增 code、`downloadCount` 归零），重新生成 `index.html`。
5. 删除 `submissions/<Slug>/<版本>-<用户名>/`，避免仓库体积重复膨胀。

> 分支保护注意：`sync-downloads.yml` 会直接 push `main`。如果开启 “Require a pull request before merging”，要给 `github-actions[bot]` 加 bypass，或把该 workflow 改成提 PR，否则下载量同步会失败。

## 一次性设置（管理员）

在 GitHub 仓库设置里完成这几步，规则才会真正“硬”：

1. **Settings → Branches → Add branch protection rule**，保护 `main`：
   - 勾选 **Require a pull request before merging**
   - 勾选 **Require status checks to pass before merging**，把 `validate-submission / validate` 设为必需
   - 勾选 **Require review from Code Owners**（配合 `.github/CODEOWNERS`）
   - 勾选 **Do not allow bypassing the above settings**
2. **Settings → Actions → General → Workflow permissions**：选 **Read and write permissions**，否则 `sync-downloads` 无法提交下载量。
3. **Settings → Branches** 里给 `sync-downloads` 用的 `github-actions[bot]` 加 bypass，或把该 workflow 改成自动提 PR。
4. **Issues → Labels** 建好这几个标签：`submission`、`accepted`、`needs-author`、`needs-test`、`rejected`。
5. **Settings → General → Social preview** 上传一张 1280×640 的预览图，发链接时更容易被点开。
