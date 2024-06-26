"""Script to export INT8 OPT models from smootquant to the TinyLLMEngine format.

Prerequisites: smoothquant (reference: https://github.com/mit-han-lab/smoothquant)

Usage:
python opt_smooth_exporter.py --model-name <model_name> --output-path <output_path>

Example command:
INT8:
python opt_smooth_exporter.py --model-name mit-han-lab/opt-1.3B-smoothquant --output-path models/OPT_1.3B
Supported model_name:
- opt-125m-smoothquant
- opt-1.3B-smoothquant
- opt-6.7B-smoothquant

FP32:
python opt_smooth_exporter.py --model_name facebook/opt-125m --output_path FP32/models/OPT_125m --no-int8_smooth

"""
import argparse
import os
import struct

import torch

os.environ["CUDA_VISIBLE_DEVICES"] = "0"


@torch.no_grad()
def _export_Qmodel(model, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "lm_head.bin"), "wb") as f:
        f.write(model.lm_head._parameters["weight"].cpu().float().numpy().tobytes())
    _export_Qdecoder(model.model.decoder, os.path.join(f"{outpath}", "decoder"))


@torch.no_grad()
def _export_model(model, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "lm_head.bin"), "wb") as f:
        f.write(model.lm_head._parameters["weight"].cpu().float().numpy().tobytes())
    _export_decoder(model.model.decoder, os.path.join(f"{outpath}", "decoder"))


def _export_Qdecoder(decoder, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    _export_embed_tokens(decoder.embed_tokens, os.path.join(f"{outpath}", "embed_tokens"))
    _export_LayerNorm(decoder.final_layer_norm, os.path.join(f"{outpath}", "final_layer_norm"))
    _export_embed_tokens(decoder.embed_positions, os.path.join(f"{outpath}", "embed_positions"))
    idx = 0
    for layer in decoder.layers:
        _export_Qdecoder_layer(layer, os.path.join(f"{outpath}", f"layer{idx}"))
        idx += 1


def _export_decoder(decoder, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    _export_embed_tokens(decoder.embed_tokens, os.path.join(f"{outpath}", "embed_tokens"))
    _export_LayerNorm(decoder.final_layer_norm, os.path.join(f"{outpath}", "final_layer_norm"))
    _export_embed_tokens(decoder.embed_positions, os.path.join(f"{outpath}", "embed_positions"))
    idx = 0
    for layer in decoder.layers:
        _export_decoder_layer(layer, os.path.join(f"{outpath}", f"layer{idx}"))
        idx += 1


def _export_Qdecoder_layer(layer, prefix: str):
    outpath = prefix
    _export_Qattention_params(layer.self_attn, os.path.join(outpath, "self_attn"))
    _export_LayerNormQ(layer.self_attn_layer_norm, os.path.join(outpath, "self_attn_layer_norm"))
    _export_W8A8B8O8Linear(layer.fc1, os.path.join(outpath, "fc1"))
    _export_W8A8BFP32OFP32Linear(layer.fc2, os.path.join(outpath, "fc2"))
    _export_LayerNormQ(layer.final_layer_norm, os.path.join(outpath, "final_layer_norm"))


def _export_decoder_layer(layer, prefix: str):
    outpath = prefix
    _export_attention_params(layer.self_attn, os.path.join(outpath, "self_attn"))
    _export_LayerNorm(layer.self_attn_layer_norm, os.path.join(outpath, "self_attn_layer_norm"))
    _export_LinearFP(layer.fc1, os.path.join(outpath, "fc1"))
    _export_LinearFP(layer.fc2, os.path.join(outpath, "fc2"))
    _export_LayerNorm(layer.final_layer_norm, os.path.join(outpath, "final_layer_norm"))


def _export_Qattention_params(attn, prefix: str):
    outpath = prefix
    _export_BMM_S8T_S8N_F32T(attn.qk_bmm, os.path.join(outpath, "qk_bmm"))
    _export_BMM_S8T_S8N_S8T(attn.pv_bmm, os.path.join(outpath, "pv_bmm"))
    _export_W8A8B8O8Linear(attn.k_proj, os.path.join(outpath, "k_proj"))
    _export_W8A8B8O8Linear(attn.v_proj, os.path.join(outpath, "v_proj"))
    _export_W8A8B8O8Linear(attn.q_proj, os.path.join(outpath, "q_proj"))
    _export_W8A8BFP32OFP32Linear(attn.out_proj, os.path.join(outpath, "out_proj"))


def _export_attention_params(attn, prefix: str):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(outpath, "scaling.bin"), "wb") as f:
        f.write(bytearray(struct.pack("f", attn.scaling)))
    _export_LinearFP(attn.k_proj, os.path.join(outpath, "k_proj"))
    _export_LinearFP(attn.v_proj, os.path.join(outpath, "v_proj"))
    _export_LinearFP(attn.q_proj, os.path.join(outpath, "q_proj"))
    _export_LinearFP(attn.out_proj, os.path.join(outpath, "out_proj"))


def _export_embed_tokens(embed_tokens, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "weight.bin"), "wb") as f:
        f.write(embed_tokens.weight.cpu().float().numpy().tobytes())


def _export_BMM_S8T_S8N_F32T(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "alpha.bin"), "wb") as f:
        f.write(op.a.cpu().float().numpy().tobytes())


def _export_BMM_S8T_S8N_S8T(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "alpha.bin"), "wb") as f:
        f.write(op.a.cpu().float().numpy().tobytes())


def _export_W8A8B8O8Linear(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "weight.bin"), "wb") as f:
        f.write(op.weight.cpu().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "bias.bin"), "wb") as f:
        f.write((op.bias.cpu().float() * (op.b.item() / op.a.item())).round().int().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "bias_int8.bin"), "wb") as f:
        f.write((op.bias.cpu().numpy().tobytes()))
    with open(os.path.join(f"{outpath}", "alpha.bin"), "wb") as f:
        f.write(op.a.cpu().float().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "beta.bin"), "wb") as f:
        f.write(op.b.cpu().float().numpy().tobytes())


def _export_W8A8BFP32OFP32Linear(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "weight.bin"), "wb") as f:
        f.write(op.weight.cpu().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "bias.bin"), "wb") as f:
        f.write(op.bias.cpu().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "alpha.bin"), "wb") as f:
        f.write(op.a.cpu().float().numpy().tobytes())


def _export_LayerNorm(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "weight.bin"), "wb") as f:
        f.write(op.weight.cpu().float().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "bias.bin"), "wb") as f:
        f.write(op.bias.cpu().float().numpy().tobytes())


def _export_LayerNormQ(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "weight.bin"), "wb") as f:
        f.write(op.weight.cpu().float().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "bias.bin"), "wb") as f:
        f.write(op.bias.cpu().float().numpy().tobytes())


def _export_LinearFP(op, prefix):
    outpath = prefix
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(f"{outpath}", "weight.bin"), "wb") as f:
        f.write(op._parameters["weight"].cpu().float().numpy().tobytes())
    with open(os.path.join(f"{outpath}", "bias.bin"), "wb") as f:
        f.write(op._parameters["bias"].cpu().float().numpy().tobytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="mit-han-lab/opt-1.3B-smoothquant")
    parser.add_argument("--output_path", type=str)
    parser.add_argument("--no-int8_smooth", dest="int8_smooth", action="store_false")
    parser.set_defaults(int8_smooth=True)
    args = parser.parse_args()

    if args.int8_smooth:
        from smoothquant.opt import Int8OPTForCausalLM

        model_smoothquant = Int8OPTForCausalLM.from_pretrained(
            args.model_name, torch_dtype=torch.float32, device_map="auto"
        )

        _export_Qmodel(model_smoothquant, args.output_path)
    else:
        from transformers import OPTForCausalLM

        model = OPTForCausalLM.from_pretrained(args.model_name, torch_dtype=torch.float32)

        _export_model(model, args.output_path)
