# wwlibrary

队伍代码的静态索引与压缩包。

## 地址

- 索引：https://eeeeeeeedison.github.io/wwlibrary/teams.json
- 代码包：https://eeeeeeeedison.github.io/wwlibrary/codes/

## 插件配置

把 `configs/code_fetch.json` 的 `base_url` 改为：

```json
{
  "base_url": "https://eeeeeeeedison.github.io/wwlibrary",
  "extra_archive_hosts": []
}
```

## 内容

- `teams.json`：全量索引。截至 2026-11-09，共 50 个队伍、72 份代码。
- `codes/`：队伍代码 zip。
- `teams/`、`index.html`：浏览器浏览页，插件不需要。
- `.nojekyll`：关闭 GitHub Pages 的 Jekyll 处理。
