"""A script to quantize supported models and updload to model zoo.

Example usage:
python quantize_and_upload.py --method <method> --token <dropbox token>

Note: This script is for developers.
"""
import argparse
import hashlib
import os

from upload import subebackups

model_paths = ["models/LLaMA_13B_2_chat"]

quantized_dir = "INT4"
db_prefix = "/MIT/transformer_assets/"


def _get_md5sum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def main():
    """Take arguments and quantize all models and upload to dropbox."""

    def _get_parser():
        parser = argparse.ArgumentParser(description="Quantize model")
        parser.add_argument("--model_path", type=str, help="Quantization method", default=None)
        parser.add_argument("--method", type=str, help="Quantization method")
        parser.add_argument("--token", help="Your Dropbox OAuth2 token.")
        return parser

    parser = _get_parser()
    args = parser.parse_args()

    if args.method not in ["QM_x86", "QM_ARM", "QM_CUDA", "FP32", "INT8"]:
        raise ValueError("expect method to be one of ['QM_x86', 'QM_ARM', 'QM_CUDA', 'FP32', 'INT8']")
    QM_method = args.method

    if args.model_path:
        target_paths = [args.model_path]
    else:
        target_paths = model_paths

    for model_path in target_paths:
        # quantize
        if args.method in ["QM_x86", "QM_CUDA", "QM_ARM"]:
            out_dir = quantized_dir
            quantize_cmd = (
                f"python model_quantizer.py --model_path {model_path} --method {QM_method} --output_path {out_dir}"
            )
            os.system(quantize_cmd)
        else:
            out_dir = "./"
        # zip
        print("zipping...")
        model_name_size = model_path.rsplit("/", maxsplit=1)[-1]
        zip_path = "/tmp/" + model_name_size + ".zip"
        zip_cmd = f"zip -qq -r {zip_path} {os.path.join(out_dir, model_path)}"
        os.system(zip_cmd)
        # md5sum
        print(f"md5sum is {_get_md5sum(zip_path)}.")
        print("uploading...")
        # upload
        upload_path = os.path.join(db_prefix, QM_method, model_name_size + ".zip")
        subebackups(zip_path, upload_path, args.token)
        print("removing temporary zip file...")
        # rm zip
        os.system(f"rm {zip_path}")


if __name__ == "__main__":
    main()
