# 第二课：用一次小改动练习 GitHub

建议先读完第一课，再自己做以下步骤。本页是练习说明，不代表这些分支或 PR 已经创建。

1. 在仓库 Code 页点击 `main` 分支选择器，创建 `learn/sms-extension` 分支。
2. 在该分支编辑 `examples/sms_vectors.json`，增加一个学习样例，或先给第一课增加一句你自己的理解。
3. 用能解释变化的提交说明，例如 `docs: 补充 TP-UDL 的理解`，提交到练习分支。
4. 打开 Pull requests → New pull request，比较练习分支与 `main`。说明修改目的和验证结果。
5. 打开 PR 的 Files changed 看具体差异；在 Checks 中查看 `SMS lab`。成功、失败、跳过和等待是不同状态。
6. 如果失败，展开失败 job 和步骤日志，定位出错的测试；修复后提交到同一分支，PR 会自动更新。
7. 审阅完成且检查通过后合并。合并后可删除练习分支，提交历史和 PR 仍保留。

学习项目之外，给别人贡献代码前先读其 `CONTRIBUTING`。没有写权限时通常先 Fork；自己的仓库用分支即可。

参考：[GitHub flow](https://docs.github.com/en/get-started/using-github/github-flow)、[PR 入门](https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart)。
