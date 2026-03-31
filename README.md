# ASN EDU/GOV 分类工具

这个仓库提供一个可运行的 Python 脚本，用于基于 MaxMind ASN IPv4 CSV 数据，把记录按组织名称分类为 `edu` 或 `gov`，并导出两个结果文件。

## 输入数据

默认输入文件名：

- `GeoLite2-ASN-Blocks-IPv4.csv`

CSV 需要包含以下字段（MaxMind 原始格式）：

- `network`
- `autonomous_system_number`
- `autonomous_system_organization`

## 分类方法

脚本使用“关键词打分 + 负面关键词抑制”规则：

1. 对组织名做标准化（小写、去噪、压缩空格）。
2. 分别计算 EDU 分数和 GOV 分数。
3. 根据负面关键词（如 cloud/hosting/telecom 等）做减分。
4. 判定规则：
   - `gov_score >= 3` 且 `gov_score > edu_score` -> `gov`
   - `edu_score >= 3` 且 `edu_score >= gov_score` -> `edu`
   - 其他情况不输出

## 输出文件

运行后会导出：

- `edu_asn.csv`
- `gov_asn.csv`

每个文件字段结构相同：

- `asn,org,network`

同一个 ASN 下有多个网段时，会按多行展开。

## 使用方式

### 0) 获取脚本
```bash
wget https://raw.githubusercontent.com/413hy/ak/codex/clarify-your-main-objective/asn_classifier.py
```

### 1) 使用默认输入文件名

```bash
python3 asn_classifier.py
```

### 2) 指定输入文件

```bash
python3 asn_classifier.py /path/to/GeoLite2-ASN-Blocks-IPv4.csv
```

### 3) 指定输出文件名

```bash
python3 asn_classifier.py /path/to/GeoLite2-ASN-Blocks-IPv4.csv --edu-output result/edu_asn.csv --gov-output result/gov_asn.csv
```

## 脚本文件

- `asn_classifier.py`

