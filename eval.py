import json
from collections import defaultdict
import sys
from datetime import datetime


class ResultSaver:
    def __init__(self, output_file="evaluation_results.txt"):
        self.output_file = output_file
        self.console_output = []

    def print_and_save(self, text):
        """同时打印到控制台和保存到内存"""
        print(text)
        self.console_output.append(text)

    def save_to_file(self):
        """将结果保存到文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"代码 Agent 主动澄清能力评估报告\n")
            f.write(f"生成时间: {timestamp}\n")
            f.write("=" * 80 + "\n\n")

            for line in self.console_output:
                f.write(line + "\n")

        print(f"\n✅ 结果已保存到文件: {self.output_file}")


def calculate_average_metrics_by_ambiguity_type(file_path):
    # 初始化存储结构 - 按模糊类型分类
    single_turn_metrics = {
        "missing_goal": defaultdict(list),
        "missing_premises": defaultdict(list),
        "ambiguous_terms": defaultdict(list)
    }

    multi_turn_metrics = {
        "missing_goal": defaultdict(list),
        "missing_premises": defaultdict(list),
        "ambiguous_terms": defaultdict(list)
    }

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                task_id = data.get("task_id", "")
                scenario = data.get("scenario", "")
                metrics = data.get("metrics", {})

                # 确定模糊类型
                ambiguity_type = None
                if "missing_goal" in task_id:
                    ambiguity_type = "missing_goal"
                elif "missing_premises" in task_id:
                    ambiguity_type = "missing_premises"
                elif "ambiguous_terms" in task_id:
                    ambiguity_type = "ambiguous_terms"

                if not ambiguity_type:
                    continue

                if "Single-Turn" in scenario:
                    # 单轮场景指标
                    target_dict = single_turn_metrics[ambiguity_type]
                    target_dict["kqc_coverage"].append(metrics.get("kqc_coverage", 0))
                    target_dict["mpr_coverage"].append(metrics.get("mpr_coverage", 0))
                    target_dict["total_gold_questions"].append(metrics.get("total_gold_questions", 0))
                    target_dict["total_gold_premises"].append(metrics.get("total_gold_premises", 0))
                    target_dict["matched_kqc_count"].append(metrics.get("matched_kqc_count", 0))
                    target_dict["matched_mpr_count"].append(metrics.get("matched_mpr_count", 0))
                    target_dict["unmatched_kqc_count"].append(metrics.get("unmatched_kqc_count", 0))
                    target_dict["unmatched_mpr_count"].append(metrics.get("unmatched_mpr_count", 0))

                elif "Multi-Turn" in scenario:
                    # 多轮场景指标
                    target_dict = multi_turn_metrics[ambiguity_type]
                    target_dict["clarification_coverage"].append(metrics.get("clarification_coverage", 0))
                    target_dict["efficiency_ratio"].append(metrics.get("efficiency_ratio", 0))
                    target_dict["atc"].append(metrics.get("atc", 0))
                    target_dict["total_required_clarifications"].append(metrics.get("total_required_clarifications", 0))
                    target_dict["agent_question_turns"].append(metrics.get("agent_question_turns", 0))
                    target_dict["clarified_premises_count"].append(metrics.get("clarified_premises_count", 0))
                    target_dict["unmatched_clarifications_count"].append(
                        metrics.get("unmatched_clarifications_count", 0))

    # 计算每种模糊类型的平均值
    def calculate_type_averages(metrics_dict):
        results = {}
        for amb_type, metrics in metrics_dict.items():
            type_avg = {}
            for key, values in metrics.items():
                if values:
                    type_avg[f"avg_{key}"] = sum(values) / len(values)
                    type_avg[f"total_{key}"] = sum(values)
                    type_avg[f"count_{key}"] = len(values)
            results[amb_type] = type_avg
        return results

    single_turn_results = calculate_type_averages(single_turn_metrics)
    multi_turn_results = calculate_type_averages(multi_turn_metrics)

    return {
        "single_turn": single_turn_results,
        "multi_turn": multi_turn_results
    }


def print_detailed_results_by_type(results, saver):
    """按模糊类型打印详细的统计结果"""

    saver.print_and_save("=" * 80)
    saver.print_and_save("代码 Agent 主动澄清能力评估 - 按模糊类型分类统计")
    saver.print_and_save("=" * 80)

    # 单轮场景结果
    saver.print_and_save("\n📊 单轮场景 (Single-Turn) - 按模糊类型分类:")
    saver.print_and_save("=" * 60)

    single_turn = results["single_turn"]

    for amb_type in ["missing_goal", "missing_premises", "ambiguous_terms"]:
        data = single_turn.get(amb_type, {})
        if not data:
            continue

        saver.print_and_save(f"\n🔍 {amb_type.replace('_', ' ').title()}:")
        saver.print_and_save("-" * 40)
        saver.print_and_save(f"   🔑 关键问题覆盖率 (KQC): {data.get('avg_kqc_coverage', 0):.4f}")
        saver.print_and_save(f"   📋 缺失前提召回率 (MPR): {data.get('avg_mpr_coverage', 0):.4f}")
        saver.print_and_save(
            f"   📈 平均匹配KQC数量: {data.get('avg_matched_kqc_count', 0):.2f} / {data.get('avg_total_gold_questions', 0):.2f}")
        saver.print_and_save(
            f"   📈 平均匹配MPR数量: {data.get('avg_matched_mpr_count', 0):.2f} / {data.get('avg_total_gold_premises', 0):.2f}")
        saver.print_and_save(f"   ❌ 平均未匹配KQC: {data.get('avg_unmatched_kqc_count', 0):.2f}")
        saver.print_and_save(f"   ❌ 平均未匹配MPR: {data.get('avg_unmatched_mpr_count', 0):.2f}")
        saver.print_and_save(f"   📊 任务数量: {data.get('count_kqc_coverage', 0)}")

    # 多轮场景结果
    saver.print_and_save("\n🔄 多轮场景 (Multi-Turn) - 按模糊类型分类:")
    saver.print_and_save("=" * 60)

    multi_turn = results["multi_turn"]

    for amb_type in ["missing_goal", "missing_premises", "ambiguous_terms"]:
        data = multi_turn.get(amb_type, {})
        if not data:
            continue

        saver.print_and_save(f"\n🔍 {amb_type.replace('_', ' ').title()}:")
        saver.print_and_save("-" * 40)
        saver.print_and_save(f"   🎯 澄清覆盖率: {data.get('avg_clarification_coverage', 0):.4f}")
        saver.print_and_save(f"   ⚡ 效率比率: {data.get('avg_efficiency_ratio', 0):.4f}")
        saver.print_and_save(f"   ⏱️  平均澄清轮数 (ATC): {data.get('avg_atc', 0):.4f}")
        saver.print_and_save(
            f"   📊 平均澄清前提数量: {data.get('avg_clarified_premises_count', 0):.2f} / {data.get('avg_total_required_clarifications', 0):.2f}")
        saver.print_and_save(f"   🔄 平均提问轮次: {data.get('avg_agent_question_turns', 0):.2f}")
        saver.print_and_save(f"   ❌ 平均未匹配澄清: {data.get('avg_unmatched_clarifications_count', 0):.2f}")
        saver.print_and_save(f"   📊 任务数量: {data.get('count_clarification_coverage', 0)}")


def calculate_overall_averages(results):
    """计算总体平均值（不分类型）"""
    single_turn_overall = defaultdict(list)
    multi_turn_overall = defaultdict(list)

    # 单轮场景总体平均
    for amb_type, metrics in results["single_turn"].items():
        for key, value in metrics.items():
            if key.startswith("avg_"):
                metric_name = key.replace("avg_", "")
                single_turn_overall[metric_name].append(value)

    # 多轮场景总体平均
    for amb_type, metrics in results["multi_turn"].items():
        for key, value in metrics.items():
            if key.startswith("avg_"):
                metric_name = key.replace("avg_", "")
                multi_turn_overall[metric_name].append(value)

    # 计算总体平均
    single_avg = {f"overall_avg_{k}": sum(v) / len(v) if v else 0 for k, v in single_turn_overall.items()}
    multi_avg = {f"overall_avg_{k}": sum(v) / len(v) if v else 0 for k, v in multi_turn_overall.items()}

    return {
        "single_turn": single_avg,
        "multi_turn": multi_avg
    }


def print_comparison_table(results, saver):
    """打印对比表格"""
    saver.print_and_save("\n" + "=" * 80)
    saver.print_and_save("📋 模糊类型对比表格")
    saver.print_and_save("=" * 80)

    single_turn = results["single_turn"]
    multi_turn = results["multi_turn"]

    # 单轮场景对比
    saver.print_and_save("\n📊 单轮场景指标对比:")
    saver.print_and_save("-" * 70)
    saver.print_and_save(f"{'模糊类型':<20} {'KQC':<8} {'MPR':<8} {'任务数量':<10}")
    saver.print_and_save("-" * 70)

    for amb_type in ["missing_goal", "missing_premises", "ambiguous_terms"]:
        data = single_turn.get(amb_type, {})
        if data:
            kqc = data.get('avg_kqc_coverage', 0)
            mpr = data.get('avg_mpr_coverage', 0)
            count = data.get('count_kqc_coverage', 0)
            saver.print_and_save(f"{amb_type.replace('_', ' ').title():<20} {kqc:<8.3f} {mpr:<8.3f} {count:<10}")

    # 多轮场景对比
    saver.print_and_save("\n🔄 多轮场景指标对比:")
    saver.print_and_save("-" * 70)
    saver.print_and_save(f"{'模糊类型':<20} {'澄清覆盖率':<10} {'效率比率':<10} {'ATC':<8} {'任务数量':<10}")
    saver.print_and_save("-" * 70)

    for amb_type in ["missing_goal", "missing_premises", "ambiguous_terms"]:
        data = multi_turn.get(amb_type, {})
        if data:
            coverage = data.get('avg_clarification_coverage', 0)
            efficiency = data.get('avg_efficiency_ratio', 0)
            atc = data.get('avg_atc', 0)
            count = data.get('count_clarification_coverage', 0)
            saver.print_and_save(
                f"{amb_type.replace('_', ' ').title():<20} {coverage:<10.3f} {efficiency:<10.3f} {atc:<8.3f} {count:<10}")


def print_paper_format(results, overall_results, saver):
    """输出论文格式的结果"""
    saver.print_and_save("\n" + "=" * 80)
    saver.print_and_save("📄 论文结果格式")
    saver.print_and_save("=" * 80)

    single_turn = results["single_turn"]
    multi_turn = results["multi_turn"]

    saver.print_and_save("\n单轮场景结果:")
    saver.print_and_save("-" * 40)
    for amb_type in ["missing_goal", "missing_premises", "ambiguous_terms"]:
        data = single_turn.get(amb_type, {})
        if data:
            kqc = data.get('avg_kqc_coverage', 0)
            mpr = data.get('avg_mpr_coverage', 0)
            saver.print_and_save(f"{amb_type.replace('_', ' ').title()}: KQC={kqc:.3f}, MPR={mpr:.3f}")

    saver.print_and_save(
        f"\n单轮场景总体平均: KQC={overall_results['single_turn'].get('overall_avg_kqc_coverage', 0):.3f}, MPR={overall_results['single_turn'].get('overall_avg_mpr_coverage', 0):.3f}")

    saver.print_and_save("\n多轮场景结果:")
    saver.print_and_save("-" * 40)
    for amb_type in ["missing_goal", "missing_premises", "ambiguous_terms"]:
        data = multi_turn.get(amb_type, {})
        if data:
            coverage = data.get('avg_clarification_coverage', 0)
            efficiency = data.get('avg_efficiency_ratio', 0)
            atc = data.get('avg_atc', 0)
            saver.print_and_save(
                f"{amb_type.replace('_', ' ').title()}: 澄清覆盖率={coverage:.3f}, 效率比率={efficiency:.3f}, ATC={atc:.3f}")

    saver.print_and_save(
        f"\n多轮场景总体平均: 澄清覆盖率={overall_results['multi_turn'].get('overall_avg_clarification_coverage', 0):.3f}, 效率比率={overall_results['multi_turn'].get('overall_avg_efficiency_ratio', 0):.3f}, ATC={overall_results['multi_turn'].get('overall_avg_atc', 0):.3f}")


def save_structured_data(results, overall_results, filename="structured_results.json"):
    """保存结构化数据到JSON文件"""
    structured_data = {
        "detailed_results": results,
        "overall_results": overall_results,
        "analysis_timestamp": datetime.now().isoformat()
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"✅ 结构化数据已保存到: {filename}")


# 使用示例
if __name__ == "__main__":
    input_file = "gpt5_clareval_results.jsonl"  # 替换为您的输入文件路径
    output_file = "gpt5_clareval_report.jsonl"  # 输出报告文件
    json_file = "evaluation_data.jsonl"  # 结构化数据文件

    # 初始化结果保存器
    saver = ResultSaver(output_file)

    try:
        # 计算按模糊类型分类的指标
        detailed_results = calculate_average_metrics_by_ambiguity_type(input_file)

        # 打印详细结果
        print_detailed_results_by_type(detailed_results, saver)

        # 打印对比表格
        print_comparison_table(detailed_results, saver)

        # 计算总体平均
        overall_results = calculate_overall_averages(detailed_results)

        # 输出论文格式
        print_paper_format(detailed_results, overall_results, saver)

        # 额外统计：各类型的任务分布
        saver.print_and_save("\n" + "=" * 80)
        saver.print_and_save("📈 任务分布统计")
        saver.print_and_save("=" * 80)

        single_count = {amb_type: data.get('count_kqc_coverage', 0) for amb_type, data in
                        detailed_results["single_turn"].items()}
        multi_count = {amb_type: data.get('count_clarification_coverage', 0) for amb_type, data in
                       detailed_results["multi_turn"].items()}

        saver.print_and_save(f"单轮场景任务分布: {single_count}")
        saver.print_and_save(f"多轮场景任务分布: {multi_count}")
        saver.print_and_save(f"单轮场景总任务数: {sum(single_count.values())}")
        saver.print_and_save(f"多轮场景总任务数: {sum(multi_count.values())}")

        # 保存结果到文件
        saver.save_to_file()

        # 保存结构化数据到JSON
        save_structured_data(detailed_results, overall_results, json_file)

        print(f"\n🎉 分析完成！")
        print(f"📄 详细报告: {output_file}")
        print(f"📊 结构化数据: {json_file}")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到输入文件 '{input_file}'")
        print("请确保文件路径正确，然后重新运行程序。")
    except Exception as e:
        print(f"❌ 分析过程中出现错误: {str(e)}")
        import traceback

        traceback.print_exc()