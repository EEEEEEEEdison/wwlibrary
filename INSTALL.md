# 安装这套投稿规则（维护者一次性操作）

> 目标：让 `wwlibrary` 仓库具备「网页即可投稿 + CI 硬性拦截 + 自动保持索引干净」的完整闭环。
> 全程约 20 分钟，装完只需要在 GitHub 后台点几下。

## 1. 复制文件到仓库根目录

把本目录下的这些内容复制到 `wwlibrary` 仓库：

```
.github/CODEOWNERS
.github/ISSUE_TEMPLATE/
.github/PULL_REQUEST_TEMPLATE.md
.github/scripts/validate_submission.py
.github/submission-schema.json
.github/workflows/validate-submission.yml
submissions/
README.md              ← 直接替换现有 README（含完整投稿教程）
CONTRIBUTING.md
docs/
LICENSE
NOTICE.md
.gitattributes
```

如果仓库已有 `.github/workflows/`，**不要覆盖 `sync-downloads.yml`**，只新增 `validate-submission.yml`。

提交时建议单独一个 commit，例如：

```bash
git add .github submissions README.md CONTRIBUTING.md docs LICENSE NOTICE.md .gitattributes
git commit -m "新增投稿规范、CI 校验与投稿教程"
git push
```

## 2. 开启分支保护（最关键的一步）

打开仓库 **Settings → Rules → Rulesets**（或 **Settings → Branches → Add branch ruleset**），为 `main` 新建规则：

1. **Target branches**：`main`（或 `Default branch`）。
2. 勾选 **Require a pull request before merging**
   - Required approvals：`0`（一个人维护时选 0；有协作者时设 1）
   - 勾选 **Dismiss stale pull request approvals when new commits are pushed**
3. 勾选 **Require status checks to pass**
   - 搜索并添加 **`validate-submission / validate`**（必须先跑过一次 workflow 才会出现在列表里）
   - 勾选 **Require branches to be up to date before merging**
4. 勾选 **Block force pushes** 与 **Restrict deletions**
5. **Bypass list**：加上 **Repository admin**（你自己）。**个人仓库无法把 GitHub Actions 加进 bypass**（API 会报 `Actor GitHub Actions integration must be part of the ruleset source or owner organization`），所以要按下面的「2b」用部署密钥让 `sync-downloads` 继续自动提交。

> 验证：开一个测试 PR，把 `meta.json` 里 `scenes` 改成 `大世界`，确认 `validate-submission` 变红、Merge 状态 BLOCKED。

### 2b. 让 sync-downloads 穿过分支保护（部署密钥）

1. 生成一对专用 SSH 密钥（不要设密码）：
   ```bash
   ssh-keygen -t ed25519 -N "" -C "wwlibrary-sync" -f sync_key
   ```
2. **Settings → Deploy keys → Add deploy key**：粘贴 `sync_key.pub`，勾选 **Allow write access**，记下 key 的 ID（API 返回的 `id`）。
3. **Settings → Secrets and variables → Actions → New repository secret**：名字 `SYNC_DEPLOY_KEY`，值是 `sync_key` 的**私钥全文**。
4. 在 Rulesets 的 **Bypass list** 里加 **Deploy key**，选刚添加的 key（API 里 `actor_type: "DeployKey"`，`actor_id` 填 key ID）。
5. 把 `.github/workflows/sync-downloads.yml` 的提交步骤改成用 SSH 推送（核心片段）：
   ```yaml
   - name: Commit changes
     env:
       SYNC_DEPLOY_KEY: ${{ secrets.SYNC_DEPLOY_KEY }}
     run: |
       # ... git add / git commit 之后 ...
       mkdir -p ~/.ssh
       printf '%s\n' "$SYNC_DEPLOY_KEY" > ~/.ssh/id_ed25519
       chmod 600 ~/.ssh/id_ed25519
       ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
       git remote set-url origin git@github.com:EEEEEEEEdison/wwlibrary.git
       GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes" git push
   ```
6. 验证：故意把 `teams.json` 里某个 `downloadCount` 改小 1，手动跑一次 `sync-downloads`，确认它自动生成一条「同步下载量」提交并推送到 `main`。

> 本地测试过：部署密钥可以正常穿过 Ruleset 的 PR 与状态检查要求；密钥只绑定这个仓库、只有写权限，泄露影响可控，建议定期轮换。

## 3. Actions 权限

**Settings → Actions → General → Workflow permissions** 选 **Read and write permissions**，否则 `sync-downloads` 无法提交下载量。

## 4. 建标签（用于人工审核流转）

**Issues → Labels** 新建：

| 标签 | 用途 |
| --- | --- |
| `submission` | 新投稿，待处理 |
| `accepted` | 审核通过，等待合并/发布 |
| `needs-author` | 需要作者修改 |
| `needs-test` | 维护者需实机验证 |
| `rejected` | 拒绝（搬运、无法实机、恶意代码等） |

## 5. 自测（装完必做）

在本地仓库根目录运行：

```bash
python .github/scripts/validate_submission.py --all
```

Windows 上如果 `python` 指向 Microsoft Store，改用 `py .github/scripts/validate_submission.py --all`。

再开一个测试 PR 验证 CI 门禁：

| 测试 PR 内容 | 期望结果 |
| --- | --- |
| 合法 `meta.json` + `code.zip` | ✅ 绿灯 |
| `scenes` 填 `大世界` | ❌ 红灯，报「scenes 含未定义场景」 |
| `team` 填 `Roverr` | ❌ 红灯，报「角色不在白名单」 |
| 顺手改了 `teams.json` | ❌ 红灯，报「投稿 PR 只能新增文件」 |
| 一个 PR 放两个队伍 | ❌ 红灯，报「一个 PR 只能提交一个代码包」 |

测试完把测试分支删掉即可，不要合并。

## 6. 第一次提交的换行问题

`.gitattributes` 会把文本统一成 LF。首次提交可能看到大量换行变更，建议单独提交一次，不要和功能改动混在一起。

## 7. 发布与宣传

- 宣传文案模板见 [`docs/ANNOUNCEMENT.md`](docs/ANNOUNCEMENT.md)（B站专栏、QQ 群短文案、视频简介都有）。
- 发之前按文案末尾的「发布前检查」过一遍：Topics、Social preview、置顶投稿须知、示例 Release 资产。
- 建议在仓库 **Settings → General → Social preview** 上传一张 1280×640 预览图，链接分享出去更有点击率。

## 8. 注意事项

- `submissions/` 会被 GitHub Pages 一起发布，投稿 zip 在合并前就能被直接访问；介意的话可以把投稿目录改到 `inbox/`，同时改 `.github/scripts/validate_submission.py` 里的 `SUBMISSIONS` 常量。
- 合并投稿后记得上传 Release 资产并更新 `teams.json`，否则 `sync-downloads` 会报 `release assets missing`。字段写法见 [`docs/DATA-CONTRACT.md`](docs/DATA-CONTRACT.md)。
- `teams.json`、`index.html`、`teams/` 不在投稿白名单里，CI 会拒绝贡献者修改；维护者自己改不受限制（但建议也走 PR，留记录）。
- 人工审核标准见 [`docs/REVIEW-CHECKLIST.md`](docs/REVIEW-CHECKLIST.md)，逐条过一遍再合并。
