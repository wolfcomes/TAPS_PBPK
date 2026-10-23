# 运行环境与复现边界

PBPK 使用现有 conda **`ospsuite-r`**，位于 `/data/home/zhangzhiyong/miniconda3/envs/ospsuite-r`。2026-10-23 实际核对 R 4.5.3、ospsuite 12.3.2，`initPKSim()` 加载 PK-Sim 12.1.222。R 包版本与 PK-Sim 库版本不是同一个版本号。

## 基线重算

从项目根目录执行：

```bash
source /data/home/zhangzhiyong/miniconda3/etc/profile.d/conda.sh
conda activate ospsuite-r
Rscript scripts/run_pbpk.R DXM /tmp/taps_dxm_new
Rscript scripts/run_pbpk.R MCT /tmp/taps_mct_new
Rscript scripts/run_pbpk.R DES /tmp/taps_des_new
```

不要只调用环境中的 `Rscript` 而省略激活：rSharp/.NET 依赖环境设置。当前 conda 初始化会提示 `conda-libmamba-solver` / `libmambapy.QueryFormat` 插件错误；本次激活及 R 模型运行仍成功。此次整理未修改全局 conda 安装。

运行入口为 [run_pbpk.R](../scripts/run_pbpk.R)，模型清单为 [model_catalog.csv](model_catalog.csv)。脚本从自身位置解析项目路径，可从其他工作目录调用；输出路径相对调用时的工作目录。输出目录必须新建或为空。默认解压所存 PKML 到临时目录，选取现有的静脉血浆和母药肝内浓度输出，审计参数，求解后自动清理临时解压文件。

每个模拟生成 `concentrations.csv`、`units.json`、`parameter_audit.csv`；运行根目录生成环境信息和完成时的 `run_manifest.json`，记录输入 SHA256。缺少完成清单的目录视为未完成，不直接参与比较。脚本不拟合参数、不覆盖活动区结果，也不自动评价实验精度。

DXM/DES 原结果的时间为 min、浓度 µmol/L。MCT 活动区 `baseline_curves.csv` 则为 h、ng/mL；比较新 R 输出时，时间除以 60，浓度 µmol/L 乘分子量 325.36 得 ng/mL。均以各次实际单位与参数审计为准，不将不同单位 CSV 逐值直接比较。

## 从快照重建

```bash
Rscript scripts/run_pbpk.R DXM /tmp/taps_dxm_snapshot_new snapshot
Rscript scripts/run_pbpk.R MCT /tmp/taps_mct_snapshot_new snapshot
```

重建会调用 `initPKSim()` 与 `runSimulationsFromSnapshot()`，导出库的 PKML 和原始结果；每个输入放入独立输出子目录，避免导出器清理同目录其他 CSV。MCT 一个 JSON 含两个模拟，仅构建一次。此模式输出采用库原生格式，需另行按名称/单位与基线核对；不保证跨版本逐位相同。

MCT 运行不再从外部咖啡因等基础模板取参。原试点继承的求解框架、通用 Rat、生理/计算方法仍已写入快照/PKML；这属于模型假设，不能通过搬文件消除。作者七室 PBK 代码单独保存在 `MCT/models/author_original/`，本入口不把它当 PK-Sim 模型执行。

## 文档与完整性维护

Python 入口使用当前可用的 Python 3、`markdown_it` 和 `beautifulsoup4`；PBPK 求解不依赖 Python。

```bash
python scripts/build_report.py
python scripts/check_project.py
python scripts/check_project.py --archive
```

报告只编辑 [MD 源文件](reports/research_report.md)，HTML 是同源生成视图。核验包括活动文档链接、HTML 同步、模型目录、压缩模型解析、数据计数及结构来源哈希；`--archive` 另逐文件核对归档前哈希及活动证据迁移来源。

`historical_rerun_verification.json`、旧运行审计等原证据中的旧路径保留原值，作为历史上下文；当前可执行入口只读取新目录表。完整迁移清单和本次核验记录留在 `legacy/2026-10-23_project_reset/`，无需纳入日常阅读。

本次已实际求解全部 8 个 PKML 基线（DXM 3、DES 3、MCT 2），并从项目外的工作目录重建 MCT 快照的两个模拟。DXM/DES 所保留各输出列与历史值一致；MCT PKML 对历史曲线的最大峰值归一差为 3.38×10⁻⁸，AUC 最大相对差为 2.57×10⁻⁹；MCT 快照原生导出与保留曲线一致。新 R 输出与库原生导出使用不同输出配置和数值表示，不声称所有格式逐位相同。上述检查验证目录重构后的软件复现，未验证模型的实验准确性。

`ospsuite-r` 是 PBPK 环境，不代表已经安装 TAPS、MD、QM/MM 软件或准备好催化体系。相关方法与资源需按[研究计划](plans/research_plan.md)另行确定。
