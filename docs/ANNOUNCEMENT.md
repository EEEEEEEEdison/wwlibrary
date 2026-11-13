# 宣传文案（可直接改）

## 标题备选

- 鸣潮队伍代码库开放投稿：按角色 / 场景 / 难度筛选，插件一键下载
- 做了个鸣潮队伍代码索引，现在缺你的那套轴
- 不用翻群文件了：鸣潮队伍代码按队伍归档，支持插件直接下载

## 正文（B站专栏 / 贴吧 / NGA）

玩鸣潮抄队伍代码，最烦的应该不是没有代码，而是：

- 群文件翻半天，不知道哪个是新版；
- 文件名只有“最终版”“真最终版”；
- 想找“海墟下半 + 高容错”的轴，只能一个个点开看；
- 作者想更新，旧包还挂在群文件里，没人知道有新版本。

所以我做了一个静态索引：**wwlibrary**。

它把队伍代码按「队伍 / 场景 / 难度」归档，配合 OK-WW 的「代码获取」插件，可以直接在游戏里筛选、下载、导入。索引是纯静态的 GitHub Pages，不登录、不收费、不挂广告。

**在线索引**：https://eeeeeeeedison.github.io/wwlibrary/
**仓库**：https://github.com/EEEEEEEEdison/wwlibrary
**投稿指南**：https://github.com/EEEEEEEEdison/wwlibrary/blob/main/CONTRIBUTING.md

现在仓库里已经有几十套代码，但一个人的测试量有限，所以开放投稿。投稿只需要在 GitHub 网页上操作，**不用装 Git、不用命令行**：

1. Fork 仓库；
2. 在 `submissions/<队伍Slug>/<版本号>-<你的用户名>/` 下放两个文件：`meta.json` + `code.zip`；
3. 发起 Pull Request，等 CI 自动检查变绿。

格式不对的 PR 不会被合并——场景、难度、角色名都有硬性白名单，CI 会直接标红指出哪一行错了。

投稿不白投：

- 索引页和插件里都会保留作者署名；
- 下载量按作者累计，后面会做作者榜；
- 每个版本都能追溯到提交记录，不会再出现“最终版覆盖最终版”。

审核会看三件事：**实机跑通、配置写清、代码来源可确认**。格式问题 CI 会拦，内容问题我会在 PR 里说清楚。

如果你手里有压箱底的轴，欢迎来投；如果只是想要某个队伍，也可以开 Issue 点名，我尽量摇人。

## 短版（QQ 群 / Discord）

> 做了个鸣潮队伍代码索引，按队伍 / 场景 / 难度分类，OK-WW 的「代码获取」插件可直接筛选下载：https://eeeeeeeedison.github.io/wwlibrary/
> 现在开放投稿，GitHub 网页端就能提 PR（不用装 Git）：https://github.com/EEEEEEEEdison/wwlibrary/blob/main/CONTRIBUTING.md
> 要求：实机跑通、写清配置、代码来源可确认。作者署名和下载量都会保留。

## B站视频简介

> 鸣潮队伍代码索引 wwlibrary：按角色、场景、难度筛选，OK-WW 插件一键下载导入。
> 索引：https://eeeeeeeedison.github.io/wwlibrary/
> 投稿：https://github.com/EEEEEEEEdison/wwlibrary/blob/main/CONTRIBUTING.md
> 这期主要演示怎么用，以及投稿格式。代码都是社区作者写的，我只是做归档和索引；如有冒犯请联系下架。

## 发布前检查

- [ ] README 顶部一眼能看到“这是什么 / 怎么用 / 怎么投稿”
- [ ] 仓库加了 Topics：`wuthering-waves` `wuwa` `ok-ww` `game-automation`
- [ ] 设置了 Social preview 图（Settings → Social preview）
- [ ] Release 里至少有一个可下载的示例代码
- [ ] 分支保护已开启，`validate-submission / validate` 是 required check
- [ ] 置顶 Issue 或 Discussion 里放了投稿须知
- [ ] 宣传文案里的链接都能打开
