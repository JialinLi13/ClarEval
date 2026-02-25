import json
import math
from collections import defaultdict
from datetime import datetime
import sys


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
            f.write(f"ClarEval 评测报告 (Based on ACL_CodeAgent)\n")
            f.write(f"生成时间: {timestamp}\n")
            f.write("=" * 80 + "\n\n")

            for line in self.console_output:
                f.write(line + "\n")

        print(f"\n✅ 结果已保存到文件: {self.output_file}")


def safe_mean(values):
    """计算平均值，处理空列表"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_metrics(file_path, saver):
    # 初始化存储结构
    # 结构: metrics[dataset_type][fuzzy_type] = list of results
    metrics = {
        "single_turn": defaultdict(list),
        "multi_turn": defaultdict(lambda: defaultdict(list))
    }

    total_tasks = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line.strip())
                total_tasks += 1

                dataset_type = data.get("dataset", "unknown")
                fuzzy_type = data.get("fuzzy_type", "unknown")

                if dataset_type == "single_turn":
                    # Single Turn: 主要评估是否识别出了意图（KQC）
                    # 由于没有 Ground Truth Label，这里我们统计模型回复的长度作为简单参考
                    # 或者检查是否包含问号 '?' 来判断是否进行了提问
                    has_question = 1 if "?" in data.get("model_response", "") else 0
                    metrics["single_turn"][fuzzy_type].append(has_question)

                elif dataset_type == "multi_turn":
                    # Multi Turn: 计算 ATC, MPR (Count), EAR
                    script = data.get("dialogue_script", [])

                    # 提取所有澄清成功的轮次索引
                    turn_indices = [turn.get("turn_index", 0) for turn in script if "turn_index" in turn]

                    # 1. Clarified Count (MPR的分子)
                    clarified_count = len(turn_indices)

                    # 2. ATC (Average Turns to Clarify)
                    # 只有在有澄清发生时才计算 ATC
                    if clarified_count > 0:
                        current_atc = sum(turn_indices) / clarified_count
                    else:
                        current_atc = None  # 标记为 None，不计入平均

                    # 3. EAR Score (Efficiency-Adjusted Recall)
                    # 公式: Sum( 1 / log2(turn + 1) )
                    current_ear_score = sum(1 / math.log2(t + 1) for t in turn_indices)

                    metrics["multi_turn"][fuzzy_type]["clarified_count"].append(clarified_count)
                    if current_atc is not None:
                        metrics["multi_turn"][fuzzy_type]["atc"].append(current_atc)
                    metrics["multi_turn"][fuzzy_type]["ear_score"].append(current_ear_score)

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {file_path}")
        return

    # --- 输出报告 ---

    saver.print_and_save(f"📊 数据集概览")
    saver.print_and_save(f"总任务数: {total_tasks}")
    saver.print_and_save("-" * 80)

    # 1. Multi-Turn Analysis
    saver.print_and_save(f"\n🤖 多轮对话评估 (Multi-Turn Evaluation)")
    saver.print_and_save(
        f"{'Ambiguity Type':<25} | {'Avg Clarified':<15} | {'ATC (Efficiency)':<18} | {'EAR Score':<15}")
    saver.print_and_save("-" * 80)

    overall_multi = defaultdict(list)

    for f_type, res in metrics["multi_turn"].items():
        avg_count = safe_mean(res["clarified_count"])
        avg_atc = safe_mean(res["atc"])
        avg_ear = safe_mean(res["ear_score"])

        # 收集总体数据
        overall_multi["clarified_count"].extend(res["clarified_count"])
        overall_multi["atc"].extend(res["atc"])
        overall_multi["ear_score"].extend(res["ear_score"])

        saver.print_and_save(f"{f_type:<25} | {avg_count:<15.3f} | {avg_atc:<18.3f} | {avg_ear:<15.3f}")

    # 打印多轮总体平均
    if overall_multi:
        saver.print_and_save("-" * 80)
        ov_count = safe_mean(overall_multi["clarified_count"])
        ov_atc = safe_mean(overall_multi["atc"])
        ov_ear = safe_mean(overall_multi["ear_score"])
        saver.print_and_save(f"{'OVERALL':<25} | {ov_count:<15.3f} | {ov_atc:<18.3f} | {ov_ear:<15.3f}")

    # 2. Single-Turn Analysis
    saver.print_and_save(f"\n📝 单轮对话评估 (Single-Turn Analysis)")
    saver.print_and_save(f"注意: 此处仅统计回复中包含问号的比例 (Question Rate)，作为主动澄清意愿的参考。")
    saver.print_and_save(f"{'Ambiguity Type':<25} | {'Question Rate':<15}")
    saver.print_and_save("-" * 50)

    overall_single = []
    for f_type, questions in metrics["single_turn"].items():
        q_rate = safe_mean(questions)
        overall_single.extend(questions)
        saver.print_and_save(f"{f_type:<25} | {q_rate:<15.3%}")

    if overall_single:
        saver.print_and_save("-" * 50)
        saver.print_and_save(f"{'OVERALL':<25} | {safe_mean(overall_single):<15.3%}")

    saver.save_to_file()


if __name__ == "__main__":
    # 你的输入文件路径
    input_file = "gpt5_clareval_results.jsonl"

    saver = ResultSaver()
    print(f"🚀 开始评估文件: {input_file}...")
    calculate_metrics(input_file, saver)