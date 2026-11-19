# 数据契约：投稿格式 → teams.json → 插件

这份文档给维护者看。`meta.json` 只是投稿暂存格式；插件真正读取的是 `teams.json`。两者必须一一对应，CI 校验的是前者，发布时按下面的规则生成后者。

## 字段映射

| `meta.json` | `teams.json` 位置 | 说明 |
| --- | --- | --- |
| `team[]` | `teams[].members` / `teams[].team` / `codes[].members` / `codes[].team` | 数组原样写入；`team` 字符串用 `", "` 连接。**顺序即站位顺序，不能排序。** |
| `name` | `codes[].name` | 插件表格不直接显示，但搜索和描述弹窗会用到 |
| `author` | `codes[].author` | 表格“作者”列 |
| `version` | `codes[].version` | 表格“版本”列 |
| `description` | `codes[].description` | 描述弹窗正文；开头的 `【场景】【难度】【说明】` 行会被插件剥掉，所以这些标题行下面必须另有正文 |
| `scenes[]` | `codes[].scenes` | 插件按这个数组筛选；必须是 `日常 / 矩阵 / 深塔 / 海墟上半 / 海墟下半 / 刷4c` |
| `difficulty` | `codes[].difficulty` | 插件按这个值筛选；必须是 `高容错 / 低容错 / 椰果` |
| `tested` | 不写入 | 只作为人工审核依据；也可以并进 `description` |
| `video` | 不写入 | 只作为审核依据；可放进 README 或 PR |
| — | `codes[].timestamp` | 合并时间，Unix 秒 |
| — | `codes[].modifiedAt` | 合并时间，ISO 8601 UTC，例如 `2026-10-08T16:32:44.000Z` |
| — | `codes[].size` / `sizeFormatted` | `code.zip` 的字节数 / 人类可读大小 |
| — | `codes[].downloadCount` | 新投稿固定 `0`，之后由 `sync_download_counts.py` 同步 |
| — | `codes[].downloadUrl` / `rawUrl` | Release 资产地址，两者当前相同 |
| — | `codes[].filename` | 下载到本地的文件名，建议 `<name>_<author>_<version>.zip` |
| — | `codes[].assetName` | Release 资产名，必须与 Release 里实际上传的文件名一致 |

## 关键不变量

1. **`members` 的字符串必须与插件 `CHARACTER_NAMES` 的 key 完全一致**，否则插件里会显示英文原名。
   - `Yangyang: Xuanling` 是一个 key（显示为“秧秧·玄翎”），不能拆成两个成员。
   - `Calcharo` 在白名单里，虽然当前仓库还没有他的队伍。
2. **`scenes` / `difficulty` 必须是插件枚举的原值**。写错不会报错，但插件会把它归为“未分类”，等于白填。
3. **`team` 数组的顺序不能变**。插件按数组顺序展示队伍，投稿者的站位顺序就是显示顺序。
4. **`assetName` 必须真实存在于 Release**。`sync_download_counts.py` 只要发现任何一个 `assetName` 找不到，整个下载量同步就会失败。
5. **`totalTeams` / `totalCodes` 必须与实际数组长度一致**。插件不校验，但网页会显示错。

## 自动发布流程（`publish-submission.yml`）

投稿 PR 合并到 `main` 后，`.github/workflows/publish-submission.yml` 会自动调用 `.github/scripts/publish_submissions.py` 完成全部发布步骤：

1. 复用 `validate_submission.py` 复核 `submissions/` 下的待发布目录。
2. 上传 `code.zip` 到 Release（tag `1`），资产名按 `<ASCII前缀>_<version>_<sha8>.zip` 规则生成（已存在同名资产则幂等复用）。
3. 在 `teams.json` 与 `teams/<Slug>.json` 中写入完整派生字段并更新 `totalTeams` / `totalCodes`。
4. 核对 `teams.json` 内所有 `assetName` 均真实存在于 Release `1`，确保后续 `sync-downloads` 不会报 `release assets missing`。
5. 删除已发布的 `submissions/<Slug>/<版本>-<用户名>/` 目录，通过 `SYNC_DEPLOY_KEY` 推送回 `main`，并在关联 PR 下回复下载链接。

`index.html` 已改造为启动时动态 `fetch('teams.json')` 渲染，无需手动重新生成。如需手动补跑，可在 GitHub Actions 页面手动触发 `publish-submission`。
