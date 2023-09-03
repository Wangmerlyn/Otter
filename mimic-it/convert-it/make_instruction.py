"""
Module used to make an FunQA_instruction.json
"""
import argparse
import datetime
from typing import Dict
import json
import os
import bisect
import subprocess


def runCmd(command):
    """
    Run command in shell
    """
    ret = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=1,
    )
    return ret


def get_git_version(path: str = "."):
    """
    Change
    """
    cmd = 'cd {}; git log --pretty=format:"%h" -n 1'
    content = str(runCmd(cmd.format(path)).stdout, "utf-8")
    cmd = "cd -"
    runCmd(cmd)
    # print(content)
    return content


def make_instruction(
    image_json_path: str, annotation_path: str, output_path: str
):
    """
    Make an FunQA_instruction.json from image json file and annotations
    """
    assert os.path.exists(image_json_path), "image json file doesn't exist"
    assert os.path.exists(annotation_path), "annotation json file doesn't exist"
    with open(image_json_path, "r", encoding="utf-8") as image_json_file:
        fun_qa = json.loads(image_json_file.read())
    keys_list = list(fun_qa.keys())
    keys_list.sort()
    with open(annotation_path, "r", encoding="utf-8") as f_anno:
        annotation = json.loads(f_anno.read())
    # add a instruction ID as key for each instruction pair
    instructions = {}
    for pair in annotation:
        instruction_id = pair["ID"]
        instructions[f"FunQA_{instruction_id}"] = pair
    for key, pair in instructions.items():
        pair["answer"] = pair.pop("output")

    # search image keys for corresponding images
    prefix_list = ["_".join(i.split("_")[2:-1]) for i in keys_list]

    for key, pair in instructions.items():
        video_name = pair["visual_input"].split(".")[0]
        start_index = bisect.bisect_left(prefix_list, video_name)
        end_index = bisect.bisect_right(prefix_list, video_name)
        pair["image_ids"] = keys_list[start_index:end_index]

    # collecting rel_ins_ids
    # search for instructions with same video name
    rel_ins_ids_dict = {}

    for key, pair in instructions.items():
        video = pair["visual_input"]
        if video not in rel_ins_ids_dict:
            rel_ins_ids_dict[video] = []
        rel_ins_ids_dict[video].append(key)

    # add a rel_ins_ids attribute for each pair
    for key, pair in instructions.items():
        video = pair["visual_input"]
        list_copy = rel_ins_ids_dict[video][:]
        list_copy.remove(key)
        pair["rel_ins_ids"] = list_copy

    # remove unnecessary attributes
    for key, pair in instructions.items():
        pair.pop("visual_input")
        pair.pop("ID")
        pair.pop("task")

    # create a meta data dictionary
    meta_data = {}
    meta_data["version"] = get_git_version()
    meta_data["author"] = "NobleAI"
    meta_data["time"] = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_json = {}
    output_json["meta"] = meta_data
    output_json["data"] = instructions

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(output_json, output_file)
    return output_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image_json_path",
        default="./output/FunQA.json",
        help="Path to the image json file.",
    )
    parser.add_argument(
        "--annotation_path",
        default="../../dataset/annotation_with_ID/funqa_train.json",
        help="path to the annotation file.",
    )
    parser.add_argument(
        "--output_path",
        default="./output/FunQA_instructions.json",
        help="path to save the FunQA_instructions json file",
    )

    args = parser.parse_args()
    make_instruction_args: Dict[str, str] = {}
    make_instruction_args["image_json_path"] = args.image_json_path
    make_instruction_args["annotation_path"] = args.annotation_path
    make_instruction_args["output_path"] = args.output_path

    make_instruction(**make_instruction_args)
