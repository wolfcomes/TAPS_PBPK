# TAPS → 动力学 → PBPK

本项目研究：**将 TAPS 构象采样、QM/MM 化学反应计算与动力学网络连接，能否得到可独立检验的代谢参数，并改善 PBPK 对药物暴露的预测。**

当前处于数据与模型基础准备阶段。已有公开模型、实验参照、分子结构和 PBPK 敏感性/偏差诊断；尚未完成 TAPS、QM/MM、分子速率推导或正式的参数替换验证。文件存在、模型能运行，都不代表该科学问题已经得到验证。

## 从哪里开始

1. 阅读本页，了解目标、进度与目录。
2. 阅读[研究报告](docs/reports/research_report.md)或带目录的 [HTML 报告](docs/reports/research_report.html)，了解案例选择、关键证据和限制。
3. 按[当前研究计划](docs/plans/research_plan.md)推进；具体输入和字段说明分别见 [DXM](DXM/README.md)、[MCT](MCT/README.md)。

## 两个案例承担不同任务

| 案例 | 研究对象 | 定位 | 当前判断 |
|---|---|---|---|
| DXM | 右美沙芬 → 右啡烷，人 CYP2D6，O-去甲基化 | 主方法验证 | 公开 PBPK、观测、同反应 QM/MM 文献及目标敏感性较齐全；下一步先冻结独立体外参照和评价数据用途 |
| MCT | 野百合碱 → 脱氢野百合碱，大鼠 CYP3A1 候选支路 | PA 生物活化探索 | 现有参数是混合微粒体的母体总消耗，不能归为 CYP3A1 活化参数；母体 PBPK 基线也仍严重失配 |

OSP 模型及地昔帕明、阿普唑仑、地高辛比较材料统一放在 `DXM/`。它们用于选择研究条件和检查接口；公开模型中的拟合参数不充当独立实验真值。

## 进度与当前优先级

| 工作 | 状态 | 现在能说明什么 |
|---|---|---|
| DXM 公开模型与观测整理 | 已有 | 冻结版本含 29 个模拟、41 组观测、393 个时间点 |
| DXM/DES 目标参数敏感性 | 已完成历史计算 | 102 组主运行支持优先研究 DXM 母体终点，同时揭示参数补偿 |
| MCT 文献、补充代码、母体 PK 整理 | 已有 | 已取得 Suparmi 两份原始补充材料；Lin 曲线有 14 个近似数字化均值点 |
| MCT OSPSuite-R 重跑与偏差诊断 | 已完成历史计算 | 数值复现一致，但 IV AUC 高估约 11.26 倍，PO AUC 低估约 73.6 倍 |
| 独立 G1 参数与评价集冻结 | **下一步** | DXM 的 assay、构建体、活性酶量、结合校正与数据独立性仍需核对 |
| 反应复合物、TAPS、QM/MM、速率网络 | 待执行 | 当前 SDF/PDB 只是起始材料 |
| 正式 G0/G1/G2 与实验 PK 比较 | 待执行 | 尚无 molecular-derived 参数或正式 G2 结果 |

主线先推进 DXM 的独立参数和数据冻结，再准备催化体系。MCT 并行核对单酶/产物证据与母体模型，达到门槛后再接入分子参数。具体交付和停止条件以[研究计划](docs/plans/research_plan.md)为准。

## 项目结构

```text
TAPS_PBPK/
├── README.md
├── DXM/                 主验证案例；OSP 原始模型与比较资料
│   ├── data/            观测长表、映射、参数及来源
│   ├── models/          官方快照、选定基线、论文原生项目
│   ├── structures/      DXM/DXO SDF、CYP2D6 PDB
│   ├── references/      PBPK、QM/MM、门控研究
│   ├── results/         既有敏感性摘要、基线曲线与审计
│   └── comparators/     DES 与两个 MM 示例
├── MCT/                 PA 探索案例；与 DXM 使用同样的一级分类
│   ├── data/            代谢/PK 表、母体数字化点、旁证资料
│   ├── models/          作者原模型代码、项目 pilot 基线
│   ├── structures/      MCT、CYP3A1；MNO 单列为另一支路参考
│   ├── references/      两篇核心 PDF、两份原补充 DOCX
│   └── results/         基线失配与诊断结果
├── docs/
│   ├── plans/           唯一当前研究计划
│   ├── reports/         唯一当前报告，MD 与 HTML 同源
│   ├── references/      通用方法资料
│   ├── environment.md   执行环境、命令和模板依赖
│   └── model_catalog.csv 运行入口使用的模型目录表
├── scripts/             基线运行、报告生成、项目核验
└── legacy/              旧版本、完整历史批次、搜索与过程记录
```

活动区每类输入只保留一套；基线 PKML 无损 gzip 压缩，运行时自动解压。旧专题报告、未选候选、完整历史批次、重复结构、日志及旧 ZIP 已归档。**日常工作不需要阅读 `legacy/`。**

## 运行与维护

PBPK 使用 conda `ospsuite-r`。从项目根目录运行：

```bash
source /data/home/zhangzhiyong/miniconda3/etc/profile.d/conda.sh
conda activate ospsuite-r
Rscript scripts/run_pbpk.R DXM /tmp/taps_dxm_baseline
Rscript scripts/run_pbpk.R MCT /tmp/taps_mct_baseline
```

输出目录必须是新目录或空目录。默认重算所保存的 PKML；这是软件复现检查，不进行拟合，也不自动与实验评判精度。快照重建、DES 对照及输出单位见[环境说明](docs/environment.md)。

报告以 MD 为唯一编辑源；修改后执行 `python scripts/build_report.py`。项目结构与证据计数检查执行 `python scripts/check_project.py`。当前科学结论更新到报告，后续任务更新到计划；过程日志写入具体运行目录，替代版本移入 `legacy/`，避免再并列维护多份“当前进度”。
