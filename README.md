# Telecom Notes · 通信协议实验笔记

[![SMS lab](https://github.com/GLORYDAY114/telecom-notes/actions/workflows/sms-lab.yml/badge.svg)](https://github.com/GLORYDAY114/telecom-notes/actions/workflows/sms-lab.yml)

从一个能运行、能核对结果的小实验开始：**短信 PDU 解码 → 字段解释 → 重新编码 → 字节比对**。

本仓库使用合成样例，仅做离线编解码，不连接手机、SIM 卡或运营商网络，也不会发送短信。

## 先看结果

| 样例 | 正文 | 可见字符数 | TP-UDL | TP-UD 字节数 |
|---|---|---:|---|---:|
| `gsm7` | `hellohello` | 10 | 10 septets | 9 |
| `extension` | `^` | 1 | 2 septets | 2 |
| `ucs2` | `你好` | 2 | 4 octets | 4 |

每个样例验证两件事：Pycrate 解析对象重新序列化后字节一致；从解码出的号码、正文和编码方式创建新对象后，字节也一致。固定样例与预期字段保存在 [sms_vectors.json](examples/sms_vectors.json)。

## 在 Windows 上运行

需要 Python 3.11 或以上。下载仓库 ZIP 并解压，或用 Git 克隆；在仓库文件夹里打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe sms_lab.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

这些命令直接使用虚拟环境中的 Python，不需要修改 PowerShell 执行策略。

macOS/Linux 对应命令：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python sms_lab.py
.venv/bin/python -m unittest discover -s tests -v
```

查看第一条短信的 Pycrate 字段树：

```powershell
.\.venv\Scripts\python.exe sms_lab.py --sample gsm7 --tree
```

## 阅读顺序

1. [第一课：逐字节解释短信 PDU](notes/01-sms-pdu.md)。
2. [实验代码](sms_lab.py)：先看 `encode_submit()`，再看 `decode_submit()`。
3. [测试](tests/test_sms_lab.py)：固定样例、7-septet 填充、末尾 `@`/回车、长度边界与非法输入。
4. [GitHub 操作练习](notes/02-github-practice.md)：通过分支和 PR 留下一次自己的改动。
5. [已记录的本地运行结果](notes/run-results.txt)。最新线上结果以 Actions 页面为准。

## 范围与版本

第一课只支持：SMSC 长度为 `00` 的外层、首字节 `01` 的 SMS-SUBMIT、数字型国际目的地址、PID `00`、DCS `00`/`08`，以及不含 UDH 和有效期字段的单段短信。遇到范围以外的数据会拒绝处理；这不是通用 PDU 解码器，也不是完整的协议一致性测试套件。

依赖固定为 `pycrate==0.8.1`。Pycrate 当前维护地址是 [pycrate-org/pycrate](https://github.com/pycrate-org/pycrate)，旧的 P1sec 地址不作为本实验的维护入口。标准对照使用 Release 16，具体章节见第一课；不宣称覆盖全部版本。

## 后续学习选题

- [ ] UDH 与长短信分段、重组、填充位。
- [ ] SMS-DELIVER 与短信时间戳。
- [ ] SMS over IMS 的 SIP MESSAGE 与消息体封装。
- [ ] 4G/5G NAS 短信信令流程。
- [ ] RCS 的 CPIM、MSRP 与能力协商。

这些是学习计划，尚未实现。
