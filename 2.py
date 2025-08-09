import json
import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 添加时间处理相关导入
import datetime
import email.utils

# 加载模型和分词器
model_path = r"D:\model_bf\Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype="auto", device_map="auto"
)


# 翻译函数
def translate_text(text):
    # 构造更明确的提示词，要求翻译成中文，并特别指定术语翻译
    prompt = f"将以下英文翻译成中文!只输出翻译结果，不要添加任何其他内容：{text}"
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(**model_inputs, max_new_tokens=32768)
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()
    try:
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
    torch.cuda.empty_cache()
    return content


# 逐条翻译新闻内容
def translate_news_item(news_item):
    # 仅翻译 title 和 summary 字段
    translated_item = {}
    for key, value in news_item.items():
        if key in ["title", "summary"] and isinstance(value, str) and value.strip():
            try:
                translated_item[key] = translate_text(value)
            except Exception as e:
                print(f"翻译字段 {key} 时出错: {e}")
                translated_item[key] = value  # 保留原文
        else:
            # 如果是published字段且值为GMT时间格式，则转换为北京时间
            if (
                value != "未知时间"
                and key == "published"
                and isinstance(value, str)
                and value.strip()
            ):
                try:
                    # 解析GMT时间并转换为北京时间
                    parsed_time = email.utils.parsedate_to_datetime(value)
                    # 转换为北京时间 (UTC+8)
                    beijing_time = parsed_time + datetime.timedelta(hours=8)
                    translated_item[key] = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print(f"时间转换出错: {e}，保留原始值")
                    translated_item[key] = value  # 如果转换失败，保留原始值
            else:
                translated_item[key] = value
    return translated_item


# 批量翻译函数以提高效率
def translate_news_batch(news_items, batch_size=8):
    translated_data = []
    for i in range(0, len(news_items), batch_size):
        batch = news_items[i : i + batch_size]
        print(f"正在翻译批次 {i//batch_size+1}/{(len(news_items)-1)//batch_size+1}")
        batch_results = []
        for item in batch:
            try:
                translated_item = translate_news_item(item)
                batch_results.append(translated_item)
            except Exception as e:
                print(f"翻译批次中的新闻时出错: {e}")
                batch_results.append(item)  # 保留原文
        translated_data.extend(batch_results)
        # 每个批次后清理缓存
        torch.cuda.empty_cache()
    return translated_data


def bj_time(value):
    try:
        # 解析GMT时间并转换为北京时间
        parsed_time = email.utils.parsedate_to_datetime(value)
        # 转换为北京时间 (UTC+8)
        beijing_time = parsed_time + datetime.timedelta(hours=8)
        return beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"时间转换出错: {e}，保留原始值")
        return value  # 如果转换失败，保留原始值


def main():
    # 获取当前目录下所有JSON文件
    current_directory = "./news"
    json_files = [
        f
        for f in os.listdir(current_directory)
        if f.endswith(".json") and f != "translated_" + f
    ]
    # 处理每个JSON文件
    for input_file in json_files:
        print(f"正在处理文件: {current_directory}/{input_file}")
        # 读取JSON文件
        with open(f"{current_directory}/{input_file}", "r", encoding="utf-8") as f:
            data = json.load(f)
        # 批量翻译新闻内容
        translated_data = {
            "title": data["title"],
            "description": data["description"],
            # 转为北京时间
            "updatetime": bj_time(data["updatetime"]),
            "news": [],
        }
        # 使用批量翻译替代逐条翻译
        print(f"开始批量翻译 {input_file} 中的新闻...")
        try:
            translated_data["news"] = translate_news_batch(data["news"])
        except Exception as e:
            print(f"批量翻译 {input_file} 时出错 {e}")
        # 保存到新文件
        file_path = "./translated_news"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        output_file = f"./translated_news/translated_{input_file}"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        print(f"文件 {input_file} 翻译完成，结果已保存到 {output_file}")


if __name__ == "__main__":
    main()
